from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    PublicationAuthorModel,
    PublicationModel,
    ResearcherModel,
)
from eunigraph.modules.embeddings.application import PublicationEmbeddingService
from eunigraph.modules.embeddings.domain import EmbeddingProvider
from eunigraph.modules.embeddings.infrastructure.models import PublicationEmbeddingModel
from eunigraph.modules.embeddings.infrastructure.providers import GeminiEmbeddingProvider
from eunigraph.persistence.postgres import models  # noqa: F401


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.deleted: list[object] = []
        self.flush_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0

    def add(self, value: object) -> None:
        self.added.append(value)

    def delete(self, value: object) -> None:
        self.deleted.append(value)

    def flush(self) -> None:
        self.flush_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def scalars(self, _query: object) -> list[object]:
        return []


class ResetFakeSession(FakeSession):
    def __init__(self, values: Sequence[object]) -> None:
        super().__init__()
        self._values = list(values)

    def scalars(self, _query: object) -> list[object]:
        return list(self._values)


class FakeProvider(EmbeddingProvider):
    def __init__(self, vectors: Sequence[list[float]]) -> None:
        self.vectors = list(vectors)
        self.received_texts: list[list[str]] = []

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return "gemini-embedding-001"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.received_texts.append(texts)
        return self.vectors[: len(texts)]


class FakeVectorStore:
    def __init__(self) -> None:
        self.upserts: list[dict[str, Any]] = []
        self.deleted_collections: list[str] = []

    def upsert_publication_embedding(
        self,
        *,
        collection_name: str,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        self.upserts.append(
            {
                "collection_name": collection_name,
                "point_id": point_id,
                "vector": vector,
                "payload": payload,
            },
        )

    def get_collection_status(self, collection_name: str) -> dict[str, Any]:
        return {
            "exists": True,
            "points_count": len(self.upserts),
            "status": "green",
        }

    def delete_collection(self, collection_name: str) -> bool:
        self.deleted_collections.append(collection_name)
        return True


class FakePublicationEmbeddingService(PublicationEmbeddingService):
    def __init__(
        self,
        session: Session,
        settings: Any,
        publications: Sequence[PublicationModel],
        *,
        provider: EmbeddingProvider,
        vector_store: FakeVectorStore,
    ) -> None:
        super().__init__(
            session,
            settings,
            provider=provider,
            vector_store=cast(Any, vector_store),
        )
        self.publications = list(publications)

    def _select_publications(
        self,
        *,
        publication_ids: list[Any] | None,
        limit: int | None,
    ) -> list[PublicationModel]:
        selected = self.publications
        if publication_ids:
            selected = [
                publication
                for publication in selected
                if publication.id in publication_ids
            ]
        if limit is not None:
            return selected[:limit]
        return selected

    def _publication_or_404(self, publication_id: Any) -> PublicationModel:
        for publication in self.publications:
            if publication.id == publication_id:
                return publication
        raise AssertionError("Publication not found in test service")


def _settings(content_fields: tuple[str, ...] = ("title", "authors", "abstract")) -> Any:
    return SimpleNamespace(
        embeddings_enabled=True,
        embeddings_provider="gemini",
        embeddings_model="gemini-embedding-001",
        embeddings_version="v1",
        embeddings_batch_size=16,
        embeddings_request_timeout_seconds=60,
        embeddings_max_retries=3,
        embeddings_content_fields=content_fields,
        qdrant_collection_publications="publication_embeddings",
        qdrant_api_key=None,
        gemini_api_key="test-key",
    )


def test_build_publication_content_uses_configured_fields_and_labels() -> None:
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Ada Lovelace",
        normalized_name="ada lovelace",
    )
    publication = PublicationModel(
        id=uuid4(),
        title="A semantic map",
        normalized_title="a semantic map",
        abstract="Research metadata and graph analysis.",
    )
    publication.authors = [
        PublicationAuthorModel(
            publication_id=publication.id,
            researcher_id=researcher.id,
            author_position=1,
            researcher=researcher,
        ),
    ]
    service = FakePublicationEmbeddingService(
        cast(Session, FakeSession()),
        _settings(),
        [publication],
        provider=FakeProvider([[0.1, 0.2]]),
        vector_store=FakeVectorStore(),
    )

    content = service._build_publication_content(publication)

    assert content == (
        "Title: A semantic map\n\n"
        "Authors: Ada Lovelace\n\n"
        "Abstract: Research metadata and graph analysis."
    )


