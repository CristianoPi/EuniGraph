from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib import error, parse, request
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
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
from eunigraph.modules.ingestion.application.eunice_seed_targets import (
    DEFAULT_EUNICE_TARGET_ORGANIZATIONS,
    EUNICETargetOrganizationSpec,
)
from eunigraph.modules.ingestion.application.openaire_beginners_kit import (
    OpenAireBeginnersKitSeeder,
    SeedLoadError,
)
from eunigraph.modules.ingestion.infrastructure.models import (
    DataSourceModel,
    IngestionRunModel,
    SourceRecordModel,
)
from eunigraph.shared.utils import normalize_text

logger = logging.getLogger(__name__)

OPENAIRE_GRAPH_EUNICE_SOURCE_NAME = "OpenAIRE Graph EUNICE Seed"
OPENAIRE_GRAPH_EUNICE_SOURCE_TYPE = "openaire_graph_eunice"


@dataclass(frozen=True, slots=True)
class ResolvedTargetOrganization:
    spec: EUNICETargetOrganizationSpec
    api_payload: dict[str, Any]
    openaire_id: str


@dataclass(frozen=True, slots=True)
class EUNICESeedStatus:
    api_base_url: str
    configured_targets: list[dict[str, Any]]
    table_counts: dict[str, int]
    latest_ingestion_run_id: str | None
    latest_ingestion_status: str | None


