from __future__ import annotations

from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from urllib import error, request
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    ExternalIdentifierModel,
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
    ResearcherAffiliationModel,
    ResearcherModel,
)
from eunigraph.modules.ingestion.application.openaire_beginners_kit import (
    OpenAireBeginnersKitSeeder,
    SeedLoadError,
)
from eunigraph.modules.ingestion.application.openaire_graph_eunice import (
    EUNICESeedStatus,
    OpenAireGraphApiClient,
    OpenAireGraphEuniceSeeder,
)
from eunigraph.modules.ingestion.infrastructure.models import (
    DataSourceModel,
    IngestionRunModel,
)
from eunigraph.persistence.postgres import models  # noqa: F401


class FakeSeedSession:
    def __init__(
        self,
        *,
        scalar_values: list[object | None] | None = None,
        existing_relations: list[PublicationAuthorModel] | None = None,
        scalars_values: list[list[object]] | None = None,
        get_values: dict[UUID, object] | None = None,
    ) -> None:
        self.scalar_values = list(scalar_values or [])
        self.existing_relations = list(existing_relations or [])
        self.scalars_values = list(scalars_values or [])
        self.added: list[object] = []
        self.commit_calls = 0
        self.rollback_calls = 0
        self.flush_calls = 0
        self.ingestion_runs: dict[UUID, IngestionRunModel] = {}
        self.records_by_id: dict[UUID, object] = {}
        self.get_values = dict(get_values or {})

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        self.flush_calls += 1
        for value in self.added:
            object_id = getattr(value, "id", None)
            if object_id is None:
                cast(Any, value).id = uuid4()
                object_id = cast(UUID, cast(Any, value).id)
            self.records_by_id[cast(UUID, object_id)] = value
            if isinstance(value, IngestionRunModel):
                self.ingestion_runs[value.id] = value

    def commit(self) -> None:
        self.commit_calls += 1
        self.flush()

    def rollback(self) -> None:
        self.rollback_calls += 1

    def scalar(self, _query: object) -> object | None:
        if not self.scalar_values:
            return None
        return self.scalar_values.pop(0)

    def scalars(self, _query: object) -> list[object]:
        if self.scalars_values:
            return list(self.scalars_values.pop(0))
        return list(self.existing_relations)

    def get(self, _model: type[object], key: UUID) -> object | None:
        if key in self.get_values:
            return self.get_values[key]
        if key in self.records_by_id:
            return self.records_by_id[key]
        return self.ingestion_runs.get(key)

    def expunge_all(self) -> None:
        return None


class FailingSeeder(OpenAireBeginnersKitSeeder):
    def _validate_dataset_path(self) -> Path:
        return Path("/tmp/openaire-beginners-kit")

    def _get_or_create_logical_source(self) -> DataSourceModel:
        return DataSourceModel(
            id=uuid4(),
            name="OpenAIRE Beginner's Kit",
            source_type="openaire_beginners_kit",
        )

    def _process_datasources(
        self,
        archive_path: Path,
        data_source_id: UUID,
        ingestion_run_id: UUID,
        limit: int | None,
    ) -> int:
        raise SeedLoadError(
            category="db",
            stage="publication persistence",
            message="duplicate key value violates unique constraint uq_publication_author_pair",
            status_code=status.HTTP_409_CONFLICT,
            archive_name="publication.tar",
            processed_records=151,
            limit_per_file=limit,
        )


def _settings() -> object:
    return SimpleNamespace(
        openaire_beginners_kit_path="data/openaire/beginners_kit",
        openaire_graph_api_base_url="https://api.openaire.eu/graph",
        openaire_graph_api_timeout_seconds=30,
        openaire_graph_api_page_size=100,
        openaire_eunice_seed_max_publications=250,
    )


def test_upsert_publication_authors_skips_duplicate_researcher_links_and_reassigns_rank() -> None:
    publication = PublicationModel(id=uuid4(), title="Test", normalized_title="test")
    ada = ResearcherModel(
        id=uuid4(),
        full_name="Ada Lovelace",
        normalized_name="ada lovelace",
    )
    grace = ResearcherModel(
        id=uuid4(),
        full_name="Grace Hopper",
        normalized_name="grace hopper",
    )
    session = FakeSeedSession(scalar_values=[ada, grace])
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))

    seeder._upsert_publication_authors(
        publication,
        {
            "author": [
                {"fullname": "Ada Lovelace", "rank": "1"},
                {"fullname": "Ada Lovelace", "rank": "1"},
                {"fullname": "Grace Hopper", "rank": "1"},
            ]
        },
        uuid4(),
    )

    relations = [
        item for item in session.added if isinstance(item, PublicationAuthorModel)
    ]

    assert len(relations) == 2
    assert {relation.researcher_id for relation in relations} == {ada.id, grace.id}
    assert sorted(relation.author_position for relation in relations) == [1, 2]


