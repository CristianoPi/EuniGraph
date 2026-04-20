from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    ResearcherAffiliationModel,
    ResearcherModel,
)
from eunigraph.modules.coauthorship.application import CoauthorshipGraphService
from eunigraph.persistence.postgres import models  # noqa: F401


class FakeSession:
    def __init__(
        self,
        values: Sequence[object],
        *,
        affiliation_values: dict[UUID, Sequence[object]] | None = None,
        get_values: dict[UUID, object] | None = None,
    ) -> None:
        self._values = values
        self._affiliation_values = dict(affiliation_values or {})
        self._get_values = dict(get_values or {})

    def scalars(self, _query: object) -> list[object]:
        query_repr = str(_query)
        if "researcher_affiliation" in query_repr:
            if not self._affiliation_values:
                return []
            return list(next(iter(self._affiliation_values.values())))
        return list(self._values)

    def get(self, _model: object, key: UUID) -> object | None:
        return self._get_values.get(key)


def _settings() -> Any:
    return SimpleNamespace(coauthorship_graph_storage_path=Path("/tmp/eunigraph-test-graphs"))


def test_collect_graph_inputs_builds_weighted_edges_and_optional_isolated_nodes() -> None:
    org = OrganizationModel(id=uuid4(), name="Uni", normalized_name="uni")
    researcher_a = ResearcherModel(
        id=uuid4(),
        full_name="Ada Lovelace",
        normalized_name="ada lovelace",
        primary_organization=org,
    )
    researcher_b = ResearcherModel(
        id=uuid4(),
        full_name="Grace Hopper",
        normalized_name="grace hopper",
        primary_organization=org,
    )
    researcher_c = ResearcherModel(
        id=uuid4(),
        full_name="Alan Turing",
        normalized_name="alan turing",
    )
    researcher_d = ResearcherModel(
        id=uuid4(),
        full_name="Solo Author",
        normalized_name="solo author",
    )
    publication_one = PublicationModel(
        id=uuid4(),
        title="Paper One",
        normalized_title="paper one",
        publication_year=2020,
    )
    publication_two = PublicationModel(
        id=uuid4(),
        title="Paper Two",
        normalized_title="paper two",
        publication_date=date(2022, 5, 1),
    )
    publication_three = PublicationModel(
        id=uuid4(),
        title="Solo Paper",
        normalized_title="solo paper",
        publication_year=2024,
    )
    authorships = [
        PublicationAuthorModel(
            publication_id=publication_one.id,
            researcher_id=researcher_a.id,
            author_position=1,
            publication=publication_one,
            researcher=researcher_a,
        ),
        PublicationAuthorModel(
            publication_id=publication_one.id,
            researcher_id=researcher_b.id,
            author_position=2,
            publication=publication_one,
            researcher=researcher_b,
        ),
        PublicationAuthorModel(
            publication_id=publication_two.id,
            researcher_id=researcher_a.id,
            author_position=1,
            publication=publication_two,
            researcher=researcher_a,
        ),
        PublicationAuthorModel(
            publication_id=publication_two.id,
            researcher_id=researcher_b.id,
            author_position=2,
            publication=publication_two,
            researcher=researcher_b,
        ),
        PublicationAuthorModel(
            publication_id=publication_two.id,
            researcher_id=researcher_c.id,
            author_position=3,
            publication=publication_two,
            researcher=researcher_c,
        ),
        PublicationAuthorModel(
            publication_id=publication_three.id,
            researcher_id=researcher_d.id,
            author_position=1,
            publication=publication_three,
            researcher=researcher_d,
        ),
    ]
    service = CoauthorshipGraphService(cast(Session, FakeSession(authorships)), _settings())

    with_isolated_nodes, edges = service._collect_graph_inputs(include_isolated_nodes=True)
    without_isolated_nodes, _ = service._collect_graph_inputs(include_isolated_nodes=False)

    assert str(researcher_d.id) in with_isolated_nodes
    assert str(researcher_d.id) not in without_isolated_nodes
    ab_sorted = sorted((str(researcher_a.id), str(researcher_b.id)))
    ab_key = (ab_sorted[0], ab_sorted[1])
    assert edges[ab_key]["weight"] == 2
    assert edges[ab_key]["first_collaboration_year"] == 2020
    assert edges[ab_key]["last_collaboration_year"] == 2022
    ac_sorted = sorted((str(researcher_a.id), str(researcher_c.id)))
    bc_sorted = sorted((str(researcher_b.id), str(researcher_c.id)))
    ac_key = (ac_sorted[0], ac_sorted[1])
    bc_key = (bc_sorted[0], bc_sorted[1])
    assert edges[ac_key]["weight"] == 1
    assert edges[bc_key]["weight"] == 1
    assert with_isolated_nodes[str(researcher_a.id)]["university_code"] is None


