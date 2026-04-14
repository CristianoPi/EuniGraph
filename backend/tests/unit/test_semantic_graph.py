from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
    ResearcherModel,
)
from eunigraph.modules.embeddings.infrastructure.models import PublicationEmbeddingModel
from eunigraph.modules.semantic_graph.application import SemanticGraphService
from eunigraph.persistence.postgres import models  # noqa: F401


class FakeSession:
    def __init__(self, values: Sequence[object]) -> None:
        self._values = values

    def scalars(self, _query: object) -> list[object]:
        return list(self._values)


class FakeVectorStore:
    def __init__(self, results_by_point_id: dict[str, list[dict[str, Any]]]) -> None:
        self.results_by_point_id = results_by_point_id

    def get_collection_status(self, _collection_name: str) -> dict[str, Any]:
        return {"exists": True, "points_count": 3, "status": "green"}

    def get_collection_distance(self, _collection_name: str) -> str:
        return "Cosine"

    def query_similar_publications(
        self,
        *,
        collection_name: str,
        point_id: str,
        limit: int,
        score_threshold: float | None,
    ) -> list[dict[str, Any]]:
        del collection_name
        results = list(self.results_by_point_id.get(point_id, []))[:limit]
        if score_threshold is None:
            return results
        return [result for result in results if result["score"] >= score_threshold]


def _settings() -> Any:
    return SimpleNamespace(
        semantic_graph_storage_path=Path("/tmp/eunigraph-semantic-test-graphs"),
        embeddings_provider="gemini",
        embeddings_model="gemini-embedding-001",
        embeddings_version="v1",
        qdrant_collection_publications="publication_embeddings",
    )


def _publication(
    *,
    publication_id: UUID,
    title: str,
    point_id: str,
    publication_year: int,
    organization: OrganizationModel | None = None,
    author_name: str | None = None,
) -> PublicationModel:
    publication = PublicationModel(
        id=publication_id,
        title=title,
        normalized_title=title.lower(),
        publication_year=publication_year,
    )
    publication.embeddings = [
        PublicationEmbeddingModel(
            id=uuid4(),
            publication_id=publication_id,
            embedding_provider="gemini",
            qdrant_collection="publication_embeddings",
            qdrant_point_id=point_id,
            embedding_model="gemini-embedding-001",
            embedding_version="v1",
            content_hash=f"hash-{point_id}",
        ),
    ]
    if organization is not None:
        publication.organizations = [
            PublicationOrganizationModel(
                publication_id=publication_id,
                organization_id=organization.id,
                relation_type="affiliated_with",
                organization=organization,
            ),
        ]
    if author_name is not None:
        researcher = ResearcherModel(
            id=uuid4(),
            full_name=author_name,
            normalized_name=author_name.lower(),
        )
        publication.authors = [
            PublicationAuthorModel(
                publication_id=publication_id,
                researcher_id=researcher.id,
                author_position=1,
                researcher=researcher,
            ),
        ]
    return publication


