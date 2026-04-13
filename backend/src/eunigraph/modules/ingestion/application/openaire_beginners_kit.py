from __future__ import annotations

import gzip
import hashlib
import json
import tarfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from eunigraph.core.config import Settings
from eunigraph.modules.catalog.infrastructure.models import (
    ExternalIdentifierModel,
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
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


@dataclass(slots=True)
class SeedStatus:
    dataset_path: str
    dataset_path_exists: bool
    required_files: dict[str, bool]
    table_counts: dict[str, int]
    latest_ingestion_run_id: str | None
    latest_ingestion_status: str | None


class OpenAireBeginnersKitSeeder:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

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

        ingestion_run = IngestionRunModel(
            data_source_id=data_source.id,
            status="running",
            triggered_by="admin-api",
            raw_config={"limit_per_file": limit_per_file},
        )
        self.session.add(ingestion_run)
        self.session.flush()

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
            self.session.commit()
        except Exception as exc:  # pragma: no cover - defensive rollback path
            self.session.rollback()
            failed_run = self.session.get(IngestionRunModel, ingestion_run.id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.notes = str(exc)
                self.session.commit()
            raise

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
        with tarfile.open(archive_path, mode="r") as archive:
            for member in archive:
                if not member.isfile() or not member.name.endswith(".gz"):
                    continue

                extracted = archive.extractfile(member)
                if extracted is None:
                    continue

                with gzip.open(extracted, mode="rt", encoding="utf-8") as handle:
                    for line in handle:
                        if limit is not None and yielded >= limit:
                            return
                        stripped = line.strip()
                        if not stripped:
                            continue
                        yielded += 1
                        yield json.loads(stripped)

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
        return record

    def _process_datasources(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
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
        return processed

    def _process_projects(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
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
        return processed

    def _process_organizations(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
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
        self.session.flush()
        return processed

    def _process_publications(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
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
        self.session.flush()
        return processed

    def _process_relations(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        processed = 0
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
            processed += 1
        self.session.flush()
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
            organization = self.session.scalar(
                select(OrganizationModel).where(OrganizationModel.openaire_id == openaire_id)
            )
        if organization is None and ror_id:
            organization = self.session.scalar(
                select(OrganizationModel).where(OrganizationModel.ror_id == ror_id),
            )
        if organization is None and normalized_name:
            organization = self.session.scalar(
                select(OrganizationModel).where(
                    OrganizationModel.normalized_name == normalized_name,
                ),
            )

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
                name=initial_name,
                normalized_name=normalized_name,
            )
            self.session.add(organization)

        resolved_name = self._coalesce(
            payload.get("legalshortname"),
            payload.get("legalname"),
            payload.get("officialname"),
            organization.name,
        )
        organization.name = resolved_name or organization.name
        organization.normalized_name = normalize_text(organization.name)
        organization.organization_type = (
            self._extract_value(payload.get("type")) or organization.organization_type
        )
        organization.country_code = self._extract_country_code(payload) or organization.country_code
        organization.city = payload.get("city") or organization.city
        organization.website = (
            self._extract_first(payload.get("websiteurl")) or organization.website
        )
        organization.ror_id = ror_id or organization.ror_id
        organization.openaire_id = openaire_id or organization.openaire_id
        self.session.flush()
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

        publication = None
        if openaire_id:
            publication = self.session.scalar(
                select(PublicationModel).where(PublicationModel.openaire_id == openaire_id)
            )
        if publication is None and doi:
            publication = self.session.scalar(
                select(PublicationModel).where(PublicationModel.doi == doi),
            )
        if publication is None:
            publication = self.session.scalar(
                select(PublicationModel).where(
                    PublicationModel.normalized_title == normalized_title,
                    PublicationModel.publication_year == self._extract_publication_year(payload),
                )
            )

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
        publication.publication_year = self._extract_publication_year(payload)
        publication.doi = doi or publication.doi
        publication.openaire_id = openaire_id or publication.openaire_id
        publication.publication_type = (
            self._extract_value(payload.get("type")) or publication.publication_type
        )
        publication.language_code = (
            self._extract_value(payload.get("language")) or publication.language_code
        )
        publication.journal_name = (
            self._extract_container_name(payload) or publication.journal_name
        )
        publication.venue_name = (
            self._extract_first(payload.get("source")) or publication.venue_name
        )
        publication.publisher = payload.get("publisher") or publication.publisher
        publication.open_access = self._extract_open_access(payload)
        publication.source_url = (
            self._extract_first_from_instances(payload, "url")
            or publication.source_url
        )
        publication.canonical_source_record_id = source_record_id
        self.session.flush()
        return publication

    def _upsert_publication_authors(
        self,
        publication: PublicationModel,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        for author_payload in payload.get("author") or []:
            full_name = self._coalesce(
                author_payload.get("fullname"),
                author_payload.get("fullName"),
            )
            if not full_name:
                continue

            orcid = self._extract_nested_pid_value(author_payload.get("pid"), "orcid")
            researcher = None
            if orcid:
                researcher = self.session.scalar(
                    select(ResearcherModel).where(ResearcherModel.orcid == orcid),
                )
            if researcher is None:
                normalized_author_name = normalize_text(full_name)
                researcher = self.session.scalar(
                    select(ResearcherModel).where(
                        ResearcherModel.normalized_name == normalized_author_name,
                    ),
                )

            if researcher is None:
                researcher = ResearcherModel(
                    full_name=full_name,
                    given_name=author_payload.get("name"),
                    family_name=author_payload.get("surname"),
                    normalized_name=normalize_text(full_name),
                    display_name=full_name,
                    orcid=orcid,
                )
                self.session.add(researcher)
                self.session.flush()

            relation = self.session.scalar(
                select(PublicationAuthorModel).where(
                    PublicationAuthorModel.publication_id == publication.id,
                    PublicationAuthorModel.researcher_id == researcher.id,
                )
            )
            if relation is None:
                relation = PublicationAuthorModel(
                    publication_id=publication.id,
                    researcher_id=researcher.id,
                    author_position=int(author_payload.get("rank") or 0),
                    author_list_name=full_name,
                    source_record_id=source_record_id,
                )
                self.session.add(relation)

    def _upsert_publication_identifiers(
        self,
        publication: PublicationModel,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        identifiers: list[tuple[str, str]] = []

        for pid in payload.get("pid") or []:
            identifier_type = (pid.get("scheme") or "").lower().strip()
            identifier_value = (pid.get("value") or "").strip()
            if identifier_type and identifier_value:
                identifiers.append((identifier_type, identifier_value))

        for original_id in payload.get("originalId") or []:
            if isinstance(original_id, str) and original_id.strip():
                identifiers.append(("original_id", original_id.strip()))

        for identifier_type, identifier_value in identifiers:
            existing = self.session.scalar(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "publication",
                    ExternalIdentifierModel.identifier_type == identifier_type,
                    ExternalIdentifierModel.identifier_value == identifier_value,
                )
            )
            if existing is None:
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

    def _map_publication_organization_relation(
        self,
        payload: dict[str, Any],
        source_record_id: UUID,
    ) -> None:
        source_id = payload.get("source")
        target_id = payload.get("target")
        if not isinstance(source_id, str) or not isinstance(target_id, str):
            return

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
            return

        organization = self.session.scalar(
            select(OrganizationModel).where(
                OrganizationModel.openaire_id == organization_identifier,
            )
        )
        publication = self.session.scalar(
            select(PublicationModel).where(
                PublicationModel.openaire_id == publication_identifier,
            )
        )
        if organization is None or publication is None:
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