def test_filter_subgraph_researcher_and_weight_limit() -> None:
    service = CoauthorshipGraphService(cast(Session, FakeSession([])), _settings())
    center_id = str(uuid4())
    neighbor_heavy_id = str(uuid4())
    neighbor_light_id = str(uuid4())
    payload = {
        "build_id": str(uuid4()),
        "graph_type": "coauthorship",
        "generated_at": "2026-04-13T10:00:00+00:00",
        "summary": {
            "node_count": 3,
            "edge_count": 2,
            "component_count": 1,
            "community_count": 1,
            "graph_version": "abc123",
        },
        "data_snapshot": {},
        "nodes": [
            {
                "id": center_id,
                "label": "Ada Lovelace",
                "full_name": "Ada Lovelace",
                "normalized_name": "ada lovelace",
                "primary_organization_id": None,
                "primary_organization_name": None,
                "degree": 2,
                "strength": 4,
                "betweenness": 1.0,
                "component_id": 0,
                "community_id": 0,
            },
            {
                "id": neighbor_heavy_id,
                "label": "Grace Hopper",
                "full_name": "Grace Hopper",
                "normalized_name": "grace hopper",
                "primary_organization_id": None,
                "primary_organization_name": None,
                "degree": 1,
                "strength": 3,
                "betweenness": 0.0,
                "component_id": 0,
                "community_id": 0,
            },
            {
                "id": neighbor_light_id,
                "label": "Alan Turing",
                "full_name": "Alan Turing",
                "normalized_name": "alan turing",
                "primary_organization_id": None,
                "primary_organization_name": None,
                "degree": 1,
                "strength": 1,
                "betweenness": 0.0,
                "component_id": 0,
                "community_id": 0,
            },
        ],
        "edges": [
            {
                "source": center_id,
                "target": neighbor_heavy_id,
                "weight": 3,
                "shared_publication_count": 3,
                "first_collaboration_year": 2020,
                "last_collaboration_year": 2024,
                "shared_publication_ids": ["p1", "p2", "p3"],
            },
            {
                "source": center_id,
                "target": neighbor_light_id,
                "weight": 1,
                "shared_publication_count": 1,
                "first_collaboration_year": 2022,
                "last_collaboration_year": 2022,
                "shared_publication_ids": ["p4"],
            },
        ],
    }

    subgraph = service._filter_subgraph(
        payload,
        researcher_id=UUID(center_id),
        organization_id=None,
        max_nodes=2,
        min_edge_weight=2,
        community_id=None,
    )

    assert subgraph["summary"]["node_count"] == 2
    assert subgraph["summary"]["edge_count"] == 1
    assert {node["id"] for node in subgraph["nodes"]} == {center_id, neighbor_heavy_id}


def test_compute_graph_version_is_stable_for_equivalent_inputs() -> None:
    service = CoauthorshipGraphService(cast(Session, FakeSession([])), _settings())
    node_a = {"id": "a", "primary_organization_id": None}
    node_b = {"id": "b", "primary_organization_id": "org-1"}
    edge = {
        "source": "a",
        "target": "b",
        "weight": 2,
        "first_collaboration_year": 2020,
        "last_collaboration_year": 2024,
    }

    version_one = service._compute_graph_version([node_a, node_b], [edge])
    version_two = service._compute_graph_version([node_b, node_a], [edge])

    assert version_one == version_two


