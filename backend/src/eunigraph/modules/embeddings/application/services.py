from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from eunigraph.core.config import Settings
from eunigraph.modules.catalog.infrastructure.models import (
    PublicationAuthorModel,
    PublicationModel,
)
from eunigraph.modules.embeddings.domain import (
    EmbeddingProvider,
    EmbeddingProviderError,
)
from eunigraph.modules.embeddings.infrastructure import (
    GeminiEmbeddingProvider,
    PublicationEmbeddingModel,
    QdrantPublicationEmbeddingStore,
)
from eunigraph.persistence.qdrant.client import get_qdrant_client

SUPPORTED_PUBLICATION_CONTENT_FIELDS = {"title", "authors", "abstract"}


@dataclass(slots=True)
class PublicationEmbeddingBuildOutcome:
    publication_id: UUID
    status: str
    reason: str | None
    embedding_id: UUID | None
    qdrant_point_id: str | None


@dataclass(slots=True)
class EmbeddingsBuildSummary:
    provider: str
    model: str
    embedding_version: str
    collection_name: str
    processed_count: int
    generated_count: int
    skipped_count: int
    failed_count: int
    results: list[PublicationEmbeddingBuildOutcome]


@dataclass(slots=True)
class EmbeddingsProviderSummary:
    enabled: bool
    provider: str
    model: str
    embedding_version: str
    batch_size: int
    request_timeout_seconds: int
    max_retries: int
    content_fields: tuple[str, ...]
    qdrant_collection: str
    qdrant_api_key_configured: bool
    gemini_api_key_configured: bool


@dataclass(slots=True)
class EmbeddingsStatusSummary:
    enabled: bool
    provider: str
    model: str
    embedding_version: str
    qdrant_collection: str
    qdrant_collection_exists: bool
    qdrant_points_count: int
    qdrant_collection_status: str | None
    total_publications: int
    active_embeddings_count: int
    latest_embedding_updated_at: datetime | None


@dataclass(slots=True)
class EmbeddingsResetSummary:
    collection_name: str
    collection_deleted: bool
    deleted_metadata_count: int
    provider: str
    model: str
    embedding_version: str