def test_build_embeddings_skips_when_content_hash_and_config_match() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="A semantic map",
        normalized_title="a semantic map",
        abstract="Research metadata and graph analysis.",
    )
    session = FakeSession()
    vector_store = FakeVectorStore()
    provider = FakeProvider([[0.1, 0.2]])
    service = FakePublicationEmbeddingService(
        cast(Session, session),
        _settings(),
        [publication],
        provider=provider,
        vector_store=vector_store,
    )
    existing_content = service._build_publication_content(publication)
    publication.embeddings = [
        PublicationEmbeddingModel(
            id=uuid4(),
            publication_id=publication.id,
            embedding_provider="gemini",
            qdrant_collection="publication_embeddings",
            qdrant_point_id="point-1",
            embedding_model="gemini-embedding-001",
            embedding_version="v1",
            content_hash=service._compute_content_hash(existing_content),
        ),
    ]

    summary = service.build_embeddings()

    assert summary.generated_count == 0
    assert summary.skipped_count == 1
    assert provider.received_texts == []
    assert vector_store.upserts == []
    assert session.commit_calls == 0


def test_build_embeddings_generates_and_persists_publication_embedding() -> None:
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Ada Lovelace",
        normalized_name="ada lovelace",
    )
    publication = PublicationModel(
        id=uuid4(),
        title="A semantic map",
        normalized_title="a semantic map",
        abstract="Research metadata and graph analysis.",
        doi="10.1000/example",
    )
    publication.authors = [
        PublicationAuthorModel(
            publication_id=publication.id,
            researcher_id=researcher.id,
            author_position=1,
            researcher=researcher,
        ),
    ]
    session = FakeSession()
    vector_store = FakeVectorStore()
    provider = FakeProvider([[0.1, 0.2, 0.3]])
    service = FakePublicationEmbeddingService(
        cast(Session, session),
        _settings(),
        [publication],
        provider=provider,
        vector_store=vector_store,
    )

    summary = service.build_embeddings(force=True)

    assert summary.generated_count == 1
    assert summary.skipped_count == 0
    assert len(vector_store.upserts) == 1
    assert vector_store.upserts[0]["payload"]["title"] == "A semantic map"
    assert vector_store.upserts[0]["payload"]["authors"] == ["Ada Lovelace"]
    assert (
        vector_store.upserts[0]["payload"]["content_text"]
        == "Title: A semantic map\n\n"
        "Authors: Ada Lovelace\n\n"
        "Abstract: Research metadata and graph analysis."
    )
    assert vector_store.upserts[0]["payload"]["doi"] == "10.1000/example"
    assert "embedding_provider" not in vector_store.upserts[0]["payload"]
    assert "embedding_model" not in vector_store.upserts[0]["payload"]
    assert "embedding_version" not in vector_store.upserts[0]["payload"]
    assert session.commit_calls == 1
    assert publication.embeddings[0].embedding_provider == "gemini"
    assert publication.embeddings[0].embedding_model == "gemini-embedding-001"
    assert publication.embeddings[0].embedding_version == "v1"


def test_gemini_provider_extracts_embedding_values_from_rest_shapes() -> None:
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        model_name="gemini-embedding-001",
        timeout_seconds=60,
        max_retries=3,
    )

    singular = provider._extract_embedding_values({"embedding": {"values": [0.1, 0.2]}})
    plural = provider._extract_embedding_values({"embeddings": [{"values": [0.3, 0.4]}]})

    assert singular == [0.1, 0.2]
    assert plural == [0.3, 0.4]


def test_reset_embeddings_deletes_collection_and_matching_metadata() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="A semantic map",
        normalized_title="a semantic map",
        abstract="Research metadata and graph analysis.",
    )
    target_embedding = PublicationEmbeddingModel(
        id=uuid4(),
        publication_id=publication.id,
        embedding_provider="gemini",
        qdrant_collection="publication_embeddings",
        qdrant_point_id="point-1",
        embedding_model="gemini-embedding-001",
        embedding_version="v1",
        content_hash="hash-1",
    )
    session = ResetFakeSession([target_embedding])
    vector_store = FakeVectorStore()
    service = FakePublicationEmbeddingService(
        cast(Session, session),
        _settings(),
        [publication],
        provider=FakeProvider([[0.1, 0.2]]),
        vector_store=vector_store,
    )
    publication.embeddings = [target_embedding]

    summary = service.reset_embeddings()

    assert summary.collection_deleted is True
    assert summary.deleted_metadata_count == 1
    assert vector_store.deleted_collections == ["publication_embeddings"]
    assert session.deleted == [target_embedding]
    assert session.commit_calls == 1