def test_collect_graph_inputs_builds_union_edges_and_mutual_flags() -> None:
    org = OrganizationModel(id=uuid4(), name="Uni", normalized_name="uni")
    pub_a = _publication(
        publication_id=uuid4(),
        title="Paper A",
        point_id="point-a",
        publication_year=2022,
        organization=org,
        author_name="Ada Lovelace",
    )
    pub_b = _publication(
        publication_id=uuid4(),
        title="Paper B",
        point_id="point-b",
        publication_year=2023,
        organization=org,
        author_name="Grace Hopper",
    )
    pub_c = _publication(
        publication_id=uuid4(),
        title="Paper C",
        point_id="point-c",
        publication_year=2024,
        author_name="Alan Turing",
    )
    vector_store = FakeVectorStore(
        {
            "point-a": [
                {
                    "point_id": "point-a",
                    "score": 1.0,
                    "payload": {"publication_id": str(pub_a.id)},
                },
                {
                    "point_id": "point-b",
                    "score": 0.91,
                    "payload": {"publication_id": str(pub_b.id)},
                },
            ],
            "point-b": [
                {
                    "point_id": "point-a",
                    "score": 0.88,
                    "payload": {"publication_id": str(pub_a.id)},
                },
                {
                    "point_id": "point-c",
                    "score": 0.82,
                    "payload": {"publication_id": str(pub_c.id)},
                },
            ],
            "point-c": [
                {
                    "point_id": "point-b",
                    "score": 0.79,
                    "payload": {"publication_id": str(pub_b.id)},
                },
            ],
        },
    )
    service = SemanticGraphService(
        cast(Session, FakeSession([])),
        _settings(),
        vector_store=cast(Any, vector_store),
    )

    node_map, edge_map = service._collect_graph_inputs(
        publications=[pub_a, pub_b, pub_c],
        top_k=2,
        score_threshold=0.75,
        mutual_knn=False,
        edge_symmetry_policy="max_score_union",
        include_isolated_nodes=False,
    )

    ab_key = (
        str(pub_a.id) if str(pub_a.id) < str(pub_b.id) else str(pub_b.id),
        str(pub_b.id) if str(pub_a.id) < str(pub_b.id) else str(pub_a.id),
    )
    bc_key = (
        str(pub_b.id) if str(pub_b.id) < str(pub_c.id) else str(pub_c.id),
        str(pub_c.id) if str(pub_b.id) < str(pub_c.id) else str(pub_b.id),
    )
    assert set(node_map) == {str(pub_a.id), str(pub_b.id), str(pub_c.id)}
    assert edge_map[ab_key]["weight"] == 0.91
    assert edge_map[ab_key]["mutual_match"] is True
    assert edge_map[bc_key]["weight"] == 0.82
    assert edge_map[bc_key]["mutual_match"] is True
    assert node_map[str(pub_a.id)]["authors"] == ["Ada Lovelace"]
    assert node_map[str(pub_a.id)]["organization_names"] == ["Uni"]


def test_collect_graph_inputs_respects_mutual_knn_and_drops_one_way_edges() -> None:
    pub_a = _publication(
        publication_id=uuid4(),
        title="Paper A",
        point_id="point-a",
        publication_year=2022,
    )
    pub_b = _publication(
        publication_id=uuid4(),
        title="Paper B",
        point_id="point-b",
        publication_year=2023,
    )
    pub_c = _publication(
        publication_id=uuid4(),
        title="Paper C",
        point_id="point-c",
        publication_year=2024,
    )
    vector_store = FakeVectorStore(
        {
            "point-a": [
                {"point_id": "point-b", "score": 0.9, "payload": {"publication_id": str(pub_b.id)}},
            ],
            "point-b": [],
            "point-c": [],
        },
    )
    service = SemanticGraphService(
        cast(Session, FakeSession([])),
        _settings(),
        vector_store=cast(Any, vector_store),
    )

    node_map, edge_map = service._collect_graph_inputs(
        publications=[pub_a, pub_b, pub_c],
        top_k=2,
        score_threshold=0.7,
        mutual_knn=True,
        edge_symmetry_policy="max_score_union",
        include_isolated_nodes=False,
    )

    assert node_map == {}
    assert edge_map == {}