def test_render_svg_outputs_placeholder_for_empty_graph() -> None:
    service = CoauthorshipGraphService(cast(Session, FakeSession([])), _settings())

    svg = service._render_svg([], [])

    assert "No coauthorship graph has been materialized yet" in svg
    assert svg.startswith("<svg")


def test_resolve_researcher_eunice_university_uses_primary_organization() -> None:
    organization = OrganizationModel(
        id=uuid4(),
        name="University of Catania",
        normalized_name="university of catania",
        country_code="IT",
    )
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Ada Lovelace",
        normalized_name="ada lovelace",
        primary_organization=organization,
    )
    service = CoauthorshipGraphService(cast(Session, FakeSession([])), _settings())

    university = service._resolve_researcher_eunice_university(researcher)

    assert university is not None
    assert university.code == "unict"


def test_resolve_researcher_eunice_university_uses_parent_organization_lineage() -> None:
    parent = OrganizationModel(
        id=uuid4(),
        name="Université de Mons",
        normalized_name="universite de mons",
        country_code="BE",
    )
    child = OrganizationModel(
        id=uuid4(),
        name="Faculty of Engineering, Université de Mons",
        normalized_name="faculty of engineering universite de mons",
        country_code="BE",
        parent_organization=parent,
        parent_organization_id=parent.id,
    )
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Grace Hopper",
        normalized_name="grace hopper",
        primary_organization=child,
    )
    service = CoauthorshipGraphService(cast(Session, FakeSession([])), _settings())

    university = service._resolve_researcher_eunice_university(researcher)

    assert university is not None
    assert university.code == "umons"


def test_resolve_researcher_eunice_university_skips_ambiguous_affiliations() -> None:
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Alan Turing",
        normalized_name="alan turing",
    )
    affiliation_one = ResearcherAffiliationModel(
        researcher_id=researcher.id,
        organization_id=uuid4(),
        organization=OrganizationModel(
            id=uuid4(),
            name="University of Vaasa",
            normalized_name="university of vaasa",
            country_code="FI",
        ),
        is_primary=False,
    )
    affiliation_two = ResearcherAffiliationModel(
        researcher_id=researcher.id,
        organization_id=uuid4(),
        organization=OrganizationModel(
            id=uuid4(),
            name="University of Catania",
            normalized_name="university of catania",
            country_code="IT",
        ),
        is_primary=False,
    )
    session = FakeSession(
        [],
        affiliation_values={researcher.id: [affiliation_one, affiliation_two]},
    )
    service = CoauthorshipGraphService(cast(Session, session), _settings())

    university = service._resolve_researcher_eunice_university(researcher)

    assert university is None


def test_render_svg_for_graph_uses_scatter_layout_without_labels() -> None:
    service = CoauthorshipGraphService(cast(Session, FakeSession([])), _settings())

    svg = service._render_svg(
        [
            {
                "id": "researcher-a",
                "label": "Ada Lovelace",
                "full_name": "Ada Lovelace",
                "normalized_name": "ada lovelace",
                "primary_organization_id": None,
                "primary_organization_name": None,
                "degree": 2,
                "strength": 3,
                "betweenness": 0.4,
                "component_id": 0,
                "community_id": 0,
            },
            {
                "id": "researcher-b",
                "label": "Grace Hopper",
                "full_name": "Grace Hopper",
                "normalized_name": "grace hopper",
                "primary_organization_id": None,
                "primary_organization_name": None,
                "degree": 1,
                "strength": 1,
                "betweenness": 0.0,
                "component_id": 0,
                "community_id": 0,
            },
        ],
        [
            {
                "source": "researcher-a",
                "target": "researcher-b",
                "weight": 1,
                "shared_publication_count": 1,
                "first_collaboration_year": 2024,
                "last_collaboration_year": 2024,
                "shared_publication_ids": ["publication-1"],
            },
        ],
    )

    assert "<text" not in svg
    assert 'r="2.70"' in svg
    assert 'r="2.10"' in svg
