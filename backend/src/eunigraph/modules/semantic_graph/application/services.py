from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, selectinload

from eunigraph.core.config import Settings
from eunigraph.modules.catalog.infrastructure.models import (
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
)
from eunigraph.modules.embeddings.infrastructure import (
    PublicationEmbeddingModel,
    QdrantPublicationEmbeddingStore,
)
from eunigraph.modules.semantic_graph.infrastructure.models import SemanticGraphBuildModel
from eunigraph.persistence.qdrant.client import get_qdrant_client

GRAPH_TYPE = "semantic_similarity"
BUILD_STATUS_COMPLETED = "completed"
BUILD_STATUS_FAILED = "failed"
BUILD_STATUS_NOT_BUILT = "not_built"
BUILD_STATUS_RUNNING = "running"
SUPPORTED_EDGE_SYMMETRY_POLICIES = {"max_score_union", "mutual_only"}


@dataclass(slots=True)
class SemanticGraphBuildSummary:
    build_id: UUID | None
    graph_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    triggered_by: str | None
    is_active: bool
    node_count: int | None
    edge_count: int | None
    component_count: int | None
    community_count: int | None
    graph_version: str | None
    artifact_paths: dict[str, str] | None
    build_params: dict[str, Any] | None
    data_snapshot: dict[str, Any] | None
    error_message: str | None
    latest_successful_build_id: UUID | None


