from __future__ import annotations

import gzip
import hashlib
import json
import logging
import tarfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from eunigraph.core.config import Settings
from eunigraph.modules.catalog.infrastructure.models import (
    ExternalIdentifierModel,
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
    ResearcherAffiliationModel,
    ResearcherModel,
)
from eunigraph.modules.ingestion.infrastructure.models import (
    DataSourceModel,
    IngestionRunModel,
    SourceRecordModel,
)
from eunigraph.shared.utils import normalize_text

REQUIRED_ARCHIVES = (
    "publication.tar",
    "organization.tar",
    "datasource.tar",
    "project.tar",
    "relation.tar",
)
PROGRESS_LOG_INTERVAL = 100
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SeedStatus:
    dataset_path: str
    dataset_path_exists: bool
    required_files: dict[str, bool]
    table_counts: dict[str, int]
    latest_ingestion_run_id: str | None
    latest_ingestion_status: str | None


@dataclass(slots=True)
class SeedLoadError(Exception):
    category: str
    stage: str
    message: str
    status_code: int
    archive_name: str | None = None
    processed_records: int | None = None
    limit_per_file: int | None = None

    def detail(self) -> str:
        parts = [f"Seed {self.category} error during {self.stage}: {self.message}"]
        if self.archive_name:
            parts.append(f"archive={self.archive_name}")
        if self.processed_records is not None:
            parts.append(f"processed_records={self.processed_records}")
        if self.limit_per_file is not None:
            parts.append(f"limit_per_file={self.limit_per_file}")
        return " | ".join(parts)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail=self.detail(),
        )