def test_extract_language_code_prefers_short_code_over_long_label() -> None:
    session = FakeSeedSession()
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))

    extracted = seeder._extract_language_code({"code": "eng", "label": "English"})

    assert extracted == "eng"
    assert (
        seeder._extract_language_code(
            {"label": "Greek, Modern (1453-)"}
        )
        is None
    )


def test_clip_text_truncates_overlong_descriptive_fields() -> None:
    session = FakeSeedSession()
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))

    clipped = seeder._clip_text("x" * 130, max_length=120, field_name="researcher.given_name")

    assert clipped == "x" * 120


def test_create_source_record_reuses_duplicate_identifier_within_same_run() -> None:
    session = FakeSeedSession()
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))
    ingestion_run_id = uuid4()
    data_source_id = uuid4()

    first = seeder._create_source_record(
        data_source_id=data_source_id,
        ingestion_run_id=ingestion_run_id,
        entity_type="datasource",
        source_identifier="re3data_____::duplicate",
        payload={"id": "re3data_____::duplicate", "name": "first"},
    )
    second = seeder._create_source_record(
        data_source_id=data_source_id,
        ingestion_run_id=ingestion_run_id,
        entity_type="datasource",
        source_identifier="re3data_____::duplicate",
        payload={"id": "re3data_____::duplicate", "name": "first"},
    )

    assert first is second
    assert len([item for item in session.added if item is first]) == 1


def test_upsert_publication_identifiers_skips_conflicting_duplicates_within_same_run() -> None:
    session = FakeSeedSession()
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))
    first_publication = PublicationModel(id=uuid4(), title="First", normalized_title="first")
    second_publication = PublicationModel(id=uuid4(), title="Second", normalized_title="second")

    seeder._upsert_publication_identifiers(
        first_publication,
        {"pid": [{"scheme": "pmc", "value": "PMC8917921"}]},
        uuid4(),
    )
    seeder._upsert_publication_identifiers(
        second_publication,
        {"pid": [{"scheme": "pmc", "value": "PMC8917921"}]},
        uuid4(),
    )

    identifiers = [
        item for item in session.added if isinstance(item, ExternalIdentifierModel)
    ]

    assert len(identifiers) == 1
    assert identifiers[0].entity_id == first_publication.id
    assert identifiers[0].identifier_type == "pmc"
    assert identifiers[0].identifier_value == "PMC8917921"


def test_assign_unique_entity_value_skips_conflict_for_unflushed_entities() -> None:
    session = FakeSeedSession()
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))
    first_publication = PublicationModel(title="First", normalized_title="first")
    second_publication = PublicationModel(title="Second", normalized_title="second")

    first_doi = seeder._assign_unique_entity_value(
        model=first_publication,
        value="10.1000/example",
        current_value=first_publication.doi,
        field_name="publication.doi",
        cache=seeder._publication_by_doi,
        model_class=PublicationModel,
        model_field="doi",
    )
    second_doi = seeder._assign_unique_entity_value(
        model=second_publication,
        value="10.1000/example",
        current_value=second_publication.doi,
        field_name="publication.doi",
        cache=seeder._publication_by_doi,
        model_class=PublicationModel,
        model_field="doi",
    )

    assert first_doi == "10.1000/example"
    assert second_doi is None


def test_map_researcher_affiliation_relation_derives_solo_author_affiliation() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="Solo paper",
        normalized_title="solo paper",
        openaire_id="pub-1",
    )
    organization = OrganizationModel(
        id=uuid4(),
        name="Uni",
        normalized_name="uni",
        openaire_id="org-1",
    )
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Ada Lovelace",
        normalized_name="ada lovelace",
    )
    author = PublicationAuthorModel(
        publication_id=publication.id,
        researcher_id=researcher.id,
        author_position=1,
        researcher=researcher,
    )
    session = FakeSeedSession(
        scalars_values=[[author], []],
        get_values={researcher.id: researcher},
    )
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))
    seeder._publication_by_openaire_id[publication.openaire_id or ""] = publication
    seeder._organization_by_openaire_id[organization.openaire_id or ""] = organization

    seeder._map_researcher_affiliation_relation(
        {
            "reltype": {"name": "hasAuthorInstitution", "type": "affiliation"},
            "source": "pub-1",
            "sourceType": "result",
            "target": "org-1",
            "targetType": "organization",
        },
        uuid4(),
    )

    affiliations = [
        item for item in session.added if isinstance(item, ResearcherAffiliationModel)
    ]

    assert len(affiliations) == 1
    assert affiliations[0].researcher_id == researcher.id
    assert affiliations[0].organization_id == organization.id
    assert affiliations[0].is_primary is True
    assert researcher.primary_organization_id == organization.id