class SemanticGraphService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        *,
        vector_store: QdrantPublicationEmbeddingStore | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage_path = settings.semantic_graph_storage_path
        self._vector_store = vector_store

    def build(
        self,
        *,
        triggered_by: str | None = None,
        top_k: int = 5,
        score_threshold: float | None = 0.75,
        edge_symmetry_policy: str = "max_score_union",
        mutual_knn: bool = False,
        include_isolated_nodes: bool = False,
        publication_type: str | None = None,
        language_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> SemanticGraphBuildSummary:
        self._validate_build_params(
            top_k=top_k,
            edge_symmetry_policy=edge_symmetry_policy,
            year_from=year_from,
            year_to=year_to,
        )
        build = SemanticGraphBuildModel(
            graph_type=GRAPH_TYPE,
            status=BUILD_STATUS_RUNNING,
            triggered_by=triggered_by or "api",
            build_params={
                "top_k": top_k,
                "score_threshold": score_threshold,
                "edge_symmetry_policy": edge_symmetry_policy,
                "mutual_knn": mutual_knn,
                "include_isolated_nodes": include_isolated_nodes,
                "publication_type": publication_type,
                "language_code": language_code,
                "year_from": year_from,
                "year_to": year_to,
                "qdrant_collection": self.settings.qdrant_collection_publications,
                "embedding_provider": self.settings.embeddings_provider,
                "embedding_model": self.settings.embeddings_model,
                "embedding_version": self.settings.embeddings_version,
                "weight_strategy": "qdrant_score",
            },
            is_active=False,
        )
        self.session.add(build)
        self.session.commit()
        self.session.refresh(build)

        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            payload, graph, snapshot, resolved_build_params = self._build_materialized_graph(
                top_k=top_k,
                score_threshold=score_threshold,
                edge_symmetry_policy=edge_symmetry_policy,
                mutual_knn=mutual_knn,
                include_isolated_nodes=include_isolated_nodes,
                publication_type=publication_type,
                language_code=language_code,
                year_from=year_from,
                year_to=year_to,
            )
            artifact_dir = self._artifact_directory(build.id)
            artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact_paths = self._write_artifacts(
                build_id=build.id,
                graph=graph,
                payload=payload,
                artifact_dir=artifact_dir,
            )

            build.status = BUILD_STATUS_COMPLETED
            build.completed_at = datetime.now(UTC)
            build.is_active = True
            build.node_count = int(payload["summary"]["node_count"])
            build.edge_count = int(payload["summary"]["edge_count"])
            build.component_count = int(payload["summary"]["component_count"])
            build.community_count = payload["summary"]["community_count"]
            build.graph_version = str(payload["summary"]["graph_version"])
            build.artifact_paths = artifact_paths
            build.data_snapshot = snapshot
            build.build_params = resolved_build_params
            build.error_message = None

            self.session.execute(
                update(SemanticGraphBuildModel)
                .where(
                    SemanticGraphBuildModel.graph_type == GRAPH_TYPE,
                    SemanticGraphBuildModel.id != build.id,
                    SemanticGraphBuildModel.is_active.is_(True),
                )
                .values(is_active=False)
            )
            self.session.commit()
            self.session.refresh(build)
            return self._to_summary(build)
        except Exception as exc:
            self.session.rollback()
            failed_build = self.session.get(SemanticGraphBuildModel, build.id)
            if failed_build is None:
                raise
            failed_build.status = BUILD_STATUS_FAILED
            failed_build.completed_at = datetime.now(UTC)
            failed_build.error_message = str(exc)
            failed_build.is_active = False
            self.session.commit()
            self.session.refresh(failed_build)
            return self._to_summary(failed_build)

    def get_status(self) -> SemanticGraphBuildSummary:
        build = self._latest_build()
        if build is None:
            return SemanticGraphBuildSummary(
                build_id=None,
                graph_type=GRAPH_TYPE,
                status=BUILD_STATUS_NOT_BUILT,
                started_at=None,
                completed_at=None,
                triggered_by=None,
                is_active=False,
                node_count=None,
                edge_count=None,
                component_count=None,
                community_count=None,
                graph_version=None,
                artifact_paths=None,
                build_params=None,
                data_snapshot=None,
                error_message=None,
                latest_successful_build_id=None,
            )
        return self._to_summary(build)

    def get_graph(self) -> dict[str, Any]:
        return self._load_materialized_payload()

    def get_subgraph(
        self,
        *,
        publication_id: UUID | None = None,
        organization_id: UUID | None = None,
        publication_year: int | None = None,
        max_nodes: int | None = None,
        min_edge_weight: float | None = None,
        min_degree: int | None = None,
        largest_component_only: bool = False,
        community_id: int | None = None,
    ) -> dict[str, Any]:
        payload = self._load_materialized_payload()
        return self._filter_subgraph(
            payload,
            publication_id=publication_id,
            organization_id=organization_id,
            publication_year=publication_year,
            max_nodes=max_nodes,
            min_edge_weight=min_edge_weight,
            min_degree=min_degree,
            largest_component_only=largest_component_only,
            community_id=community_id,
        )

    def get_metrics(self) -> dict[str, Any]:
        payload = self._load_materialized_payload()
        nodes = list(payload["nodes"])
        return {
            "build_id": payload["build_id"],
            "graph_version": payload["summary"]["graph_version"],
            "node_count": payload["summary"]["node_count"],
            "edge_count": payload["summary"]["edge_count"],
            "component_count": payload["summary"]["component_count"],
            "community_count": payload["summary"]["community_count"],
            "top_degree_nodes": sorted(
                nodes,
                key=lambda node: (node["degree"], node["strength"], node["label"]),
                reverse=True,
            )[:10],
            "top_strength_nodes": sorted(
                nodes,
                key=lambda node: (node["strength"], node["degree"], node["label"]),
                reverse=True,
            )[:10],
            "top_betweenness_nodes": sorted(
                nodes,
                key=lambda node: (node["betweenness"], node["strength"], node["label"]),
                reverse=True,
            )[:10],
        }

    def get_node_metrics(self, publication_id: UUID) -> dict[str, Any]:
        payload = self._load_materialized_payload()
        publication_id_str = str(publication_id)
        node = next((item for item in payload["nodes"] if item["id"] == publication_id_str), None)
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publication node not found in the active semantic graph",
            )
        incident_edges = [
            edge
            for edge in payload["edges"]
            if edge["source"] == publication_id_str or edge["target"] == publication_id_str
        ]
        neighbors = sorted(
            (
                {
                    "publication_id": (
                        edge["target"] if edge["source"] == publication_id_str else edge["source"]
                    ),
                    "weight": edge["weight"],
                    "similarity_score": edge["similarity_score"],
                    "rank": edge["rank"],
                    "mutual_match": edge["mutual_match"],
                }
                for edge in incident_edges
            ),
            key=lambda item: (item["weight"], item["mutual_match"], -item["rank"]),
            reverse=True,
        )
        return {
            "build_id": payload["build_id"],
            "node": node,
            "incident_edges": incident_edges,
            "neighbors": neighbors,
        }

    def get_visualization_path(self) -> Path:
        build = self._latest_successful_build_or_404()
        if build.artifact_paths is None or "visualization" not in build.artifact_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No semantic graph visualization is available",
            )
        visualization_path = Path(build.artifact_paths["visualization"])
        if not visualization_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The persisted semantic graph visualization file is missing",
            )
        return visualization_path

    def _validate_build_params(
        self,
        *,
        top_k: int,
        edge_symmetry_policy: str,
        year_from: int | None,
        year_to: int | None,
    ) -> None:
        if top_k < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="`top_k` must be greater than or equal to 1",
            )
        if edge_symmetry_policy not in SUPPORTED_EDGE_SYMMETRY_POLICIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported edge symmetry policy `{edge_symmetry_policy}`. "
                    f"Supported values: {', '.join(sorted(SUPPORTED_EDGE_SYMMETRY_POLICIES))}"
                ),
            )
        if year_from is not None and year_to is not None and year_from > year_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="`year_from` cannot be greater than `year_to`",
            )

    def _vector_store_instance(self) -> QdrantPublicationEmbeddingStore:
        if self._vector_store is not None:
            return self._vector_store
        self._vector_store = QdrantPublicationEmbeddingStore(get_qdrant_client())
        return self._vector_store

    def _latest_build(self) -> SemanticGraphBuildModel | None:
        query: Select[tuple[SemanticGraphBuildModel]] = (
            select(SemanticGraphBuildModel)
            .where(SemanticGraphBuildModel.graph_type == GRAPH_TYPE)
            .order_by(SemanticGraphBuildModel.started_at.desc())
        )
        return self.session.scalars(query).first()

    def _latest_successful_build(self) -> SemanticGraphBuildModel | None:
        query: Select[tuple[SemanticGraphBuildModel]] = (
            select(SemanticGraphBuildModel)
            .where(
                SemanticGraphBuildModel.graph_type == GRAPH_TYPE,
                SemanticGraphBuildModel.status == BUILD_STATUS_COMPLETED,
                SemanticGraphBuildModel.is_active.is_(True),
            )
            .order_by(SemanticGraphBuildModel.started_at.desc())
        )
        build = self.session.scalars(query).first()
        if build is not None:
            return build
        fallback_query: Select[tuple[SemanticGraphBuildModel]] = (
            select(SemanticGraphBuildModel)
            .where(
                SemanticGraphBuildModel.graph_type == GRAPH_TYPE,
                SemanticGraphBuildModel.status == BUILD_STATUS_COMPLETED,
            )
            .order_by(SemanticGraphBuildModel.started_at.desc())
        )
        return self.session.scalars(fallback_query).first()

    def _latest_successful_build_or_404(self) -> SemanticGraphBuildModel:
        build = self._latest_successful_build()
        if build is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No completed semantic graph build is available",
            )
        return build

    def _to_summary(self, build: SemanticGraphBuildModel) -> SemanticGraphBuildSummary:
        latest_successful_build = self._latest_successful_build()
        return SemanticGraphBuildSummary(
            build_id=build.id,
            graph_type=build.graph_type,
            status=build.status,
            started_at=build.started_at,
            completed_at=build.completed_at,
            triggered_by=build.triggered_by,
            is_active=build.is_active,
            node_count=build.node_count,
            edge_count=build.edge_count,
            component_count=build.component_count,
            community_count=build.community_count,
            graph_version=build.graph_version,
            artifact_paths=build.artifact_paths,
            build_params=build.build_params,
            data_snapshot=build.data_snapshot,
            error_message=build.error_message,
            latest_successful_build_id=(
                latest_successful_build.id if latest_successful_build is not None else None
            ),
        )

    def _artifact_directory(self, build_id: UUID) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return self.storage_path / f"{timestamp}_{build_id}"

    def _load_materialized_payload(self) -> dict[str, Any]:
        build = self._latest_successful_build_or_404()
        if build.artifact_paths is None or "api_payload" not in build.artifact_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No materialized semantic graph payload is available",
            )
        payload_path = Path(build.artifact_paths["api_payload"])
        if not payload_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The persisted semantic graph payload file is missing",
            )
        return cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))

    def _build_materialized_graph(
        self,
        *,
        top_k: int,
        score_threshold: float | None,
        edge_symmetry_policy: str,
        mutual_knn: bool,
        include_isolated_nodes: bool,
        publication_type: str | None,
        language_code: str | None,
        year_from: int | None,
        year_to: int | None,
    ) -> tuple[dict[str, Any], Any, dict[str, Any], dict[str, Any]]:
        publications = self._select_publications_with_embeddings(
            publication_type=publication_type,
            language_code=language_code,
            year_from=year_from,
            year_to=year_to,
        )
        collection_status = self._vector_store_instance().get_collection_status(
            self.settings.qdrant_collection_publications,
        )
        if publications and not collection_status["exists"]:
            raise RuntimeError(
                "Configured Qdrant collection "
                f"`{self.settings.qdrant_collection_publications}` is missing",
            )
        qdrant_distance = self._vector_store_instance().get_collection_distance(
            self.settings.qdrant_collection_publications,
        )
        node_map, edge_map = self._collect_graph_inputs(
            publications=publications,
            top_k=top_k,
            score_threshold=score_threshold,
            mutual_knn=mutual_knn,
            edge_symmetry_policy=edge_symmetry_policy,
            include_isolated_nodes=include_isolated_nodes,
        )
        nodes = sorted(node_map.values(), key=lambda node: (node["label"], node["id"]))
        edges = sorted(edge_map.values(), key=lambda edge: (edge["source"], edge["target"]))
        graph, node_metrics, component_count, community_count = self._analyze_graph(nodes, edges)

        for node in nodes:
            metrics = node_metrics[node["id"]]
            node["degree"] = metrics["degree"]
            node["strength"] = metrics["strength"]
            node["betweenness"] = metrics["betweenness"]
            node["component_id"] = metrics["component_id"]
            node["community_id"] = metrics["community_id"]

        graph_version = self._compute_graph_version(
            nodes=nodes,
            edges=edges,
            build_params={
                "top_k": top_k,
                "score_threshold": score_threshold,
                "edge_symmetry_policy": edge_symmetry_policy,
                "mutual_knn": mutual_knn,
                "qdrant_distance": qdrant_distance,
            },
        )
        snapshot = self._build_data_snapshot(publication_count=len(publications))
        resolved_build_params = {
            "qdrant_collection": self.settings.qdrant_collection_publications,
            "qdrant_distance": qdrant_distance,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "edge_symmetry_policy": edge_symmetry_policy,
            "mutual_knn": mutual_knn,
            "weight_strategy": "qdrant_score",
            "include_isolated_nodes": include_isolated_nodes,
            "publication_type": publication_type,
            "language_code": language_code,
            "year_from": year_from,
            "year_to": year_to,
            "embedding_provider": self.settings.embeddings_provider,
            "embedding_model": self.settings.embeddings_model,
            "embedding_version": self.settings.embeddings_version,
        }
        payload = {
            "build_id": None,
            "graph_type": GRAPH_TYPE,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "component_count": component_count,
                "community_count": community_count,
                "graph_version": graph_version,
            },
            "nodes": nodes,
            "edges": edges,
            "data_snapshot": snapshot,
        }
        return payload, graph, snapshot, resolved_build_params

    def _select_publications_with_embeddings(
        self,
        *,
        publication_type: str | None,
        language_code: str | None,
        year_from: int | None,
        year_to: int | None,
    ) -> list[PublicationModel]:
        query: Select[tuple[PublicationModel]] = (
            select(PublicationModel)
            .join(PublicationModel.embeddings)
            .options(
                selectinload(PublicationModel.embeddings),
                selectinload(PublicationModel.authors).selectinload(
                    PublicationAuthorModel.researcher,
                ),
                selectinload(PublicationModel.organizations).selectinload(
                    PublicationOrganizationModel.organization,
                ),
            )
            .where(
                PublicationEmbeddingModel.embedding_provider == self.settings.embeddings_provider,
                PublicationEmbeddingModel.embedding_model == self.settings.embeddings_model,
                PublicationEmbeddingModel.embedding_version == self.settings.embeddings_version,
                PublicationEmbeddingModel.qdrant_collection
                == self.settings.qdrant_collection_publications,
            )
            .order_by(PublicationModel.created_at.desc())
        )
        if publication_type is not None:
            query = query.where(PublicationModel.publication_type == publication_type)
        if language_code is not None:
            query = query.where(PublicationModel.language_code == language_code)
        if year_from is not None:
            query = query.where(PublicationModel.publication_year >= year_from)
        if year_to is not None:
            query = query.where(PublicationModel.publication_year <= year_to)
        return list(self.session.scalars(query).unique())

    def _collect_graph_inputs(
        self,
        *,
        publications: list[PublicationModel],
        top_k: int,
        score_threshold: float | None,
        mutual_knn: bool,
        edge_symmetry_policy: str,
        include_isolated_nodes: bool,
    ) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
        node_map: dict[str, dict[str, Any]] = {}
        point_id_to_publication_id: dict[str, str] = {}
        for publication in publications:
            publication_id = str(publication.id)
            node_map[publication_id] = {
                "id": publication_id,
                "label": self._publication_label(publication.title),
                "title": publication.title,
                "normalized_title": publication.normalized_title,
                "publication_year": self._publication_year(publication),
                "doi": publication.doi,
                "openaire_id": publication.openaire_id,
                "publication_type": publication.publication_type,
                "language_code": publication.language_code,
                "journal_name": publication.journal_name,
                "venue_name": publication.venue_name,
                "authors": self._publication_author_names(publication),
                "organization_ids": self._publication_organization_ids(publication),
                "organization_names": self._publication_organization_names(publication),
            }
            embedding = self._matching_embedding(publication)
            if embedding is not None:
                point_id_to_publication_id[embedding.qdrant_point_id] = publication_id

        directional_edges: dict[tuple[str, str], dict[str, Any]] = {}
        query_limit = max((top_k * 4), top_k + 10)
        for publication in publications:
            source_embedding = self._matching_embedding(publication)
            if source_embedding is None:
                continue
            source_id = str(publication.id)
            neighbor_hits = self._vector_store_instance().query_similar_publications(
                collection_name=self.settings.qdrant_collection_publications,
                point_id=source_embedding.qdrant_point_id,
                limit=query_limit,
                score_threshold=score_threshold,
            )
            accepted_count = 0
            for hit in neighbor_hits:
                target_id = self._target_publication_id(
                    point_id=str(hit["point_id"]),
                    payload=cast(dict[str, Any], hit["payload"]),
                    point_id_to_publication_id=point_id_to_publication_id,
                )
                if target_id is None or target_id == source_id or target_id not in node_map:
                    continue
                accepted_count += 1
                directional_edges[(source_id, target_id)] = {
                    "source": source_id,
                    "target": target_id,
                    "score": float(hit["score"]),
                    "rank": accepted_count,
                }
                if accepted_count >= top_k:
                    break

        edge_map: dict[tuple[str, str], dict[str, Any]] = {}
        for source_id, target_id in directional_edges:
            pair = (
                source_id if source_id < target_id else target_id,
                target_id if source_id < target_id else source_id,
            )
            if pair in edge_map:
                continue
            left_to_right = directional_edges.get((pair[0], pair[1]))
            right_to_left = directional_edges.get((pair[1], pair[0]))
            mutual_match = left_to_right is not None and right_to_left is not None
            if mutual_knn or edge_symmetry_policy == "mutual_only":
                if not mutual_match:
                    continue
            candidate_edges = [edge for edge in (left_to_right, right_to_left) if edge is not None]
            best_edge = max(candidate_edges, key=lambda edge: (edge["score"], -edge["rank"]))
            rank_values = [edge["rank"] for edge in candidate_edges]
            edge_map[pair] = {
                "source": pair[0],
                "target": pair[1],
                "weight": float(best_edge["score"]),
                "similarity_score": float(best_edge["score"]),
                "rank": min(rank_values),
                "mutual_match": mutual_match,
                "source_rank": left_to_right["rank"] if left_to_right is not None else None,
                "target_rank": right_to_left["rank"] if right_to_left is not None else None,
                "source_score": (
                    float(left_to_right["score"]) if left_to_right is not None else None
                ),
                "target_score": (
                    float(right_to_left["score"]) if right_to_left is not None else None
                ),
            }

        if not include_isolated_nodes:
            connected_node_ids = {
                node_id
                for edge in edge_map.values()
                for node_id in (edge["source"], edge["target"])
            }
            node_map = {
                node_id: node
                for node_id, node in node_map.items()
                if node_id in connected_node_ids
            }
        return node_map, edge_map

    def _analyze_graph(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> tuple[Any, dict[str, dict[str, int | float | None]], int, int | None]:
        graph_tool = self._load_graph_tool()
        graph = graph_tool["Graph"](directed=False)
        graph.add_vertex(len(nodes))

        vertex_index_by_node_id: dict[str, int] = {}
        publication_id_property = graph.new_vertex_property("string")
        label_property = graph.new_vertex_property("string")
        edge_weight_property = graph.new_edge_property("double")

        for index, node in enumerate(nodes):
            vertex = graph.vertex(index)
            vertex_index_by_node_id[node["id"]] = index
            publication_id_property[vertex] = node["id"]
            label_property[vertex] = node["label"]

        for edge in edges:
            source_vertex = graph.vertex(vertex_index_by_node_id[edge["source"]])
            target_vertex = graph.vertex(vertex_index_by_node_id[edge["target"]])
            graph_edge = graph.add_edge(source_vertex, target_vertex)
            edge_weight_property[graph_edge] = float(edge["weight"])

        graph.vertex_properties["publication_id"] = publication_id_property
        graph.vertex_properties["label"] = label_property
        graph.edge_properties["weight"] = edge_weight_property

        node_metrics: dict[str, dict[str, int | float | None]] = {}
        if nodes:
            vertex_betweenness, _ = graph_tool["betweenness"](graph, weight=edge_weight_property)
            component_labels, component_histogram = graph_tool["label_components"](graph)
            component_count = int(len(component_histogram))
            community_ids: dict[int, int] | None = None
            community_count: int | None = None
            if graph.num_vertices() > 0 and graph.num_edges() > 0:
                try:
                    community_ids = {}
                    community_state = graph_tool["minimize_blockmodel_dl"](graph)
                    blocks = community_state.get_blocks()
                    for index in range(len(nodes)):
                        community_ids[index] = int(blocks[graph.vertex(index)])
                    community_count = len(set(community_ids.values()))
                except Exception:
                    community_ids = None
                    community_count = None
        else:
            component_count = 0
            component_labels = None
            vertex_betweenness = None
            community_ids = None
            community_count = 0

        for node in nodes:
            vertex = graph.vertex(vertex_index_by_node_id[node["id"]])
            strength = 0.0
            for edge in vertex.all_edges():
                strength += float(edge_weight_property[edge])
            node_metrics[node["id"]] = {
                "degree": int(vertex.out_degree()),
                "strength": round(strength, 6),
                "betweenness": (
                    float(vertex_betweenness[vertex]) if vertex_betweenness is not None else 0.0
                ),
                "component_id": (
                    int(component_labels[vertex]) if component_labels is not None else None
                ),
                "community_id": (
                    community_ids[vertex_index_by_node_id[node["id"]]]
                    if community_ids is not None
                    else None
                ),
            }

        return graph, node_metrics, component_count, community_count

    def _write_artifacts(
        self,
        *,
        build_id: UUID,
        graph: Any,
        payload: dict[str, Any],
        artifact_dir: Path,
    ) -> dict[str, str]:
        json_path = artifact_dir / "semantic_graph.json"
        gt_path = artifact_dir / "semantic_graph.gt"
        svg_path = artifact_dir / "semantic_graph.svg"

        payload["build_id"] = str(build_id)
        json_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        graph.save(str(gt_path))
        svg_path.write_text(
            self._render_svg(payload["nodes"], payload["edges"]),
            encoding="utf-8",
        )
        return {
            "graph": str(gt_path),
            "api_payload": str(json_path),
            "visualization": str(svg_path),
        }

    def _render_svg(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
        width = 1400
        height = 1000
        if not nodes:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                '<rect width="100%" height="100%" fill="#ffffff" />'
                '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
                'font-family="sans-serif" font-size="28" fill="#333333">'
                "No semantic graph has been materialized yet"
                "</text></svg>"
            )

        sorted_nodes = sorted(
            nodes,
            key=lambda node: (-node["strength"], -node["degree"], node["label"]),
        )
        palette = [
            "#0f766e",
            "#0ea5e9",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#84cc16",
            "#ec4899",
        ]
        positions: dict[str, tuple[float, float]] = {}
        for node in sorted_nodes:
            positions[node["id"]] = self._scatter_position(
                node_id=node["id"],
                width=width,
                height=height,
            )

        edge_elements = []
        for edge in edges:
            x1, y1 = positions[edge["source"]]
            x2, y2 = positions[edge["target"]]
            stroke_width = 0.3 + min(float(edge["weight"]) * 2.5, 2.8)
            edge_elements.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                f'stroke="#94a3b8" stroke-opacity="0.24" stroke-width="{stroke_width:.2f}" />'
            )

        node_elements = []
        for node in sorted_nodes:
            x, y = positions[node["id"]]
            component_id = node.get("community_id")
            if component_id is None:
                component_id = node.get("component_id", 0)
            color = palette[int(component_id or 0) % len(palette)]
            size = 1.7 + min(float(node["strength"]) * 0.55, 4.0)
            node_elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{size:.2f}" fill="{color}" '
                'stroke="#ffffff" stroke-width="0.6" />'
            )

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            '<rect width="100%" height="100%" fill="#f8fafc" />'
            '<g>'
            + "".join(edge_elements)
            + "</g><g>"
            + "".join(node_elements)
            + "</g></svg>"
        )

    def _scatter_position(
        self,
        *,
        node_id: str,
        width: int,
        height: int,
    ) -> tuple[float, float]:
        margin_x = 70
        margin_y = 70
        digest = hashlib.sha256(node_id.encode("utf-8")).digest()
        x_seed = int.from_bytes(digest[:8], byteorder="big")
        y_seed = int.from_bytes(digest[8:16], byteorder="big")
        usable_width = width - (margin_x * 2)
        usable_height = height - (margin_y * 2)
        x = margin_x + (x_seed / (2**64 - 1)) * usable_width
        y = margin_y + (y_seed / (2**64 - 1)) * usable_height
        return (x, y)

    def _compute_graph_version(
        self,
        *,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        build_params: dict[str, Any],
    ) -> str:
        stable_payload = {
            "nodes": sorted(
                (
                    {
                        "id": node["id"],
                        "publication_year": node["publication_year"],
                        "organization_ids": node["organization_ids"],
                    }
                    for node in nodes
                ),
                key=lambda node: node["id"],
            ),
            "edges": sorted(
                (
                    {
                        "source": edge["source"],
                        "target": edge["target"],
                        "weight": edge["weight"],
                        "rank": edge["rank"],
                        "mutual_match": edge["mutual_match"],
                    }
                    for edge in edges
                ),
                key=lambda edge: (edge["source"], edge["target"]),
            ),
            "build_params": build_params,
        }
        payload_bytes = json.dumps(stable_payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload_bytes).hexdigest()

    def _build_data_snapshot(self, *, publication_count: int) -> dict[str, Any]:
        embedding_count, latest_embedding_updated_at = self.session.execute(
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
        collection_status = self._vector_store_instance().get_collection_status(
            self.settings.qdrant_collection_publications,
        )
        return {
            "selected_publication_count": publication_count,
            "active_embedding_count": int(embedding_count or 0),
            "qdrant_collection_exists": bool(collection_status["exists"]),
            "qdrant_points_count": int(collection_status["points_count"]),
            "qdrant_collection_status": collection_status["status"],
            "latest_embedding_updated_at": self._isoformat_or_none(latest_embedding_updated_at),
        }

    def _filter_subgraph(
        self,
        payload: dict[str, Any],
        *,
        publication_id: UUID | None,
        organization_id: UUID | None,
        publication_year: int | None,
        max_nodes: int | None,
        min_edge_weight: float | None,
        min_degree: int | None = None,
        largest_component_only: bool = False,
        community_id: int | None,
    ) -> dict[str, Any]:
        nodes = list(payload["nodes"])
        edges = list(payload["edges"])
        if min_edge_weight is not None:
            edges = [edge for edge in edges if edge["weight"] >= min_edge_weight]

        selected_node_ids = {node["id"] for node in nodes}
        if community_id is not None:
            selected_node_ids = {
                node["id"] for node in nodes if node.get("community_id") == community_id
            }
        if publication_year is not None:
            selected_node_ids &= {
                node["id"]
                for node in nodes
                if node.get("publication_year") == publication_year
            }
        if organization_id is not None:
            organization_id_str = str(organization_id)
            selected_node_ids &= {
                node["id"]
                for node in nodes
                if organization_id_str in node.get("organization_ids", [])
            }

        if min_degree is not None:
            selected_node_ids, edges = self._apply_min_degree_filter(
                selected_node_ids=selected_node_ids,
                edges=edges,
                min_degree=min_degree,
            )

        if publication_id is not None:
            publication_id_str = str(publication_id)
            candidate_edges = [
                edge
                for edge in edges
                if publication_id_str in (edge["source"], edge["target"])
                and edge["source"] in selected_node_ids
                and edge["target"] in selected_node_ids
            ]
            candidate_edges.sort(
                key=lambda edge: (
                    edge["weight"],
                    edge["mutual_match"],
                    -edge["rank"],
                    edge["target"],
                    edge["source"],
                ),
                reverse=True,
            )
            selected_node_ids = {publication_id_str}
            for edge in candidate_edges:
                if max_nodes is not None and len(selected_node_ids) >= max_nodes:
                    break
                selected_node_ids.add(edge["source"])
                if max_nodes is not None and len(selected_node_ids) >= max_nodes:
                    break
                selected_node_ids.add(edge["target"])
        elif max_nodes is not None:
            ranked_nodes = sorted(
                (node for node in nodes if node["id"] in selected_node_ids),
                key=lambda node: (node["strength"], node["degree"], node["label"]),
                reverse=True,
            )
            selected_node_ids = {node["id"] for node in ranked_nodes[:max_nodes]}

        if largest_component_only:
            selected_node_ids = self._largest_component_node_ids(
                selected_node_ids=selected_node_ids,
                edges=edges,
            )

        filtered_nodes = [node for node in nodes if node["id"] in selected_node_ids]
        filtered_edges = [
            edge
            for edge in edges
            if edge["source"] in selected_node_ids and edge["target"] in selected_node_ids
        ]
        filtered_nodes = [node for node in nodes if node["id"] in selected_node_ids]
        return {
            "build_id": payload["build_id"],
            "graph_type": payload["graph_type"],
            "generated_at": payload["generated_at"],
            "summary": {
                "node_count": len(filtered_nodes),
                "edge_count": len(filtered_edges),
                "component_count": len(
                    {
                        node["component_id"]
                        for node in filtered_nodes
                        if node["component_id"] is not None
                    }
                ),
                "community_count": len(
                    {
                        node["community_id"]
                        for node in filtered_nodes
                        if node["community_id"] is not None
                    }
                )
                or None,
                "graph_version": payload["summary"]["graph_version"],
            },
            "nodes": filtered_nodes,
            "edges": filtered_edges,
            "data_snapshot": payload["data_snapshot"],
        }

    def _apply_min_degree_filter(
        self,
        *,
        selected_node_ids: set[str],
        edges: list[dict[str, Any]],
        min_degree: int,
    ) -> tuple[set[str], list[dict[str, Any]]]:
        if min_degree <= 0:
            return selected_node_ids, edges
        filtered_edges = [
            edge
            for edge in edges
            if edge["source"] in selected_node_ids and edge["target"] in selected_node_ids
        ]
        degrees = self._compute_filtered_node_metrics(
            selected_node_ids=selected_node_ids,
            edges=filtered_edges,
        )
        retained_node_ids = {
            node_id
            for node_id, metrics in degrees.items()
            if metrics["degree"] >= min_degree
        }
        retained_edges = [
            edge
            for edge in filtered_edges
            if edge["source"] in retained_node_ids and edge["target"] in retained_node_ids
        ]
        return retained_node_ids, retained_edges

    def _largest_component_node_ids(
        self,
        *,
        selected_node_ids: set[str],
        edges: list[dict[str, Any]],
    ) -> set[str]:
        if not selected_node_ids:
            return set()
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in selected_node_ids}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adjacency and target in adjacency:
                adjacency[source].add(target)
                adjacency[target].add(source)

        visited: set[str] = set()
        largest_component: set[str] = set()
        for node_id in selected_node_ids:
            if node_id in visited:
                continue
            stack = [node_id]
            component: set[str] = set()
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                stack.extend(adjacency[current] - visited)
            if len(component) > len(largest_component):
                largest_component = component
        return largest_component

    def _compute_filtered_node_metrics(
        self,
        *,
        selected_node_ids: set[str],
        edges: list[dict[str, Any]],
    ) -> dict[str, dict[str, int | float]]:
        metrics = {
            node_id: {"degree": 0, "strength": 0.0}
            for node_id in selected_node_ids
        }
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            weight = float(edge["weight"])
            if source in metrics:
                metrics[source]["degree"] = int(metrics[source]["degree"]) + 1
                metrics[source]["strength"] = float(metrics[source]["strength"]) + weight
            if target in metrics:
                metrics[target]["degree"] = int(metrics[target]["degree"]) + 1
                metrics[target]["strength"] = float(metrics[target]["strength"]) + weight
        return metrics

    def _load_graph_tool(self) -> dict[str, Any]:
        try:
            graph_tool_module = importlib.import_module("graph_tool")
            centrality_module = importlib.import_module("graph_tool.centrality")
            inference_module = importlib.import_module("graph_tool.inference")
            topology_module = importlib.import_module("graph_tool.topology")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "graph-tool is not available in the backend runtime. Rebuild the backend container "
                "after the graph-tool environment fix before building the semantic graph."
            ) from exc

        graph_tool_module = cast(Any, graph_tool_module)
        centrality_module = cast(Any, centrality_module)
        inference_module = cast(Any, inference_module)
        topology_module = cast(Any, topology_module)
        return {
            "Graph": graph_tool_module.Graph,
            "betweenness": centrality_module.betweenness,
            "label_components": topology_module.label_components,
            "minimize_blockmodel_dl": inference_module.minimize_blockmodel_dl,
        }

    def _matching_embedding(
        self,
        publication: PublicationModel,
    ) -> PublicationEmbeddingModel | None:
        for embedding in publication.embeddings:
            if (
                embedding.embedding_provider == self.settings.embeddings_provider
                and embedding.embedding_model == self.settings.embeddings_model
                and embedding.embedding_version == self.settings.embeddings_version
                and embedding.qdrant_collection == self.settings.qdrant_collection_publications
            ):
                return embedding
        return None

    def _target_publication_id(
        self,
        *,
        point_id: str,
        payload: dict[str, Any],
        point_id_to_publication_id: dict[str, str],
    ) -> str | None:
        publication_id = payload.get("publication_id")
        if publication_id is not None:
            return str(publication_id)
        return point_id_to_publication_id.get(point_id)

    def _publication_label(self, title: str) -> str:
        compact = " ".join(title.split())
        if len(compact) <= 120:
            return compact
        return f"{compact[:117]}..."

    def _publication_year(self, publication: PublicationModel) -> int | None:
        if publication.publication_year is not None:
            return int(publication.publication_year)
        if publication.publication_date is not None:
            return int(publication.publication_date.year)
        return None

    def _publication_author_names(self, publication: PublicationModel) -> list[str]:
        ordered_authors = sorted(publication.authors, key=lambda author: author.author_position)
        author_names: list[str] = []
        for author in ordered_authors:
            if author.researcher is not None and author.researcher.full_name.strip():
                author_names.append(author.researcher.full_name.strip())
                continue
            if author.author_list_name is not None and author.author_list_name.strip():
                author_names.append(author.author_list_name.strip())
        return author_names

    def _publication_organization_ids(self, publication: PublicationModel) -> list[str]:
        identifiers = {
            str(link.organization.id)
            for link in publication.organizations
            if link.organization is not None
        }
        return sorted(identifiers)

    def _publication_organization_names(self, publication: PublicationModel) -> list[str]:
        names = {
            link.organization.name
            for link in publication.organizations
            if link.organization is not None and link.organization.name
        }
        return sorted(names)

    def _isoformat_or_none(self, value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None