class OpenAireBeginnersKitSeeder:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self._source_record_cache: dict[tuple[UUID, str, str], SourceRecordModel] = {}
        self._external_identifier_cache: dict[tuple[str, str, str], UUID] = {}
        self._organization_by_openaire_id: dict[str, OrganizationModel] = {}
        self._organization_by_ror_id: dict[str, OrganizationModel] = {}
        self._organization_by_normalized_name: dict[str, OrganizationModel] = {}
        self._researcher_by_orcid: dict[str, ResearcherModel] = {}
        self._researcher_by_normalized_name: dict[str, ResearcherModel] = {}
        self._publication_by_openaire_id: dict[str, PublicationModel] = {}
        self._publication_by_doi: dict[str, PublicationModel] = {}
        self._publication_by_title_year: dict[tuple[str, int | None], PublicationModel] = {}
        self._publication_author_researchers: dict[UUID, set[UUID]] = {}
        self._publication_author_positions: dict[UUID, set[int]] = {}
        self._publication_organization_relations: set[tuple[UUID, UUID, str]] = set()
        self._researcher_affiliation_pairs: set[tuple[UUID, UUID]] = set()
        self._researcher_affiliations_by_researcher: dict[
            UUID,
            list[ResearcherAffiliationModel],
        ] = {}
        self._researcher_affiliation_orgs: dict[UUID, set[UUID]] = {}

    def get_status(self) -> SeedStatus:
        dataset_path = Path(self.settings.openaire_beginners_kit_path)
        latest_run = self.session.scalar(
            select(IngestionRunModel)
            .join(DataSourceModel, IngestionRunModel.data_source_id == DataSourceModel.id)
            .where(DataSourceModel.source_type == "openaire_beginners_kit")
            .order_by(IngestionRunModel.started_at.desc())
            .limit(1)
        )

        counts = {
            "data_source": self._count(DataSourceModel),
            "ingestion_run": self._count(IngestionRunModel),
            "source_record": self._count(SourceRecordModel),
            "organization": self._count(OrganizationModel),
            "researcher": self._count(ResearcherModel),
            "publication": self._count(PublicationModel),
            "publication_author": self._count(PublicationAuthorModel),
            "publication_organization": self._count(PublicationOrganizationModel),
            "researcher_affiliation": self._count(ResearcherAffiliationModel),
            "external_identifier": self._count(ExternalIdentifierModel),
        }

        return SeedStatus(
            dataset_path=str(dataset_path),
            dataset_path_exists=dataset_path.exists(),
            required_files={
                filename: (dataset_path / filename).exists()
                for filename in REQUIRED_ARCHIVES
            },
            table_counts=counts,
            latest_ingestion_run_id=str(latest_run.id) if latest_run else None,
            latest_ingestion_status=latest_run.status if latest_run else None,
        )

    def load(self, *, limit_per_file: int | None = None) -> dict[str, int | str | None]:
        dataset_path = self._validate_dataset_path()
        data_source = self._get_or_create_logical_source()
        logger.info(
            "OpenAIRE seed started dataset_path=%s limit_per_file=%s",
            dataset_path,
            limit_per_file,
        )

        ingestion_run = IngestionRunModel(
            data_source_id=data_source.id,
            status="running",
            triggered_by="admin-api",
            raw_config={"limit_per_file": limit_per_file},
        )
        self.session.add(ingestion_run)
        self.session.flush()
        self.session.commit()
        logger.info(
            "OpenAIRE seed ingestion run created ingestion_run_id=%s data_source_id=%s",
            ingestion_run.id,
            data_source.id,
        )

        counts = {
            "datasource_records": 0,
            "organization_records": 0,
            "publication_records": 0,
            "project_records": 0,
            "relation_records": 0,
        }

        try:
            counts["datasource_records"] = self._process_datasources(
                dataset_path / "datasource.tar",
                data_source.id,
                ingestion_run.id,
                limit_per_file,
            )
            counts["organization_records"] = self._process_organizations(
                dataset_path / "organization.tar",
                data_source.id,
                ingestion_run.id,
                limit_per_file,
            )
            counts["publication_records"] = self._process_publications(
                dataset_path / "publication.tar",
                data_source.id,
                ingestion_run.id,
                limit_per_file,
            )
            counts["project_records"] = self._process_projects(
                dataset_path / "project.tar",
                data_source.id,
                ingestion_run.id,
                limit_per_file,
            )
            counts["relation_records"] = self._process_relations(
                dataset_path / "relation.tar",
                data_source.id,
                ingestion_run.id,
                limit_per_file,
            )
            ingestion_run.status = "completed"
            ingestion_run.completed_at = datetime.now(UTC)
            self.session.commit()
            logger.info(
                "OpenAIRE seed completed ingestion_run_id=%s datasource_records=%s "
                "organization_records=%s publication_records=%s project_records=%s "
                "relation_records=%s",
                ingestion_run.id,
                counts["datasource_records"],
                counts["organization_records"],
                counts["publication_records"],
                counts["project_records"],
                counts["relation_records"],
            )
        except SeedLoadError as exc:
            self.session.rollback()
            logger.warning(
                "OpenAIRE seed failed ingestion_run_id=%s detail=%s",
                ingestion_run.id,
                exc.detail(),
                exc_info=True,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, exc.detail())
            raise exc.to_http_exception() from exc
        except MemoryError as exc:
            self.session.rollback()
            seed_error = SeedLoadError(
                category="resources",
                stage="seed execution",
                message="The seed loader exhausted available memory while processing the dataset",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                limit_per_file=limit_per_file,
            )
            logger.exception(
                "OpenAIRE seed resource failure ingestion_run_id=%s",
                ingestion_run.id,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, seed_error.detail())
            raise seed_error.to_http_exception() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            seed_error = SeedLoadError(
                category="db",
                stage="seed persistence",
                message=self._format_db_error(exc),
                status_code=status.HTTP_409_CONFLICT,
                limit_per_file=limit_per_file,
            )
            logger.exception(
                "OpenAIRE seed database failure ingestion_run_id=%s",
                ingestion_run.id,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, seed_error.detail())
            raise seed_error.to_http_exception() from exc
        except Exception as exc:  # pragma: no cover - defensive rollback path
            self.session.rollback()
            seed_error = SeedLoadError(
                category="integration",
                stage="seed execution",
                message=str(exc) or exc.__class__.__name__,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                limit_per_file=limit_per_file,
            )
            logger.exception(
                "OpenAIRE seed unexpected failure ingestion_run_id=%s",
                ingestion_run.id,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, seed_error.detail())
            raise seed_error.to_http_exception() from exc

        return {
            "dataset_path": str(dataset_path),
            "ingestion_run_id": str(ingestion_run.id),
            "limit_per_file": limit_per_file,
            **counts,
        }

    def reset(self) -> dict[str, int]:
        deleted_counts = {
            "publication_author": self._count(PublicationAuthorModel),
            "publication_organization": self._count(PublicationOrganizationModel),
            "researcher_affiliation": self._count(ResearcherAffiliationModel),
            "external_identifier": self._count(ExternalIdentifierModel),
            "publication": self._count(PublicationModel),
            "researcher": self._count(ResearcherModel),
            "organization": self._count(OrganizationModel),
            "source_record": self._count(SourceRecordModel),
            "ingestion_run": self._count(IngestionRunModel),
            "data_source": self._count(DataSourceModel),
        }
        self.session.execute(delete(PublicationAuthorModel))
        self.session.execute(delete(PublicationOrganizationModel))
        self.session.execute(delete(ResearcherAffiliationModel))
        self.session.execute(delete(ExternalIdentifierModel))
        self.session.execute(delete(PublicationModel))
        self.session.execute(delete(ResearcherModel))
        self.session.execute(delete(OrganizationModel))
        self.session.execute(delete(SourceRecordModel))
        self.session.execute(delete(IngestionRunModel))
        self.session.execute(delete(DataSourceModel))
        self.session.commit()
        return deleted_counts

    def _count(self, model: type[Any]) -> int:
        return int(self.session.scalar(select(func.count()).select_from(model)) or 0)

    def _validate_dataset_path(self) -> Path:
        dataset_path = Path(self.settings.openaire_beginners_kit_path)
        if not dataset_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OPENAIRE_BEGINNERS_KIT_PATH does not exist: {dataset_path}",
            )

        missing = [
            filename
            for filename in REQUIRED_ARCHIVES
            if not (dataset_path / filename).exists()
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing Beginner's Kit archive(s): {', '.join(missing)}",
            )

        return dataset_path

    def _get_or_create_logical_source(self) -> DataSourceModel:
        source = self.session.scalar(
            select(DataSourceModel).where(DataSourceModel.name == "OpenAIRE Beginner's Kit")
        )
        if source is None:
            source = DataSourceModel(
                name="OpenAIRE Beginner's Kit",
                source_type="openaire_beginners_kit",
                description=(
                    "Manual local seed from official OpenAIRE Beginner's Kit "
                    ".tar archives."
                ),
                is_active=True,
            )
            self.session.add(source)
            self.session.flush()
        return source

    def _iter_archive_records(
        self,
        archive_path: Path,
        *,
        limit: int | None,
    ) -> Iterator[dict[str, Any]]:
        yielded = 0
        try:
            with tarfile.open(archive_path, mode="r") as archive:
                for member in archive:
                    if not member.isfile() or not member.name.endswith(".gz"):
                        continue

                    extracted = archive.extractfile(member)
                    if extracted is None:
                        continue

                    try:
                        with gzip.open(extracted, mode="rt", encoding="utf-8") as handle:
                            for line_number, line in enumerate(handle, start=1):
                                if limit is not None and yielded >= limit:
                                    return
                                stripped = line.strip()
                                if not stripped:
                                    continue
                                try:
                                    payload = json.loads(stripped)
                                except JSONDecodeError as exc:
                                    raise SeedLoadError(
                                        category="parsing",
                                        stage="json parsing",
                                        message=(
                                            f"Invalid JSON record in {member.name} at line "
                                            f"{line_number}: {exc.msg}"
                                        ),
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        archive_name=archive_path.name,
                                        processed_records=yielded,
                                        limit_per_file=limit,
                                    ) from exc
                                yielded += 1
                                yield payload
                    except (OSError, UnicodeDecodeError) as exc:
                        raise SeedLoadError(
                            category="parsing",
                            stage="archive decompression",
                            message=f"Unable to read archive member {member.name}: {exc}",
                            status_code=status.HTTP_400_BAD_REQUEST,
                            archive_name=archive_path.name,
                            processed_records=yielded,
                            limit_per_file=limit,
                        ) from exc
        except tarfile.TarError as exc:
            raise SeedLoadError(
                category="parsing",
                stage="archive parsing",
                message=f"Unable to open archive {archive_path.name}: {exc}",
                status_code=status.HTTP_400_BAD_REQUEST,
                archive_name=archive_path.name,
                processed_records=yielded,
                limit_per_file=limit,
            ) from exc

    def _create_source_record(
        self,
        *,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        entity_type: str,
        source_identifier: str,
        payload: dict[str, Any],
    ) -> SourceRecordModel:
        checksum = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        cache_key = (ingestion_run_id, entity_type, source_identifier)
        cached_record = self._source_record_cache.get(cache_key)
        if cached_record is not None:
            if cached_record.checksum != checksum:
                logger.warning(
                    "OpenAIRE seed encountered duplicate source record with changed payload "
                    "ingestion_run_id=%s entity_type=%s source_identifier=%s",
                    ingestion_run_id,
                    entity_type,
                    source_identifier,
                )
            else:
                logger.info(
                    "OpenAIRE seed skipped duplicate source record "
                    "ingestion_run_id=%s entity_type=%s source_identifier=%s",
                    ingestion_run_id,
                    entity_type,
                    source_identifier,
                )
            return cached_record

        record = SourceRecordModel(
            data_source_id=data_source_id,
            ingestion_run_id=ingestion_run_id,
            entity_type=entity_type,
            source_identifier=source_identifier,
            checksum=checksum,
            raw_payload=payload,
        )
        self.session.add(record)
        self.session.flush()
        self._source_record_cache[cache_key] = record
        return record

    def _process_datasources(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
        self._log_archive_start("datasource", archive_path, limit, ingestion_run_id)
        try:
            for payload in self._iter_archive_records(archive_path, limit=limit):
                source_identifier = self._payload_identifier(payload)
                self._create_source_record(
                    data_source_id=data_source_id,
                    ingestion_run_id=ingestion_run_id,
                    entity_type="datasource",
                    source_identifier=source_identifier,
                    payload=payload,
                )
                processed += 1
                self._log_archive_progress("datasource", archive_path, processed, limit)
        except SeedLoadError:
            raise
        except SQLAlchemyError as exc:
            raise self._build_seed_db_error(
                stage="datasource persistence",
                archive_path=archive_path,
                processed_records=processed,
                limit=limit,
                exc=exc,
            ) from exc
        self._log_archive_complete("datasource", archive_path, processed, limit)
        return processed

    def _process_projects(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
        self._log_archive_start("project", archive_path, limit, ingestion_run_id)
        try:
            for payload in self._iter_archive_records(archive_path, limit=limit):
                source_identifier = self._payload_identifier(payload)
                self._create_source_record(
                    data_source_id=data_source_id,
                    ingestion_run_id=ingestion_run_id,
                    entity_type="project",
                    source_identifier=source_identifier,
                    payload=payload,
                )
                processed += 1
                self._log_archive_progress("project", archive_path, processed, limit)
        except SeedLoadError:
            raise
        except SQLAlchemyError as exc:
            raise self._build_seed_db_error(
                stage="project persistence",
                archive_path=archive_path,
                processed_records=processed,
                limit=limit,
                exc=exc,
            ) from exc
        self._log_archive_complete("project", archive_path, processed, limit)
        return processed

    def _process_organizations(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
        self._log_archive_start("organization", archive_path, limit, ingestion_run_id)
        try:
            for payload in self._iter_archive_records(archive_path, limit=limit):
                source_identifier = self._payload_identifier(payload)
                self._create_source_record(
                    data_source_id=data_source_id,
                    ingestion_run_id=ingestion_run_id,
                    entity_type="organization",
                    source_identifier=source_identifier,
                    payload=payload,
                )
                self._upsert_organization(payload)
                processed += 1
                self._log_archive_progress("organization", archive_path, processed, limit)
            self.session.flush()
        except SeedLoadError:
            raise
        except SQLAlchemyError as exc:
            raise self._build_seed_db_error(
                stage="organization persistence",
                archive_path=archive_path,
                processed_records=processed,
                limit=limit,
                exc=exc,
            ) from exc
        self._log_archive_complete("organization", archive_path, processed, limit)
        return processed

    def _process_publications(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
        self._log_archive_start("publication", archive_path, limit, ingestion_run_id)
        try:
            for payload in self._iter_archive_records(archive_path, limit=limit):
                source_identifier = self._payload_identifier(payload)
                source_record = self._create_source_record(
                    data_source_id=data_source_id,
                    ingestion_run_id=ingestion_run_id,
                    entity_type="publication",
                    source_identifier=source_identifier,
                    payload=payload,
                )
                publication = self._upsert_publication(payload, source_record.id)
                self._upsert_publication_authors(publication, payload, source_record.id)
                self._upsert_publication_identifiers(publication, payload, source_record.id)
                processed += 1
                self._log_archive_progress("publication", archive_path, processed, limit)
            self.session.flush()
        except SeedLoadError:
            raise
        except SQLAlchemyError as exc:
            raise self._build_seed_db_error(
                stage="publication persistence",
                archive_path=archive_path,
                processed_records=processed,
                limit=limit,
                exc=exc,
            ) from exc
        self._log_archive_complete("publication", archive_path, processed, limit)
        return processed

    def _process_relations(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
        self._log_archive_start("relation", archive_path, limit, ingestion_run_id)
        try:
            for payload in self._iter_archive_records(archive_path, limit=limit):
                source_identifier = self._payload_identifier(payload)
                source_record = self._create_source_record(
                    data_source_id=data_source_id,
                    ingestion_run_id=ingestion_run_id,
                    entity_type="relation",
                    source_identifier=source_identifier,
                    payload=payload,
                )
                self._map_publication_organization_relation(payload, source_record.id)
                self._map_researcher_affiliation_relation(payload, source_record.id)
                processed += 1
                self._log_archive_progress("relation", archive_path, processed, limit)
            self.session.flush()
        except SeedLoadError:
            raise
        except SQLAlchemyError as exc:
            raise self._build_seed_db_error(
                stage="relation persistence",
                archive_path=archive_path,
                processed_records=processed,
                limit=limit,
                exc=exc,
            ) from exc
        self._log_archive_complete("relation", archive_path, processed, limit)
        return processed

    def _upsert_organization(self, payload: dict[str, Any]) -> OrganizationModel:
        openaire_id = self._payload_identifier(payload)
        ror_id = self._extract_ror(payload)
        organization_name = self._coalesce(
            payload.get("legalname"),
            payload.get("legalshortname"),
            payload.get("officialname"),
        )
        normalized_name = normalize_text(
            organization_name,
        )

        organization = None
        if openaire_id:
            organization = self._organization_by_openaire_id.get(openaire_id)
            if organization is None:
                organization = self.session.scalar(
                    select(OrganizationModel).where(OrganizationModel.openaire_id == openaire_id)
                )
                if organization is not None:
                    self._register_organization_cache(organization)
        if organization is None and ror_id:
            organization = self._organization_by_ror_id.get(ror_id)
            if organization is None:
                organization = self.session.scalar(
                    select(OrganizationModel).where(OrganizationModel.ror_id == ror_id),
                )
                if organization is not None:
                    self._register_organization_cache(organization)
        if organization is None and normalized_name:
            organization = self._organization_by_normalized_name.get(normalized_name)
            if organization is None:
                organization = self.session.scalar(
                    select(OrganizationModel).where(
                        OrganizationModel.normalized_name == normalized_name,
                    ),
                )
                if organization is not None:
                    self._register_organization_cache(organization)

        if organization is None:
            initial_name = (
                self._coalesce(
                    payload.get("legalshortname"),
                    payload.get("legalname"),
                    payload.get("officialname"),
                    openaire_id,
                )
                or openaire_id
            )
            organization = OrganizationModel(
                name=self._clip_text(
                    initial_name,
                    max_length=255,
                    field_name="organization.name",
                )
                or initial_name,
                normalized_name=self._clip_text(
                    normalized_name,
                    max_length=255,
                    field_name="organization.normalized_name",
                )
                or normalized_name,
            )
            self.session.add(organization)

        resolved_name = self._coalesce(
            payload.get("legalshortname"),
            payload.get("legalname"),
            payload.get("officialname"),
            organization.name,
        )
        organization.name = (
            self._clip_text(
                resolved_name,
                max_length=255,
                field_name="organization.name",
            )
            or organization.name
        )
        organization.normalized_name = (
            self._clip_text(
                normalize_text(organization.name),
                max_length=255,
                field_name="organization.normalized_name",
            )
            or organization.normalized_name
        )
        organization.organization_type = (
            self._clip_text(
                self._extract_value(payload.get("type")),
                max_length=64,
                field_name="organization.organization_type",
            )
            or organization.organization_type
        )
        organization.country_code = self._extract_country_code(payload) or organization.country_code
        organization.city = (
            self._clip_text(
                self._coalesce(payload.get("city")),
                max_length=120,
                field_name="organization.city",
            )
            or organization.city
        )
        organization.website = (
            self._extract_first(payload.get("websiteurl")) or organization.website
        )
        organization.ror_id = self._assign_unique_entity_value(
            model=organization,
            value=ror_id,
            current_value=organization.ror_id,
            field_name="organization.ror_id",
            cache=self._organization_by_ror_id,
            model_class=OrganizationModel,
            model_field="ror_id",
        )
        organization.openaire_id = self._assign_unique_entity_value(
            model=organization,
            value=openaire_id,
            current_value=organization.openaire_id,
            field_name="organization.openaire_id",
            cache=self._organization_by_openaire_id,
            model_class=OrganizationModel,
            model_field="openaire_id",
        )
        self.session.flush()
        self._register_organization_cache(organization)
        return organization

    def _upsert_publication(
        self,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> PublicationModel:
        title = (
            self._coalesce(
                payload.get("maintitle"),
                payload.get("mainTitle"),
                payload.get("title"),
                "Untitled",
            )
            or "Untitled"
        )
        normalized_title = normalize_text(title)
        doi = self._extract_pid_value(payload.get("pid"), "doi")
        openaire_id = self._payload_identifier(payload)
        publication_year = self._extract_publication_year(payload)

        publication = None
        if openaire_id:
            publication = self._publication_by_openaire_id.get(openaire_id)
            if publication is None:
                publication = self.session.scalar(
                    select(PublicationModel).where(PublicationModel.openaire_id == openaire_id)
                )
                if publication is not None:
                    self._register_publication_cache(publication)
        if publication is None and doi:
            publication = self._publication_by_doi.get(doi)
            if publication is None:
                publication = self.session.scalar(
                    select(PublicationModel).where(PublicationModel.doi == doi),
                )
                if publication is not None:
                    self._register_publication_cache(publication)
        if publication is None:
            publication = self._publication_by_title_year.get((normalized_title, publication_year))
            if publication is None:
                publication = self.session.scalar(
                    select(PublicationModel).where(
                        PublicationModel.normalized_title == normalized_title,
                        PublicationModel.publication_year == publication_year,
                    )
                )
                if publication is not None:
                    self._register_publication_cache(publication)

        if publication is None:
            publication = PublicationModel(title=title, normalized_title=normalized_title)
            self.session.add(publication)

        publication.title = title
        publication.normalized_title = normalized_title
        publication.abstract = (
            self._extract_first(payload.get("description")) or publication.abstract
        )
        publication.publication_date = self._parse_date(
            self._coalesce(payload.get("publicationdate")),
        )
        publication.publication_year = publication_year
        publication.doi = self._assign_unique_entity_value(
            model=publication,
            value=doi,
            current_value=publication.doi,
            field_name="publication.doi",
            cache=self._publication_by_doi,
            model_class=PublicationModel,
            model_field="doi",
        )
        publication.openaire_id = self._assign_unique_entity_value(
            model=publication,
            value=openaire_id,
            current_value=publication.openaire_id,
            field_name="publication.openaire_id",
            cache=self._publication_by_openaire_id,
            model_class=PublicationModel,
            model_field="openaire_id",
        )
        publication.publication_type = (
            self._clip_text(
                self._extract_value(payload.get("type")),
                max_length=64,
                field_name="publication.publication_type",
            )
            or publication.publication_type
        )
        publication.language_code = self._extract_language_code(
            payload.get("language"),
        ) or publication.language_code
        publication.journal_name = (
            self._clip_text(
                self._extract_container_name(payload),
                max_length=255,
                field_name="publication.journal_name",
            )
            or publication.journal_name
        )
        publication.venue_name = (
            self._clip_text(
                self._extract_first(payload.get("source")),
                max_length=255,
                field_name="publication.venue_name",
            )
            or publication.venue_name
        )
        publication.publisher = (
            self._clip_text(
                self._coalesce(payload.get("publisher")),
                max_length=255,
                field_name="publication.publisher",
            )
            or publication.publisher
        )
        publication.open_access = self._extract_open_access(payload)
        publication.source_url = (
            self._extract_first_from_instances(payload, "url")
            or publication.source_url
        )
        publication.canonical_source_record_id = source_record_id
        self.session.flush()
        self._register_publication_cache(publication)
        return publication

    def _upsert_publication_authors(
        self,
        publication: PublicationModel,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        seen_researcher_ids = set(
            self._publication_author_researchers.get(publication.id, set()),
        )
        used_positions = set(self._publication_author_positions.get(publication.id, set()))
        if not seen_researcher_ids and not used_positions:
            existing_relations = list(
                self.session.scalars(
                    select(PublicationAuthorModel).where(
                        PublicationAuthorModel.publication_id == publication.id,
                    )
                )
            )
            seen_researcher_ids = {relation.researcher_id for relation in existing_relations}
            used_positions = {relation.author_position for relation in existing_relations}
            self._publication_author_researchers[publication.id] = set(seen_researcher_ids)
            self._publication_author_positions[publication.id] = set(used_positions)

        for author_payload in payload.get("author") or []:
            raw_full_name = self._coalesce(
                author_payload.get("fullname"),
                author_payload.get("fullName"),
            )
            if not raw_full_name:
                continue
            full_name = (
                self._clip_text(
                    raw_full_name,
                    max_length=255,
                    field_name="researcher.full_name",
                )
                or raw_full_name
            )

            orcid = self._extract_nested_pid_value(author_payload.get("pid"), "orcid")
            researcher = None
            if orcid:
                researcher = self._researcher_by_orcid.get(orcid)
                if researcher is None:
                    researcher = self.session.scalar(
                        select(ResearcherModel).where(ResearcherModel.orcid == orcid),
                    )
                    if researcher is not None:
                        self._register_researcher_cache(researcher)
            if researcher is None:
                normalized_author_name = (
                    self._clip_text(
                        normalize_text(raw_full_name),
                        max_length=255,
                        field_name="researcher.normalized_name",
                    )
                    or normalize_text(raw_full_name)
                )
                researcher = self._researcher_by_normalized_name.get(normalized_author_name)
                if researcher is None:
                    researcher = self.session.scalar(
                        select(ResearcherModel).where(
                            ResearcherModel.normalized_name == normalized_author_name,
                        ),
                    )
                    if researcher is not None:
                        self._register_researcher_cache(researcher)

            if researcher is None:
                researcher = ResearcherModel(
                    full_name=full_name,
                    given_name=self._clip_text(
                        self._coalesce(author_payload.get("name")),
                        max_length=120,
                        field_name="researcher.given_name",
                    ),
                    family_name=self._clip_text(
                        self._coalesce(author_payload.get("surname")),
                        max_length=120,
                        field_name="researcher.family_name",
                    ),
                    normalized_name=(
                        self._clip_text(
                            normalize_text(raw_full_name),
                            max_length=255,
                            field_name="researcher.normalized_name",
                        )
                        or normalize_text(raw_full_name)
                    ),
                    display_name=self._clip_text(
                        raw_full_name,
                        max_length=255,
                        field_name="researcher.display_name",
                    )
                    or full_name,
                    orcid=None,
                )
                researcher.orcid = self._assign_unique_entity_value(
                    model=researcher,
                    value=orcid,
                    current_value=researcher.orcid,
                    field_name="researcher.orcid",
                    cache=self._researcher_by_orcid,
                    model_class=ResearcherModel,
                    model_field="orcid",
                )
                self.session.add(researcher)
                self.session.flush()
                self._register_researcher_cache(researcher)
            else:
                researcher.orcid = self._assign_unique_entity_value(
                    model=researcher,
                    value=orcid,
                    current_value=researcher.orcid,
                    field_name="researcher.orcid",
                    cache=self._researcher_by_orcid,
                    model_class=ResearcherModel,
                    model_field="orcid",
                )
                self._register_researcher_cache(researcher)

            if researcher.id in seen_researcher_ids:
                logger.info(
                    "OpenAIRE seed skipped duplicate publication_author relation "
                    "publication_id=%s researcher_id=%s source_record_id=%s author_name=%s",
                    publication.id,
                    researcher.id,
                    source_record_id,
                    full_name,
                )
                continue

            preferred_position = self._parse_author_position(author_payload.get("rank"))
            author_position = self._next_available_author_position(
                preferred_position,
                used_positions,
            )
            if preferred_position != author_position:
                logger.info(
                    "OpenAIRE seed normalized author position publication_id=%s "
                    "researcher_id=%s preferred_position=%s assigned_position=%s",
                    publication.id,
                    researcher.id,
                    preferred_position,
                    author_position,
                )

            relation = PublicationAuthorModel(
                publication_id=publication.id,
                researcher_id=researcher.id,
                author_position=author_position,
                author_list_name=self._clip_text(
                    raw_full_name,
                    max_length=255,
                    field_name="publication_author.author_list_name",
                )
                or full_name,
                source_record_id=source_record_id,
            )
            self.session.add(relation)
            seen_researcher_ids.add(researcher.id)
            self._publication_author_researchers.setdefault(publication.id, set()).add(
                researcher.id
            )
            self._publication_author_positions.setdefault(publication.id, set()).add(
                author_position
            )

    def _upsert_publication_identifiers(
        self,
        publication: PublicationModel,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        identifiers: list[tuple[str, str]] = []
        seen_identifiers: set[tuple[str, str]] = set()

        for pid in payload.get("pid") or []:
            identifier_type = (pid.get("scheme") or "").lower().strip()
            identifier_value = (pid.get("value") or "").strip()
            if identifier_type and identifier_value:
                identifier_key = (identifier_type, identifier_value)
                if identifier_key in seen_identifiers:
                    logger.info(
                        "OpenAIRE seed skipped duplicate publication identifier in payload "
                        "publication_id=%s identifier_type=%s identifier_value=%s",
                        publication.id,
                        identifier_type,
                        identifier_value,
                    )
                    continue
                seen_identifiers.add(identifier_key)
                identifiers.append(identifier_key)

        for original_id in payload.get("originalId") or []:
            if isinstance(original_id, str) and original_id.strip():
                identifier_key = ("original_id", original_id.strip())
                if identifier_key in seen_identifiers:
                    logger.info(
                        "OpenAIRE seed skipped duplicate publication identifier in payload "
                        "publication_id=%s identifier_type=%s identifier_value=%s",
                        publication.id,
                        identifier_key[0],
                        identifier_key[1],
                    )
                    continue
                seen_identifiers.add(identifier_key)
                identifiers.append(identifier_key)

        for identifier_type, identifier_value in identifiers:
            cache_key = ("publication", identifier_type, identifier_value)
            cached_entity_id = self._external_identifier_cache.get(cache_key)
            if cached_entity_id is not None:
                if cached_entity_id == publication.id:
                    logger.info(
                        "OpenAIRE seed skipped duplicate cached external identifier "
                        "publication_id=%s identifier_type=%s identifier_value=%s",
                        publication.id,
                        identifier_type,
                        identifier_value,
                    )
                else:
                    logger.warning(
                        "OpenAIRE seed skipped conflicting external identifier "
                        "publication_id=%s existing_publication_id=%s identifier_type=%s "
                        "identifier_value=%s",
                        publication.id,
                        cached_entity_id,
                        identifier_type,
                        identifier_value,
                    )
                continue

            existing = self.session.scalar(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "publication",
                    ExternalIdentifierModel.identifier_type == identifier_type,
                    ExternalIdentifierModel.identifier_value == identifier_value,
                )
            )
            if existing is not None:
                self._external_identifier_cache[cache_key] = existing.entity_id
                if existing.entity_id != publication.id:
                    logger.warning(
                        "OpenAIRE seed skipped pre-existing external identifier conflict "
                        "publication_id=%s existing_publication_id=%s identifier_type=%s "
                        "identifier_value=%s",
                        publication.id,
                        existing.entity_id,
                        identifier_type,
                        identifier_value,
                    )
                continue

            self.session.add(
                ExternalIdentifierModel(
                    entity_type="publication",
                    entity_id=publication.id,
                    identifier_type=identifier_type,
                    identifier_value=identifier_value,
                    is_primary=identifier_type == "doi" and identifier_value == publication.doi,
                    source_record_id=source_record_id,
                )
            )
            self._external_identifier_cache[cache_key] = publication.id
    def _map_publication_organization_relation(
        self,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        resolved = self._resolve_publication_organization_relation(payload)
        if resolved is None:
            return

        publication, organization, relation_type = resolved
        cache_key = (publication.id, organization.id, relation_type)
        if cache_key in self._publication_organization_relations:
            logger.info(
                "OpenAIRE seed skipped duplicate publication_organization relation "
                "publication_id=%s organization_id=%s relation_type=%s",
                publication.id,
                organization.id,
                relation_type,
            )
            return

        existing = self.session.scalar(
            select(PublicationOrganizationModel).where(
                PublicationOrganizationModel.publication_id == publication.id,
                PublicationOrganizationModel.organization_id == organization.id,
                PublicationOrganizationModel.relation_type == relation_type,
            )
        )
        if existing is None:
            self.session.add(
                PublicationOrganizationModel(
                    publication_id=publication.id,
                    organization_id=organization.id,
                    relation_type=relation_type,
                    source_record_id=source_record_id,
                )
            )
        self._publication_organization_relations.add(cache_key)

    def _map_researcher_affiliation_relation(
        self,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        if not self._is_affiliation_relation(payload):
            return

        resolved = self._resolve_publication_organization_relation(payload)
        if resolved is None:
            return

        publication, organization, _relation_type = resolved
        authors = list(
            self.session.scalars(
                select(PublicationAuthorModel).where(
                    PublicationAuthorModel.publication_id == publication.id,
                )
            )
        )
        if len(authors) != 1:
            return

        self._upsert_researcher_affiliation(
            researcher_id=authors[0].researcher_id,
            organization_id=organization.id,
            source_record_id=source_record_id,
        )

    def _upsert_researcher_affiliation(
        self,
        *,
        researcher_id: UUID,
        organization_id: UUID,
        source_record_id: UUID,
    ) -> None:
        cache_key = (researcher_id, organization_id)
        if cache_key in self._researcher_affiliation_pairs:
            return

        existing_affiliations = self._researcher_affiliations_by_researcher.get(researcher_id)
        if existing_affiliations is None:
            existing_affiliations = list(
                self.session.scalars(
                    select(ResearcherAffiliationModel).where(
                        ResearcherAffiliationModel.researcher_id == researcher_id,
                    )
                )
            )
            self._researcher_affiliations_by_researcher[researcher_id] = existing_affiliations
            self._researcher_affiliation_orgs[researcher_id] = {
                affiliation.organization_id for affiliation in existing_affiliations
            }
            self._researcher_affiliation_pairs.update(
                (affiliation.researcher_id, affiliation.organization_id)
                for affiliation in existing_affiliations
            )
            if cache_key in self._researcher_affiliation_pairs:
                return

        affiliation = ResearcherAffiliationModel(
            researcher_id=researcher_id,
            organization_id=organization_id,
            is_primary=False,
            source_record_id=source_record_id,
        )
        self.session.add(affiliation)
        self.session.flush()

        self._researcher_affiliations_by_researcher.setdefault(
            researcher_id,
            [],
        ).append(affiliation)
        self._researcher_affiliation_orgs.setdefault(researcher_id, set()).add(organization_id)
        self._researcher_affiliation_pairs.add(cache_key)
        self._refresh_researcher_primary_organization(researcher_id)

    def _refresh_researcher_primary_organization(self, researcher_id: UUID) -> None:
        researcher = self.session.get(ResearcherModel, researcher_id)
        if researcher is None:
            return

        affiliations = self._researcher_affiliations_by_researcher.get(researcher_id)
        if affiliations is None:
            affiliations = list(
                self.session.scalars(
                    select(ResearcherAffiliationModel).where(
                        ResearcherAffiliationModel.researcher_id == researcher_id,
                    )
                )
            )
            self._researcher_affiliations_by_researcher[researcher_id] = affiliations
            self._researcher_affiliation_orgs[researcher_id] = {
                affiliation.organization_id for affiliation in affiliations
            }

        organization_ids = self._researcher_affiliation_orgs.get(researcher_id, set())
        if len(organization_ids) == 1:
            primary_organization_id = next(iter(organization_ids))
            researcher.primary_organization_id = primary_organization_id
            for affiliation in affiliations:
                affiliation.is_primary = affiliation.organization_id == primary_organization_id
        else:
            researcher.primary_organization_id = None
            for affiliation in affiliations:
                affiliation.is_primary = False

        self._register_researcher_cache(researcher)

    def _resolve_publication_organization_relation(
        self,
        payload: dict[str, Any],
    ) -> tuple[PublicationModel, OrganizationModel, str] | None:
        source_id = payload.get("source")
        target_id = payload.get("target")
        if not isinstance(source_id, str) or not isinstance(target_id, str):
            return None

        relation_type = self._extract_relation_type(payload)
        source_type = self._extract_relation_side_type(payload.get("sourceType"))
        target_type = self._extract_relation_side_type(payload.get("targetType"))

        organization_identifier: str | None = None
        publication_identifier: str | None = None

        if self._is_organization_type(source_type) and self._is_publication_type(target_type):
            organization_identifier = source_id
            publication_identifier = target_id
        elif self._is_publication_type(source_type) and self._is_organization_type(target_type):
            publication_identifier = source_id
            organization_identifier = target_id
        else:
            return None

        organization = self._organization_by_openaire_id.get(organization_identifier)
        if organization is None:
            organization = self.session.scalar(
                select(OrganizationModel).where(
                    OrganizationModel.openaire_id == organization_identifier,
                )
            )
            if organization is not None:
                self._register_organization_cache(organization)

        publication = self._publication_by_openaire_id.get(publication_identifier)
        if publication is None:
            publication = self.session.scalar(
                select(PublicationModel).where(
                    PublicationModel.openaire_id == publication_identifier,
                )
            )
            if publication is not None:
                self._register_publication_cache(publication)

        if organization is None or publication is None:
            return None

        return publication, organization, relation_type

    def _payload_identifier(self, payload: dict[str, Any]) -> str:
        identifier = payload.get("id")
        if isinstance(identifier, str) and identifier.strip():
            return identifier.strip()

        original_ids = payload.get("originalId")
        if isinstance(original_ids, list):
            for original_id in original_ids:
                if isinstance(original_id, str) and original_id.strip():
                    return original_id.strip()

        source_id = payload.get("source")
        target_id = payload.get("target")
        relation_type = self._extract_relation_type(payload)
        if isinstance(source_id, str) and isinstance(target_id, str):
            return f"relation::{source_id}::{target_id}::{relation_type}"

        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8"),
        ).hexdigest()
        return f"generated::{payload_hash}"

    def _extract_ror(self, payload: dict[str, Any]) -> str | None:
        for pid in payload.get("pid") or []:
            identifier_type = (pid.get("scheme") or "").lower().strip()
            identifier_value = (pid.get("value") or "").strip()
            if identifier_type == "ror" and identifier_value:
                return identifier_value
        return None

    def _extract_pid_value(self, pids: Any, identifier_type: str) -> str | None:
        for pid in pids or []:
            scheme = (pid.get("scheme") or "").lower().strip()
            value = (pid.get("value") or "").strip()
            if scheme == identifier_type and value:
                return value
        return None

    def _extract_nested_pid_value(self, pid_payload: Any, identifier_type: str) -> str | None:
        if not isinstance(pid_payload, dict):
            return None
        pid_data = pid_payload.get("id") or {}
        scheme = (pid_data.get("scheme") or "").lower().strip()
        value = (pid_data.get("value") or "").strip()
        if scheme == identifier_type and value:
            return value
        return None

    def _extract_publication_year(self, payload: dict[str, Any]) -> int | None:
        publication_date = self._coalesce(payload.get("publicationdate"))
        parsed = self._parse_date(publication_date)
        return parsed.year if parsed else None

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None

    def _extract_first(self, value: Any) -> str | None:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
            return None
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _clip_text(
        self,
        value: str | None,
        *,
        max_length: int,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None
        if len(value) <= max_length:
            return value
        logger.info(
            "OpenAIRE seed truncated overlong field field=%s original_length=%s max_length=%s",
            field_name,
            len(value),
            max_length,
        )
        return value[:max_length].rstrip()

    def _same_entity(self, left: Any, right: Any) -> bool:
        if left is right:
            return True
        left_id = getattr(left, "id", None)
        right_id = getattr(right, "id", None)
        if left_id is None or right_id is None:
            return False
        return bool(left_id == right_id)

    def _assign_unique_entity_value(
        self,
        *,
        model: Any,
        value: str | None,
        current_value: str | None,
        field_name: str,
        cache: dict[str, Any],
        model_class: type[Any],
        model_field: str,
    ) -> str | None:
        if not value:
            return current_value
        if current_value == value:
            cache[value] = model
            return current_value

        cached_model = cache.get(value)
        if cached_model is None:
            cached_model = self.session.scalar(
                select(model_class).where(getattr(model_class, model_field) == value),
            )
            if cached_model is not None:
                cache[value] = cached_model

        if cached_model is not None and not self._same_entity(cached_model, model):
            logger.warning(
                "OpenAIRE seed skipped conflicting unique field field=%s value=%s "
                "entity_id=%s existing_entity_id=%s",
                field_name,
                value,
                model.id,
                cached_model.id,
            )
            return current_value

        cache[value] = model
        return value

    def _register_organization_cache(self, organization: OrganizationModel) -> None:
        if organization.openaire_id:
            self._organization_by_openaire_id[organization.openaire_id] = organization
        if organization.ror_id:
            self._organization_by_ror_id[organization.ror_id] = organization
        if organization.normalized_name:
            self._organization_by_normalized_name[organization.normalized_name] = organization

    def _register_researcher_cache(self, researcher: ResearcherModel) -> None:
        if researcher.orcid:
            self._researcher_by_orcid[researcher.orcid] = researcher
        if researcher.normalized_name:
            self._researcher_by_normalized_name[researcher.normalized_name] = researcher

    def _register_publication_cache(self, publication: PublicationModel) -> None:
        if publication.openaire_id:
            self._publication_by_openaire_id[publication.openaire_id] = publication
        if publication.doi:
            self._publication_by_doi[publication.doi] = publication
        self._publication_by_title_year[
            (publication.normalized_title, publication.publication_year)
        ] = publication

    def _extract_value(self, value: Any) -> str | None:
        if isinstance(value, dict):
            for key in ("value", "label", "code", "name"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            return None
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _extract_language_code(self, value: Any) -> str | None:
        if isinstance(value, dict):
            for key in ("code", "iso", "isoCode", "value"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()[:16]
            for key in ("label", "name"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    stripped = candidate.strip()
                    if len(stripped) <= 16:
                        return stripped
                    logger.info(
                        "OpenAIRE seed skipped overlong language label value=%s",
                        stripped,
                    )
                    return None
            return None
        if isinstance(value, str) and value.strip():
            stripped = value.strip()
            if len(stripped) <= 16:
                return stripped
            logger.info(
                "OpenAIRE seed skipped overlong language value value=%s",
                stripped,
            )
        return None

    def _extract_container_name(self, payload: dict[str, Any]) -> str | None:
        container = payload.get("container")
        if isinstance(container, dict):
            name = container.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return None

    def _extract_open_access(self, payload: dict[str, Any]) -> bool | None:
        access_right = payload.get("bestaccessright")
        access_value = self._extract_value(access_right)
        if access_value is None:
            return None
        return access_value.casefold() in {"open", "openaccess", "open access"}

    def _extract_country_code(self, payload: dict[str, Any]) -> str | None:
        country = payload.get("country")
        if isinstance(country, dict):
            for key in ("code", "countryCode", "iso", "isoCode"):
                candidate = country.get(key)
                if isinstance(candidate, str) and len(candidate.strip()) == 2:
                    return candidate.strip().upper()

        country_value = self._extract_value(country)
        if country_value and len(country_value) == 2:
            return country_value.upper()
        return None

    def _extract_first_from_instances(self, payload: dict[str, Any], field_name: str) -> str | None:
        for instance in payload.get("instance") or []:
            if not isinstance(instance, dict):
                continue
            value = self._extract_first(instance.get(field_name))
            if value:
                return value
        return None

    def _extract_relation_type(self, payload: dict[str, Any]) -> str:
        reltype = payload.get("reltype")
        if isinstance(reltype, dict):
            for key in ("name", "value", "code", "label"):
                candidate = reltype.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        if isinstance(reltype, str) and reltype.strip():
            return reltype.strip()
        return "unknown"

    def _is_affiliation_relation(self, payload: dict[str, Any]) -> bool:
        reltype = payload.get("reltype")
        if isinstance(reltype, dict):
            relation_category = reltype.get("type")
            if (
                isinstance(relation_category, str)
                and relation_category.strip().casefold() == "affiliation"
            ):
                return True
        return self._extract_relation_type(payload).casefold() in {
            "hasauthorinstitution",
            "isauthorinstitutionof",
        }

    def _extract_relation_side_type(self, value: Any) -> str:
        if isinstance(value, dict):
            for key in ("name", "value", "code", "label"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip().casefold()
        if isinstance(value, str):
            return value.strip().casefold()
        return ""

    def _is_organization_type(self, value: str) -> bool:
        return "organization" in value or "org" == value

    def _is_publication_type(self, value: str) -> bool:
        return any(token in value for token in ("result", "publication", "researchproduct"))

    def _coalesce(self, *values: Any) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _parse_author_position(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        try:
            position = int(value)
        except (TypeError, ValueError):
            return None
        if position < 1:
            return None
        return position

    def _next_available_author_position(
        self,
        preferred_position: int | None,
        used_positions: set[int],
    ) -> int:
        if preferred_position is not None and preferred_position not in used_positions:
            used_positions.add(preferred_position)
            return preferred_position

        candidate = 1
        while candidate in used_positions:
            candidate += 1
        used_positions.add(candidate)
        return candidate

    def _log_archive_start(
        self,
        entity_type: str,
        archive_path: Path,
        limit: int | None,
        ingestion_run_id: UUID,
    ) -> None:
        logger.info(
            "OpenAIRE seed phase started entity_type=%s archive=%s ingestion_run_id=%s "
            "limit_per_file=%s",
            entity_type,
            archive_path.name,
            ingestion_run_id,
            limit,
        )

    def _log_archive_progress(
        self,
        entity_type: str,
        archive_path: Path,
        processed: int,
        limit: int | None,
    ) -> None:
        if processed % PROGRESS_LOG_INTERVAL != 0:
            return
        logger.info(
            "OpenAIRE seed phase progress entity_type=%s archive=%s processed_records=%s "
            "limit_per_file=%s",
            entity_type,
            archive_path.name,
            processed,
            limit,
        )

    def _log_archive_complete(
        self,
        entity_type: str,
        archive_path: Path,
        processed: int,
        limit: int | None,
    ) -> None:
        logger.info(
            "OpenAIRE seed phase completed entity_type=%s archive=%s processed_records=%s "
            "limit_per_file=%s",
            entity_type,
            archive_path.name,
            processed,
            limit,
        )

    def _format_db_error(self, exc: SQLAlchemyError) -> str:
        original = getattr(exc, "orig", None)
        return str(original or exc)

    def _build_seed_db_error(
        self,
        *,
        stage: str,
        archive_path: Path,
        processed_records: int,
        limit: int | None,
        exc: SQLAlchemyError,
    ) -> SeedLoadError:
        return SeedLoadError(
            category="db",
            stage=stage,
            message=self._format_db_error(exc),
            status_code=status.HTTP_409_CONFLICT,
            archive_name=archive_path.name,
            processed_records=processed_records,
            limit_per_file=limit,
        )

    def _mark_ingestion_run_failed(self, ingestion_run_id: UUID, notes: str) -> None:
        failed_run = self.session.get(IngestionRunModel, ingestion_run_id)
        if failed_run is None:
            logger.error(
                "OpenAIRE seed failed to persist ingestion status ingestion_run_id=%s",
                ingestion_run_id,
            )
            return

        failed_run.status = "failed"
        failed_run.completed_at = datetime.now(UTC)
        failed_run.notes = notes
        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            logger.exception(
                "OpenAIRE seed failed to store failure metadata ingestion_run_id=%s",
                ingestion_run_id,
            )
