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
    ResearcherModel,
)
from eunigraph.modules.coauthorship.application import CoauthorshipGraphService


class FakeSession:
    def __init__(self, values: Sequence[object]) -> None:
        self._values = values

    def scalars(self, _query: object) -> list[object]:
        return list(self._values)


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
    assert edges[(str(researcher_a.id), str(researcher_b.id))]["weight"] == 2
    assert edges[(str(researcher_a.id), str(researcher_b.id))]["first_collaboration_year"] == 2020
    assert edges[(str(researcher_a.id), str(researcher_b.id))]["last_collaboration_year"] == 2022
    ac_key = tuple(sorted((str(researcher_a.id), str(researcher_c.id))))
    bc_key = tuple(sorted((str(researcher_b.id), str(researcher_c.id))))
    assert edges[ac_key]["weight"] == 1
    assert edges[bc_key]["weight"] == 1


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