class OpenAireGraphApiClient:
    def __init__(self, *, base_url: str, timeout_seconds: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._active_base_url = self._base_url

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def active_base_url(self) -> str:
        return self._active_base_url

    def search_organizations(
        self,
        *,
        page_size: int,
        **params: str,
    ) -> list[dict[str, Any]]:
        payload = self._get_json("/v1/organizations", {"pageSize": str(page_size), **params})
        return self._extract_results(payload, path="/v1/organizations")

    def iter_research_products(
        self,
        *,
        max_results: int | None,
        page_size: int,
        **params: str,
    ) -> list[dict[str, Any]]:
        page = 1
        yielded = 0
        results: list[dict[str, Any]] = []
        effective_page_size = max(1, min(page_size, 100))

        while True:
            remaining = None if max_results is None else max_results - yielded
            if remaining is not None and remaining <= 0:
                return results

            current_page_size = (
                min(effective_page_size, remaining)
                if remaining is not None
                else effective_page_size
            )
            payload = self._get_json(
                "/v2/researchProducts",
                {
                    "page": str(page),
                    "pageSize": str(current_page_size),
                    **params,
                },
            )
            page_results = self._extract_results(payload, path="/v2/researchProducts")
            if not page_results:
                return results

            results.extend(page_results)
            yielded += len(page_results)

            header = payload.get("header") if isinstance(payload, dict) else None
            total_found = self._extract_positive_int(header, "numFound")
            page_size_value = self._extract_positive_int(header, "pageSize") or current_page_size
            current_page = self._extract_positive_int(header, "page") or page
            if total_found is not None and current_page * page_size_value >= total_found:
                return results
            if len(page_results) < current_page_size:
                return results

            page += 1

    def _get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        query = parse.urlencode({key: value for key, value in params.items() if value})
        last_http_error: error.HTTPError | None = None
        last_request_error: Exception | None = None

        for base_url in self._candidate_base_urls():
            endpoint = f"{base_url}{path}"
            if query:
                endpoint = f"{endpoint}?{query}"
            http_request = request.Request(
                endpoint,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "EuniGraph/0.1 (admin seed)",
                },
                method="GET",
            )
            try:
                with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict):
                    raise SeedLoadError(
                        category="integration",
                        stage="OpenAIRE Graph API response parsing",
                        message=f"Unexpected payload type from {endpoint}",
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                self._active_base_url = base_url
                return payload
            except error.HTTPError as exc:
                last_http_error = exc
                if exc.code in {404, 405}:
                    logger.warning(
                        "OpenAIRE Graph API base URL rejected request status=%s endpoint=%s; "
                        "trying fallback if available",
                        exc.code,
                        endpoint,
                    )
                    continue
                raise SeedLoadError(
                    category="integration",
                    stage="OpenAIRE Graph API request",
                    message=f"{exc.code} while requesting {endpoint}",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                ) from exc
            except (error.URLError, TimeoutError, ValueError) as exc:
                last_request_error = exc
                continue

        if last_http_error is not None:
            raise SeedLoadError(
                category="integration",
                stage="OpenAIRE Graph API request",
                message=(
                    f"{last_http_error.code} while requesting OpenAIRE Graph API "
                    f"across configured base URL fallbacks"
                ),
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from last_http_error
        raise SeedLoadError(
            category="integration",
            stage="OpenAIRE Graph API request",
            message=f"Unable to reach OpenAIRE Graph API: {last_request_error}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from last_request_error

    def _candidate_base_urls(self) -> list[str]:
        companion = None
        if "api-beta.openaire.eu/graph" in self._base_url:
            companion = self._base_url.replace(
                "api-beta.openaire.eu/graph",
                "api.openaire.eu/graph",
            )
        elif "api.openaire.eu/graph" in self._base_url:
            companion = self._base_url.replace(
                "api.openaire.eu/graph",
                "api-beta.openaire.eu/graph",
            )

        candidates = [self._base_url]
        if companion and companion not in candidates:
            candidates.append(companion)
        return candidates

    def _extract_results(
        self,
        payload: dict[str, Any],
        *,
        path: str,
    ) -> list[dict[str, Any]]:
        results = payload.get("results")
        if not isinstance(results, list):
            raise SeedLoadError(
                category="integration",
                stage="OpenAIRE Graph API response parsing",
                message=f"Missing `results` array in response from {path}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return [item for item in results if isinstance(item, dict)]

    def _extract_positive_int(self, payload: Any, field_name: str) -> int | None:
        if not isinstance(payload, dict):
            return None
        value = payload.get(field_name)
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None


class OpenAireGraphEuniceSeeder(OpenAireBeginnersKitSeeder):
    def __init__(self, session: Session, settings: Settings) -> None:
        super().__init__(session, settings)
        self._api = OpenAireGraphApiClient(
            base_url=settings.openaire_graph_api_base_url,
            timeout_seconds=settings.openaire_graph_api_timeout_seconds,
        )
        self._target_orgs_by_publication: dict[UUID, set[UUID]] = {}

    def get_status(self) -> EUNICESeedStatus:  # type: ignore[override]
        latest_run = self.session.scalar(
            select(IngestionRunModel)
            .join(DataSourceModel, IngestionRunModel.data_source_id == DataSourceModel.id)
            .where(DataSourceModel.source_type == OPENAIRE_GRAPH_EUNICE_SOURCE_TYPE)
            .order_by(IngestionRunModel.started_at.desc())
            .limit(1)
        )
        return EUNICESeedStatus(
            api_base_url=self._api.base_url,
            configured_targets=[
                {
                    "key": spec.key,
                    "display_name": spec.display_name,
                    "aliases": list(spec.aliases),
                    "country_code": spec.country_code,
                }
                for spec in DEFAULT_EUNICE_TARGET_ORGANIZATIONS
            ],
            table_counts=self._snapshot_table_counts(),
            latest_ingestion_run_id=str(latest_run.id) if latest_run else None,
            latest_ingestion_status=latest_run.status if latest_run else None,
        )

    def load(
        self,
        *,
        limit_per_file: int | None = None,
        target_organization_keys: list[str] | None = None,
        max_publications_per_organization: int | None = None,
        publication_year_from: int | None = None,
        publication_year_to: int | None = None,
    ) -> dict[str, int | str | None]:
        target_specs = self._resolve_target_specs(target_organization_keys)
        if not target_specs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one EUNICE target organization must be configured.",
            )

        if max_publications_per_organization is None and limit_per_file is not None:
            max_publications_per_organization = limit_per_file
        max_results = (
            max_publications_per_organization
            if max_publications_per_organization is not None
            else self.settings.openaire_eunice_seed_max_publications_per_organization
        )
        before_counts = self._snapshot_table_counts()
        data_source = self._get_or_create_logical_source()
        logger.info(
            "OpenAIRE Graph EUNICE seed started api_base_url=%s target_count=%s "
            "max_publications_per_organization=%s publication_year_from=%s publication_year_to=%s",
            self._api.base_url,
            len(target_specs),
            max_results,
            publication_year_from,
            publication_year_to,
        )

        ingestion_run = IngestionRunModel(
            data_source_id=data_source.id,
            status="running",
            triggered_by="admin-api",
            raw_config={
                "target_organization_keys": [spec.key for spec in target_specs],
                "max_publications_per_organization": max_results,
                "publication_year_from": publication_year_from,
                "publication_year_to": publication_year_to,
            },
        )
        self.session.add(ingestion_run)
        self.session.flush()
        self.session.commit()

        processed_publication_ids: set[UUID] = set()
        ambiguous_publications = 0
        try:
            resolved_targets = self._resolve_target_organizations(target_specs)
            for resolved_target in resolved_targets:
                self._process_target_organization(
                    resolved_target,
                    data_source_id=data_source.id,
                    ingestion_run_id=ingestion_run.id,
                    max_publications_per_organization=max_results,
                    publication_year_from=publication_year_from,
                    publication_year_to=publication_year_to,
                    processed_publication_ids=processed_publication_ids,
                )

            ambiguous_publications = self._materialize_target_affiliations()
            ingestion_run.status = "completed"
            ingestion_run.completed_at = datetime.now(UTC)
            self.session.commit()
        except SeedLoadError as exc:
            self.session.rollback()
            logger.warning(
                "OpenAIRE Graph EUNICE seed failed ingestion_run_id=%s detail=%s",
                ingestion_run.id,
                exc.detail(),
                exc_info=True,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, exc.detail())
            raise exc.to_http_exception() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            seed_error = SeedLoadError(
                category="db",
                stage="EUNICE seed persistence",
                message=self._format_db_error(exc),
                status_code=status.HTTP_409_CONFLICT,
            )
            logger.exception(
                "OpenAIRE Graph EUNICE seed database failure ingestion_run_id=%s",
                ingestion_run.id,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, seed_error.detail())
            raise seed_error.to_http_exception() from exc
        except Exception as exc:  # pragma: no cover - defensive path
            self.session.rollback()
            seed_error = SeedLoadError(
                category="integration",
                stage="EUNICE seed execution",
                message=str(exc) or exc.__class__.__name__,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            logger.exception(
                "OpenAIRE Graph EUNICE seed unexpected failure ingestion_run_id=%s",
                ingestion_run.id,
            )
            self._mark_ingestion_run_failed(ingestion_run.id, seed_error.detail())
            raise seed_error.to_http_exception() from exc

        after_counts = self._snapshot_table_counts()
        data_source.base_url = self._api.active_base_url
        self.session.commit()
        return {
            "api_base_url": self._api.active_base_url,
            "ingestion_run_id": str(ingestion_run.id),
            "target_organizations_requested": len(target_specs),
            "resolved_target_organizations": len(resolved_targets),
            "max_publications_per_organization": max_results,
            "publication_records_processed": len(processed_publication_ids),
            "new_organizations": after_counts["organization"] - before_counts["organization"],
            "new_researchers": after_counts["researcher"] - before_counts["researcher"],
            "new_publications": after_counts["publication"] - before_counts["publication"],
            "new_publication_organization_relations": (
                after_counts["publication_organization"]
                - before_counts["publication_organization"]
            ),
            "new_researcher_affiliations": (
                after_counts["researcher_affiliation"]
                - before_counts["researcher_affiliation"]
            ),
            "ambiguous_publications": ambiguous_publications,
        }

    def _resolve_target_specs(
        self,
        requested_keys: list[str] | None,
    ) -> list[EUNICETargetOrganizationSpec]:
        available = {
            spec.key: spec
            for spec in DEFAULT_EUNICE_TARGET_ORGANIZATIONS
        }
        if not requested_keys:
            return list(available.values())

        invalid_keys = sorted({key for key in requested_keys if key not in available})
        if invalid_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Unknown EUNICE target organization keys: "
                    f"{', '.join(invalid_keys)}"
                ),
            )
        return [available[key] for key in requested_keys]

    def _resolve_target_organizations(
        self,
        target_specs: list[EUNICETargetOrganizationSpec],
    ) -> list[ResolvedTargetOrganization]:
        resolved_targets: list[ResolvedTargetOrganization] = []
        unresolved_keys: list[str] = []

        for spec in target_specs:
            resolved = self._resolve_single_target_organization(spec)
            if resolved is None:
                unresolved_keys.append(spec.key)
                continue
            resolved_targets.append(resolved)

        if unresolved_keys:
            raise SeedLoadError(
                category="configuration",
                stage="target organization resolution",
                message=(
                    "Unable to resolve OpenAIRE organizations for target key(s): "
                    f"{', '.join(unresolved_keys)}"
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return resolved_targets

    def _resolve_single_target_organization(
        self,
        spec: EUNICETargetOrganizationSpec,
    ) -> ResolvedTargetOrganization | None:
        candidates: dict[str, dict[str, Any]] = {}

        for alias in spec.aliases:
            for field_name in ("legalName", "legalShortName", "search"):
                params: dict[str, str] = {field_name: alias}
                if spec.country_code:
                    params["countryCode"] = spec.country_code
                for payload in self._api.search_organizations(page_size=10, **params):
                    openaire_id = self._extract_target_openaire_id(payload)
                    if openaire_id:
                        candidates[openaire_id] = payload

        best_payload: dict[str, Any] | None = None
        best_score = -1
        for payload in candidates.values():
            score = self._score_target_candidate(spec, payload)
            if score > best_score:
                best_score = score
                best_payload = payload

        if best_payload is None or best_score < 100:
            logger.warning(
                "OpenAIRE Graph EUNICE seed could not confidently resolve target=%s score=%s",
                spec.key,
                best_score,
            )
            return None

        openaire_id = self._extract_target_openaire_id(best_payload)
        if openaire_id is None:
            return None
        return ResolvedTargetOrganization(
            spec=spec,
            api_payload=best_payload,
            openaire_id=openaire_id,
        )

    def _process_target_organization(
        self,
        resolved_target: ResolvedTargetOrganization,
        *,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        max_publications_per_organization: int | None,
        publication_year_from: int | None,
        publication_year_to: int | None,
        processed_publication_ids: set[UUID],
    ) -> None:
        logger.info(
            "OpenAIRE Graph EUNICE seed processing target=%s openaire_id=%s",
            resolved_target.spec.key,
            resolved_target.openaire_id,
        )
        organization_record = self._create_source_record(
            data_source_id=data_source_id,
            ingestion_run_id=ingestion_run_id,
            entity_type="organization",
            source_identifier=resolved_target.openaire_id,
            payload=resolved_target.api_payload,
        )
        del organization_record

        organization = self._upsert_organization(
            self._to_legacy_organization_payload(resolved_target.api_payload),
        )
        if organization.openaire_id is None:
            organization.openaire_id = resolved_target.openaire_id
            self.session.flush()
            self._register_organization_cache(organization)

        publication_payloads = self._api.iter_research_products(
            max_results=max_publications_per_organization,
            page_size=self.settings.openaire_graph_api_page_size,
            relOrganizationId=resolved_target.openaire_id,
            type="publication",
            sortBy="publicationDate DESC",
            fromPublicationDate=str(publication_year_from) if publication_year_from else "",
            toPublicationDate=str(publication_year_to) if publication_year_to else "",
        )

        for publication_payload in publication_payloads:
            transformed_publication = self._to_legacy_publication_payload(publication_payload)
            source_identifier = self._payload_identifier(transformed_publication)
            source_record = self._create_source_record(
                data_source_id=data_source_id,
                ingestion_run_id=ingestion_run_id,
                entity_type="publication",
                source_identifier=source_identifier,
                payload=publication_payload,
            )
            publication = self._upsert_publication(
                transformed_publication,
                source_record.id,
            )
            self._upsert_publication_authors(
                publication,
                transformed_publication,
                source_record.id,
            )
            self._upsert_publication_identifiers(
                publication,
                transformed_publication,
                source_record.id,
            )
            self._map_target_publication_organization_relation(
                publication=publication,
                organization=organization,
                source_record_id=source_record.id,
            )
            self._target_orgs_by_publication.setdefault(publication.id, set()).add(organization.id)
            processed_publication_ids.add(publication.id)

    def _materialize_target_affiliations(self) -> int:
        ambiguous_publications = 0

        for publication_id, organization_ids in self._target_orgs_by_publication.items():
            if len(organization_ids) != 1:
                ambiguous_publications += 1
                continue

            publication = self.session.get(PublicationModel, publication_id)
            if publication is None or publication.canonical_source_record_id is None:
                continue

            organization_id = next(iter(organization_ids))
            authors = list(
                self.session.scalars(
                    select(PublicationAuthorModel).where(
                        PublicationAuthorModel.publication_id == publication_id,
                    )
                )
            )
            for author in authors:
                self._upsert_researcher_affiliation(
                    researcher_id=author.researcher_id,
                    organization_id=organization_id,
                    source_record_id=publication.canonical_source_record_id,
                )

        return ambiguous_publications

    def _map_target_publication_organization_relation(
        self,
        *,
        publication: PublicationModel,
        organization: Any,
        source_record_id: UUID,
    ) -> None:
        if not publication.openaire_id or not organization.openaire_id:
            return
        self._map_publication_organization_relation(
            {
                "source": publication.openaire_id,
                "sourceType": "result",
                "target": organization.openaire_id,
                "targetType": "organization",
                "reltype": {"name": "affiliation", "type": "affiliation"},
            },
            source_record_id,
        )

    def _score_target_candidate(
        self,
        spec: EUNICETargetOrganizationSpec,
        payload: dict[str, Any],
    ) -> int:
        aliases = {normalize_text(alias) for alias in spec.aliases}
        legal_name = self._coalesce(payload.get("legalName"), payload.get("legalname")) or ""
        short_name = (
            self._coalesce(payload.get("legalShortName"), payload.get("legalshortname"))
            or ""
        )
        alternative_names = payload.get("alternativeNames")
        if not isinstance(alternative_names, list):
            alternative_names = []
        candidate_names = {
            name
            for name in (
                normalize_text(legal_name),
                normalize_text(short_name),
                *[
                    normalize_text(item)
                    for item in alternative_names
                    if isinstance(item, str) and item.strip()
                ],
            )
            if name
        }
        score = 0
        for alias in aliases:
            if alias in candidate_names:
                score = max(score, 120)
            elif any(alias in candidate or candidate in alias for candidate in candidate_names):
                score = max(score, 100)

        country_code = self._extract_country_code(payload)
        if spec.country_code and country_code == spec.country_code:
            score += 10
        elif spec.country_code and country_code and country_code != spec.country_code:
            score -= 20
        return score

    def _extract_target_openaire_id(self, payload: dict[str, Any]) -> str | None:
        identifier = payload.get("id")
        if isinstance(identifier, str) and identifier.strip():
            return identifier.strip()
        return None

    def _to_legacy_organization_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": payload.get("id"),
            "legalname": payload.get("legalName") or payload.get("legalname"),
            "legalshortname": payload.get("legalShortName") or payload.get("legalshortname"),
            "websiteurl": payload.get("websiteUrl") or payload.get("websiteurl"),
            "country": payload.get("country"),
            "city": payload.get("city"),
            "pid": payload.get("pids") or payload.get("pid") or [],
            "type": payload.get("type") or "organization",
        }

    def _to_legacy_publication_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        authors = payload.get("authors") or payload.get("author") or []
        legacy_authors: list[dict[str, Any]] = []
        for author in authors:
            if not isinstance(author, dict):
                continue
            legacy_authors.append(
                {
                    "fullname": author.get("fullName") or author.get("fullname"),
                    "name": author.get("name"),
                    "surname": author.get("surname"),
                    "rank": author.get("rank"),
                    "pid": author.get("pid"),
                }
            )

        publication_date = self._sanitize_publication_date(
            payload.get("publicationDate") or payload.get("publicationdate"),
        )

        return {
            "id": payload.get("id"),
            "maintitle": payload.get("mainTitle") or payload.get("maintitle"),
            "description": payload.get("descriptions") or payload.get("description") or [],
            "publicationdate": publication_date,
            "pid": payload.get("pids") or payload.get("pid") or [],
            "originalId": payload.get("originalIds") or payload.get("originalId") or [],
            "author": legacy_authors,
            "bestaccessright": payload.get("bestAccessRight") or payload.get("bestaccessright"),
            "source": payload.get("sources") or payload.get("source") or [],
            "instance": payload.get("instances") or payload.get("instance") or [],
            "container": payload.get("container"),
            "publisher": payload.get("publisher"),
            "language": payload.get("language"),
            "type": payload.get("type"),
        }

    def _sanitize_publication_date(self, value: Any) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return None
        normalized = value.strip()
        year_text = normalized[:4]
        try:
            year = int(year_text)
        except ValueError:
            return None
        if year < 1000 or year > 3000:
            logger.info(
                "OpenAIRE Graph EUNICE seed skipped out-of-range publication date value=%s",
                normalized,
            )
            return None
        return normalized

    def _snapshot_table_counts(self) -> dict[str, int]:
        return {
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

    def _get_or_create_logical_source(self) -> DataSourceModel:
        source = self.session.scalar(
            select(DataSourceModel).where(DataSourceModel.name == OPENAIRE_GRAPH_EUNICE_SOURCE_NAME)
        )
        if source is None:
            source = DataSourceModel(
                name=OPENAIRE_GRAPH_EUNICE_SOURCE_NAME,
                source_type=OPENAIRE_GRAPH_EUNICE_SOURCE_TYPE,
                base_url=self._api.base_url,
                description=(
                    "Targeted EUNICE demo seed resolved live from the OpenAIRE Graph API."
                ),
                is_active=True,
            )
            self.session.add(source)
            self.session.flush()
        else:
            source.base_url = self._api.base_url
        return source