class PublicationEmbeddingService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        *,
        provider: EmbeddingProvider | None = None,
        vector_store: QdrantPublicationEmbeddingStore | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self._provider = provider
        self._vector_store = vector_store

    def get_provider_info(self) -> EmbeddingsProviderSummary:
        return EmbeddingsProviderSummary(
            enabled=self._embeddings_available(),
            provider=self.settings.embeddings_provider,
            model=self.settings.embeddings_model,
            embedding_version=self.settings.embeddings_version,
            batch_size=self.settings.embeddings_batch_size,
            request_timeout_seconds=self.settings.embeddings_request_timeout_seconds,
            max_retries=self.settings.embeddings_max_retries,
            content_fields=self.settings.embeddings_content_fields,
            qdrant_collection=self.settings.qdrant_collection_publications,
            qdrant_api_key_configured=self.settings.qdrant_api_key is not None,
            gemini_api_key_configured=self.settings.gemini_api_key is not None,
        )

    def get_status(self) -> EmbeddingsStatusSummary:
        if self._embeddings_available():
            collection_status = self._vector_store_instance().get_collection_status(
                self.settings.qdrant_collection_publications,
            )
        else:
            collection_status = {
                "exists": False,
                "points_count": 0,
                "status": None,
            }
        active_embeddings_count, latest_embedding_updated_at = self.session.execute(
            select(
                func.count(PublicationEmbeddingModel.id),
                func.max(PublicationEmbeddingModel.updated_at),
            ).where(
                PublicationEmbeddingModel.embedding_provider == self.settings.embeddings_provider,
                PublicationEmbeddingModel.embedding_model == self.settings.embeddings_model,
                PublicationEmbeddingModel.embedding_version == self.settings.embeddings_version,
                PublicationEmbeddingModel.qdrant_collection
                == self.settings.qdrant_collection_publications,
            ),
        ).one()
        total_publications = self.session.scalar(
            select(func.count(PublicationModel.id)),
        ) or 0
        return EmbeddingsStatusSummary(
            enabled=self._embeddings_available(),
            provider=self.settings.embeddings_provider,
            model=self.settings.embeddings_model,
            embedding_version=self.settings.embeddings_version,
            qdrant_collection=self.settings.qdrant_collection_publications,
            qdrant_collection_exists=bool(collection_status["exists"]),
            qdrant_points_count=int(collection_status["points_count"]),
            qdrant_collection_status=collection_status["status"],
            total_publications=int(total_publications),
            active_embeddings_count=int(active_embeddings_count or 0),
            latest_embedding_updated_at=latest_embedding_updated_at,
        )

    def build_embeddings(
        self,
        *,
        publication_ids: list[UUID] | None = None,
        limit: int | None = None,
        force: bool = False,
    ) -> EmbeddingsBuildSummary:
        self._ensure_embeddings_enabled()
        publications = self._select_publications(
            publication_ids=publication_ids,
            limit=limit,
        )
        results: list[PublicationEmbeddingBuildOutcome] = []
        generated_count = 0
        skipped_count = 0
        failed_count = 0

        for batch_start in range(0, len(publications), self.settings.embeddings_batch_size):
            publication_batch = publications[
                batch_start : batch_start + self.settings.embeddings_batch_size
            ]
            generated_publications: list[PublicationModel] = []
            texts: list[str] = []
            batch_results: dict[UUID, PublicationEmbeddingBuildOutcome] = {}

            for publication in publication_batch:
                content_text = self._build_publication_content(publication)
                content_hash = self._compute_content_hash(content_text)
                existing_embedding = self._matching_embedding(publication)
                if (
                    not force
                    and existing_embedding is not None
                    and existing_embedding.content_hash == content_hash
                    and existing_embedding.qdrant_collection
                    == self.settings.qdrant_collection_publications
                ):
                    batch_results[publication.id] = PublicationEmbeddingBuildOutcome(
                        publication_id=publication.id,
                        status="skipped",
                        reason="content_unchanged",
                        embedding_id=existing_embedding.id,
                        qdrant_point_id=existing_embedding.qdrant_point_id,
                    )
                    skipped_count += 1
                    continue
                generated_publications.append(publication)
                texts.append(content_text)

            if texts:
                try:
                    vectors = self._provider_instance().embed_texts(texts)
                except EmbeddingProviderError as exc:
                    failed_count += len(generated_publications)
                    for publication in generated_publications:
                        batch_results[publication.id] = PublicationEmbeddingBuildOutcome(
                            publication_id=publication.id,
                            status="failed",
                            reason=str(exc),
                            embedding_id=None,
                            qdrant_point_id=None,
                        )
                else:
                    for publication, vector in zip(generated_publications, vectors, strict=True):
                        try:
                            embedding_model = self._upsert_publication_embedding(
                                publication=publication,
                                vector=vector,
                            )
                            self.session.commit()
                        except (EmbeddingProviderError, HTTPException) as exc:
                            failed_count += 1
                            self.session.rollback()
                            batch_results[publication.id] = PublicationEmbeddingBuildOutcome(
                                publication_id=publication.id,
                                status="failed",
                                reason=str(exc),
                                embedding_id=None,
                                qdrant_point_id=None,
                            )
                            continue
                        except IntegrityError as exc:
                            self.session.rollback()
                            failed_count += 1
                            batch_results[publication.id] = PublicationEmbeddingBuildOutcome(
                                publication_id=publication.id,
                                status="failed",
                                reason=(
                                    "Invalid publication embedding metadata or conflicting "
                                    "embedding rows"
                                ),
                                embedding_id=None,
                                qdrant_point_id=None,
                            )
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=(
                                    "Invalid publication embedding metadata or conflicting "
                                    "embedding rows"
                                ),
                            ) from exc
                        else:
                            generated_count += 1
                            batch_results[publication.id] = PublicationEmbeddingBuildOutcome(
                                publication_id=publication.id,
                                status="generated",
                                reason=None,
                                embedding_id=embedding_model.id,
                                qdrant_point_id=embedding_model.qdrant_point_id,
                            )

            ordered_batch_results = [
                batch_results[publication.id]
                for publication in publication_batch
                if publication.id in batch_results
            ]
            results.extend(ordered_batch_results)

        return EmbeddingsBuildSummary(
            provider=self.settings.embeddings_provider,
            model=self.settings.embeddings_model,
            embedding_version=self.settings.embeddings_version,
            collection_name=self.settings.qdrant_collection_publications,
            processed_count=len(publications),
            generated_count=generated_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results,
        )

    def build_publication_embedding(
        self,
        publication_id: UUID,
        *,
        force: bool = False,
    ) -> PublicationEmbeddingBuildOutcome:
        summary = self.build_embeddings(
            publication_ids=[publication_id],
            force=force,
        )
        if not summary.results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publication not found",
            )
        return summary.results[0]

    def load_all_embeddings(
        self,
        *,
        force: bool = False,
    ) -> EmbeddingsBuildSummary:
        return self.build_embeddings(
            publication_ids=None,
            limit=None,
            force=force,
        )

    def get_publication_embedding(
        self,
        publication_id: UUID,
    ) -> PublicationEmbeddingModel:
        publication = self._publication_or_404(publication_id)
        embedding = self._matching_embedding(publication)
        if embedding is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No embedding found for the requested publication and active configuration",
            )
        return embedding

    def reset_embeddings(self) -> EmbeddingsResetSummary:
        self._ensure_embeddings_enabled()
        collection_deleted = self._vector_store_instance().delete_collection(
            self.settings.qdrant_collection_publications,
        )
        embeddings = list(
            self.session.scalars(
                select(PublicationEmbeddingModel).where(
                    PublicationEmbeddingModel.embedding_provider
                    == self.settings.embeddings_provider,
                    PublicationEmbeddingModel.embedding_model == self.settings.embeddings_model,
                    PublicationEmbeddingModel.embedding_version == self.settings.embeddings_version,
                    PublicationEmbeddingModel.qdrant_collection
                    == self.settings.qdrant_collection_publications,
                ),
            ),
        )
        for embedding in embeddings:
            self.session.delete(embedding)
        self.session.commit()
        return EmbeddingsResetSummary(
            collection_name=self.settings.qdrant_collection_publications,
            collection_deleted=collection_deleted,
            deleted_metadata_count=len(embeddings),
            provider=self.settings.embeddings_provider,
            model=self.settings.embeddings_model,
            embedding_version=self.settings.embeddings_version,
        )

    def _ensure_embeddings_enabled(self) -> None:
        unavailable_detail = self._embeddings_unavailable_detail()
        if unavailable_detail is not None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=unavailable_detail,
            )

    def _embeddings_available(self) -> bool:
        return self._embeddings_unavailable_detail() is None

    def _embeddings_unavailable_detail(self) -> str | None:
        if not self.settings.embeddings_enabled:
            return "Embeddings are disabled in the current environment"
        provider_name = self.settings.embeddings_provider.lower()
        if provider_name == "gemini" and self.settings.gemini_api_key is None:
            return "Embeddings are disabled because GEMINI_API_KEY is not configured"
        return None

    def _provider_instance(self) -> EmbeddingProvider:
        if self._provider is not None:
            return self._provider
        provider_name = self.settings.embeddings_provider.lower()
        if provider_name != "gemini":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unsupported embeddings provider `{self.settings.embeddings_provider}`",
            )
        if self.settings.gemini_api_key is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embeddings are disabled because GEMINI_API_KEY is not configured",
            )
        self._provider = GeminiEmbeddingProvider(
            api_key=self.settings.gemini_api_key,
            model_name=self.settings.embeddings_model,
            timeout_seconds=self.settings.embeddings_request_timeout_seconds,
            max_retries=self.settings.embeddings_max_retries,
        )
        return self._provider

    def _vector_store_instance(self) -> QdrantPublicationEmbeddingStore:
        if self._vector_store is not None:
            return self._vector_store
        self._vector_store = QdrantPublicationEmbeddingStore(get_qdrant_client())
        return self._vector_store

    def _select_publications(
        self,
        *,
        publication_ids: list[UUID] | None,
        limit: int | None,
    ) -> list[PublicationModel]:
        query: Select[tuple[PublicationModel]] = (
            select(PublicationModel)
            .options(
                selectinload(PublicationModel.embeddings),
                selectinload(PublicationModel.authors).selectinload(
                    PublicationAuthorModel.researcher,
                ),
            )
            .order_by(PublicationModel.created_at.desc())
        )
        if publication_ids:
            query = query.where(PublicationModel.id.in_(publication_ids))
        if limit is not None:
            query = query.limit(limit)
        return list(self.session.scalars(query).unique())

    def _publication_or_404(self, publication_id: UUID) -> PublicationModel:
        publication = self.session.scalar(
            select(PublicationModel)
            .options(
                selectinload(PublicationModel.embeddings),
                selectinload(PublicationModel.authors).selectinload(
                    PublicationAuthorModel.researcher,
                ),
            )
            .where(PublicationModel.id == publication_id),
        )
        if publication is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publication not found",
            )
        return publication

    def _build_publication_content(self, publication: PublicationModel) -> str:
        blocks: list[str] = []
        author_names = self._publication_author_names(publication)
        for field_name in self.settings.embeddings_content_fields:
            if field_name == "authors":
                if author_names:
                    blocks.append(f"Authors: {', '.join(author_names)}")
                continue
            if field_name not in SUPPORTED_PUBLICATION_CONTENT_FIELDS:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unsupported embedding content field `{field_name}`",
                )
            field_value = getattr(publication, field_name)
            if field_value is None:
                continue
            cleaned_value = str(field_value).strip()
            if not cleaned_value:
                continue
            blocks.append(f"{field_name.title()}: {cleaned_value}")
        if not blocks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "The selected publication does not contain embeddable content "
                    "for the configured fields"
                ),
            )
        return "\n\n".join(blocks)

    def _publication_author_names(self, publication: PublicationModel) -> list[str]:
        ordered_authors = sorted(
            publication.authors,
            key=lambda author: author.author_position,
        )
        author_names: list[str] = []
        for author in ordered_authors:
            if author.researcher is not None and author.researcher.full_name.strip():
                author_names.append(author.researcher.full_name.strip())
                continue
            if author.author_list_name is not None and author.author_list_name.strip():
                author_names.append(author.author_list_name.strip())
        return author_names

    def _build_publication_payload(
        self,
        publication: PublicationModel,
        content_text: str,
    ) -> dict[str, object]:
        author_names = self._publication_author_names(publication)
        payload: dict[str, object] = {
            "publication_id": str(publication.id),
            "title": publication.title,
            "content_text": content_text,
            "authors": author_names,
        }
        if publication.abstract:
            payload["abstract"] = publication.abstract
        if publication.publication_year is not None:
            payload["publication_year"] = publication.publication_year
        if publication.doi:
            payload["doi"] = publication.doi
        if publication.openaire_id:
            payload["openaire_id"] = publication.openaire_id
        if publication.journal_name:
            payload["journal_name"] = publication.journal_name
        if publication.venue_name:
            payload["venue_name"] = publication.venue_name
        if publication.publisher:
            payload["publisher"] = publication.publisher
        return payload

    def _compute_content_hash(self, content_text: str) -> str:
        return hashlib.sha256(content_text.encode("utf-8")).hexdigest()

    def _matching_embedding(
        self,
        publication: PublicationModel,
    ) -> PublicationEmbeddingModel | None:
        for embedding in publication.embeddings:
            if (
                embedding.embedding_provider == self.settings.embeddings_provider
                and embedding.embedding_model == self.settings.embeddings_model
                and embedding.embedding_version == self.settings.embeddings_version
            ):
                return embedding
        return None

    def _qdrant_point_id(self, publication_id: UUID) -> str:
        raw_value = (
            f"publication:{publication_id}:{self.settings.embeddings_provider}:"
            f"{self.settings.embeddings_model}:{self.settings.embeddings_version}"
        )
        return str(uuid5(NAMESPACE_URL, raw_value))

    def _upsert_publication_embedding(
        self,
        *,
        publication: PublicationModel,
        vector: list[float],
    ) -> PublicationEmbeddingModel:
        content_text = self._build_publication_content(publication)
        content_hash = self._compute_content_hash(content_text)
        point_id = self._qdrant_point_id(publication.id)
        self._vector_store_instance().upsert_publication_embedding(
            collection_name=self.settings.qdrant_collection_publications,
            point_id=point_id,
            vector=vector,
            payload=self._build_publication_payload(publication, content_text),
        )
        embedding = self._matching_embedding(publication)
        if embedding is None:
            embedding = PublicationEmbeddingModel(
                publication_id=publication.id,
                embedding_provider=self.settings.embeddings_provider,
                qdrant_collection=self.settings.qdrant_collection_publications,
                qdrant_point_id=point_id,
                embedding_model=self.settings.embeddings_model,
                embedding_version=self.settings.embeddings_version,
                content_hash=content_hash,
            )
            self.session.add(embedding)
            publication.embeddings.append(embedding)
        else:
            embedding.embedding_provider = self.settings.embeddings_provider
            embedding.qdrant_collection = self.settings.qdrant_collection_publications
            embedding.qdrant_point_id = point_id
            embedding.embedding_model = self.settings.embeddings_model
            embedding.embedding_version = self.settings.embeddings_version
            embedding.content_hash = content_hash
        self.session.flush()
        return embedding