def test_filter_subgraph_by_publication_and_organization() -> None:
    service = SemanticGraphService(cast(Session, FakeSession([])), _settings())
    publication_id = str(uuid4())
    related_id = str(uuid4())
    external_id = str(uuid4())
    org_id = str(uuid4())
    payload = {
        "build_id": str(uuid4()),
        "graph_type": "semantic_similarity",
        "generated_at": "2026-04-14T12:00:00+00:00",
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
                "id": publication_id,
                "label": "Paper A",
                "title": "Paper A",
                "normalized_title": "paper a",
                "publication_year": 2024,
                "doi": None,
                "openaire_id": None,
                "publication_type": None,
                "language_code": None,
                "journal_name": None,
                "venue_name": None,
                "authors": [],
                "organization_ids": [org_id],
                "organization_names": ["Uni"],
                "degree": 2,
                "strength": 1.7,
                "betweenness": 1.0,
                "component_id": 0,
                "community_id": 0,
            },
            {
                "id": related_id,
                "label": "Paper B",
                "title": "Paper B",
                "normalized_title": "paper b",
                "publication_year": 2024,
                "doi": None,
                "openaire_id": None,
                "publication_type": None,
                "language_code": None,
                "journal_name": None,
                "venue_name": None,
                "authors": [],
                "organization_ids": [org_id],
                "organization_names": ["Uni"],
                "degree": 1,
                "strength": 0.9,
                "betweenness": 0.0,
                "component_id": 0,
                "community_id": 0,
            },
            {
                "id": external_id,
                "label": "Paper C",
                "title": "Paper C",
                "normalized_title": "paper c",
                "publication_year": 2022,
                "doi": None,
                "openaire_id": None,
                "publication_type": None,
                "language_code": None,
                "journal_name": None,
                "venue_name": None,
                "authors": [],
                "organization_ids": [],
                "organization_names": [],
                "degree": 1,
                "strength": 0.8,
                "betweenness": 0.0,
                "component_id": 0,
                "community_id": 0,
            },
        ],
        "edges": [
            {
                "source": publication_id,
                "target": related_id,
                "weight": 0.9,
                "similarity_score": 0.9,
                "rank": 1,
                "mutual_match": True,
                "source_rank": 1,
                "target_rank": 1,
                "source_score": 0.9,
                "target_score": 0.88,
            },
            {
                "source": publication_id,
                "target": external_id,
                "weight": 0.4,
                "similarity_score": 0.4,
                "rank": 2,
                "mutual_match": False,
                "source_rank": 2,
                "target_rank": None,
                "source_score": 0.4,
                "target_score": None,
            },
        ],
    }

    subgraph = service._filter_subgraph(
        payload,
        publication_id=UUID(publication_id),
        organization_id=UUID(org_id),
        publication_year=2024,
        max_nodes=2,
        min_edge_weight=0.5,
        community_id=None,
    )

    assert subgraph["summary"]["node_count"] == 2
    assert subgraph["summary"]["edge_count"] == 1
    assert {node["id"] for node in subgraph["nodes"]} == {publication_id, related_id}


def test_render_svg_for_graph_uses_scatter_layout_without_labels() -> None:
    service = SemanticGraphService(cast(Session, FakeSession([])), _settings())

    svg = service._render_svg(
        [
            {
                "id": "publication-a",
                "label": "Paper A",
                "title": "Paper A",
                "normalized_title": "paper a",
                "publication_year": 2024,
                "doi": None,
                "openaire_id": None,
                "publication_type": None,
                "language_code": None,
                "journal_name": None,
                "venue_name": None,
                "authors": [],
                "organization_ids": [],
                "organization_names": [],
                "degree": 2,
                "strength": 1.5,
                "betweenness": 0.4,
                "component_id": 0,
                "community_id": 0,
            },
            {
                "id": "publication-b",
                "label": "Paper B",
                "title": "Paper B",
                "normalized_title": "paper b",
                "publication_year": 2024,
                "doi": None,
                "openaire_id": None,
                "publication_type": None,
                "language_code": None,
                "journal_name": None,
                "venue_name": None,
                "authors": [],
                "organization_ids": [],
                "organization_names": [],
                "degree": 1,
                "strength": 0.8,
                "betweenness": 0.0,
                "component_id": 0,
                "community_id": 0,
            },
        ],
        [
            {
                "source": "publication-a",
                "target": "publication-b",
                "weight": 0.8,
                "similarity_score": 0.8,
                "rank": 1,
                "mutual_match": True,
                "source_rank": 1,
                "target_rank": 1,
                "source_score": 0.8,
                "target_score": 0.79,
            },
        ],
    )

    assert "<text" not in svg
    assert 'r="' in svg