def test_map_researcher_affiliation_relation_skips_ambiguous_multi_author_publication() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="Team paper",
        normalized_title="team paper",
        openaire_id="pub-2",
    )
    organization = OrganizationModel(
        id=uuid4(),
        name="Uni",
        normalized_name="uni",
        openaire_id="org-2",
    )
    author_a = PublicationAuthorModel(
        publication_id=publication.id,
        researcher_id=uuid4(),
        author_position=1,
    )
    author_b = PublicationAuthorModel(
        publication_id=publication.id,
        researcher_id=uuid4(),
        author_position=2,
    )
    session = FakeSeedSession(scalars_values=[[author_a, author_b]])
    seeder = OpenAireBeginnersKitSeeder(cast(Session, session), cast(Any, _settings()))
    seeder._publication_by_openaire_id[publication.openaire_id or ""] = publication
    seeder._organization_by_openaire_id[organization.openaire_id or ""] = organization

    seeder._map_researcher_affiliation_relation(
        {
            "reltype": {"name": "hasAuthorInstitution", "type": "affiliation"},
            "source": "pub-2",
            "sourceType": "result",
            "target": "org-2",
            "targetType": "organization",
        },
        uuid4(),
    )

    assert not [
        item for item in session.added if isinstance(item, ResearcherAffiliationModel)
    ]
    assert all(
        not isinstance(item, PublicationOrganizationModel)
        for item in session.added
    )


def test_eunice_seed_status_exposes_community_configuration() -> None:
    session = FakeSeedSession()
    seeder = OpenAireGraphEuniceSeeder(cast(Session, session), cast(Any, _settings()))

    status_payload = seeder.get_status()

    assert isinstance(status_payload, EUNICESeedStatus)
    assert status_payload.api_base_url == "https://api.openaire.eu/graph"
    assert status_payload.community_id == "eunice"
    assert status_payload.product_type == "publication"
    assert status_payload.publication_date_from == "2026-01-01"
    assert status_payload.publication_date_to == "2026-12-31"
    assert status_payload.pagination_mode == "cursor"
    assert status_payload.page_size == 100
    assert status_payload.default_max_publications == 250


def test_graph_api_client_falls_back_from_beta_to_production_on_405(monkeypatch: Any) -> None:
    client = OpenAireGraphApiClient(
        base_url="https://api-beta.openaire.eu/graph",
        timeout_seconds=10,
    )

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        def read(self) -> bytes:
            return (
                b'{"header":{"numFound":1,"page":1,"pageSize":1},'
                b'"results":[{"id":"openorgs::1"}]}'
            )

    def fake_urlopen(req: Any, timeout: int) -> _Response:
        if "api-beta.openaire.eu/graph" in req.full_url:
            raise error.HTTPError(
                req.full_url,
                405,
                "Method Not Allowed",
                hdrs=Message(),
                fp=None,
            )
        return _Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    payload = client.search_organizations(page_size=1, legalName="Universita di Catania")

    assert payload == [{"id": "openorgs::1"}]
    assert client.active_base_url == "https://api.openaire.eu/graph"


def test_graph_api_client_iterates_research_products_with_cursor(monkeypatch: Any) -> None:
    client = OpenAireGraphApiClient(
        base_url="https://api.openaire.eu/graph",
        timeout_seconds=10,
    )

    responses = {
        "cursor=%2A": (
            b'{"header":{"numFound":3,"pageSize":2,"nextCursor":"cursor-2"},'
            b'"results":[{"id":"pub-1"},{"id":"pub-2"}]}'
        ),
        "cursor=cursor-2": (
            b'{"header":{"numFound":3,"pageSize":1},"results":[{"id":"pub-3"}]}'
        ),
    }

    class _Response:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def __enter__(self) -> _Response:
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        def read(self) -> bytes:
            return self._payload

    def fake_urlopen(req: Any, timeout: int) -> _Response:
        for marker, payload in responses.items():
            if marker in req.full_url:
                return _Response(payload)
        raise AssertionError(f"Unexpected URL {req.full_url}")

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    pages = list(
        client.iter_research_product_pages(
            max_results=None,
            page_size=2,
            relCommunityId="eunice",
            type="publication",
            fromPublicationDate="2026-01-01",
            toPublicationDate="2026-12-31",
        )
    )

    assert [[item["id"] for item in page] for page in pages] == [["pub-1", "pub-2"], ["pub-3"]]


def test_extract_publication_organizations_deduplicates_eunice_variants() -> None:
    session = FakeSeedSession()
    seeder = OpenAireGraphEuniceSeeder(cast(Session, session), cast(Any, _settings()))

    organizations = seeder._extract_publication_organization_payloads(
        {
            "organizations": [
                {
                    "legalName": "Universidad de Cantabria",
                    "acronym": "Universidad de Cantabria",
                    "id": "pending_org_::one",
                    "pids": None,
                },
                {
                    "legalName": "University of Cantabria",
                    "acronym": "UC",
                    "id": "openorgs____::cantabria",
                    "pids": [{"scheme": "ROR", "value": "https://ror.org/046ffzj20"}],
                },
                {
                    "legalName": "University of Cantabria",
                    "acronym": "University of Cantabria",
                    "id": "pending_org_::two",
                    "pids": None,
                },
            ]
        }
    )

    assert len(organizations) == 1
    assert organizations[0]["id"] == "openorgs____::cantabria"


def test_materialize_candidate_affiliations_links_all_authors_when_single_org() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="Seeded publication",
        normalized_title="seeded publication",
        canonical_source_record_id=uuid4(),
    )
    author_a = PublicationAuthorModel(
        publication_id=publication.id,
        researcher_id=uuid4(),
        author_position=1,
    )
    author_b = PublicationAuthorModel(
        publication_id=publication.id,
        researcher_id=uuid4(),
        author_position=2,
    )
    session = FakeSeedSession(
        scalars_values=[[author_a, author_b], [], [], []],
    )
    seeder = OpenAireGraphEuniceSeeder(cast(Session, session), cast(Any, _settings()))
    organization_id = uuid4()

    ambiguous = seeder._materialize_candidate_affiliations_for_publication(
        publication=publication,
        organization_ids={organization_id},
    )

    affiliations = [
        item for item in session.added if isinstance(item, ResearcherAffiliationModel)
    ]
    assert ambiguous is False
    assert len(affiliations) == 2
    assert {affiliation.organization_id for affiliation in affiliations} == {organization_id}


def test_materialize_candidate_affiliations_skips_multi_org_publications() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="Collaborative publication",
        normalized_title="collaborative publication",
        canonical_source_record_id=uuid4(),
    )
    session = FakeSeedSession()
    seeder = OpenAireGraphEuniceSeeder(cast(Session, session), cast(Any, _settings()))

    ambiguous = seeder._materialize_candidate_affiliations_for_publication(
        publication=publication,
        organization_ids={uuid4(), uuid4()},
    )

    assert ambiguous is True
    assert not [
        item for item in session.added if isinstance(item, ResearcherAffiliationModel)
    ]


def test_eunice_publication_date_sanitization_skips_placeholder_years() -> None:
    session = FakeSeedSession()
    seeder = OpenAireGraphEuniceSeeder(cast(Session, session), cast(Any, _settings()))

    assert seeder._sanitize_publication_date("9999-01-01") is None
    assert seeder._sanitize_publication_date("2024-05-10") == "2024-05-10"


def test_load_marks_failed_ingestion_run_and_returns_readable_error() -> None:
    session = FakeSeedSession()
    seeder = FailingSeeder(cast(Session, session), cast(Any, _settings()))

    try:
        seeder.load(limit_per_file=200)
    except HTTPException as exc:
        detail = exc.detail
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert "publication.tar" in detail
        assert "processed_records=151" in detail
        assert "limit_per_file=200" in detail
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected load() to raise HTTPException")

    ingestion_run = next(
        item for item in session.added if isinstance(item, IngestionRunModel)
    )
    assert ingestion_run.status == "failed"
    assert ingestion_run.completed_at is not None
    assert ingestion_run.notes is not None
    assert "uq_publication_author_pair" in ingestion_run.notes
    assert session.commit_calls >= 2
    assert session.rollback_calls == 1
