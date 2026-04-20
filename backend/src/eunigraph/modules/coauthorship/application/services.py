from __future__ import annotations

import hashlib
import importlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, joinedload

from eunigraph.core.config import Settings
from eunigraph.modules.catalog.infrastructure.models import (
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    ResearcherAffiliationModel,
    ResearcherModel,
)
from eunigraph.modules.coauthorship.infrastructure.models import (
    CoauthorshipGraphBuildModel,
)
from eunigraph.shared.eunice import EUNICE_UNIVERSITY_SPECS, EUNICEUniversitySpec
from eunigraph.shared.utils import normalize_text

GRAPH_TYPE = "coauthorship"
BUILD_STATUS_COMPLETED = "completed"
BUILD_STATUS_FAILED = "failed"
BUILD_STATUS_NOT_BUILT = "not_built"
BUILD_STATUS_RUNNING = "running"


@dataclass(slots=True)
class CoauthorshipBuildSummary:
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


class CoauthorshipGraphService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.storage_path = settings.coauthorship_graph_storage_path
        self._organization_cache: dict[UUID, OrganizationModel | None] = {}
        self._researcher_affiliation_cache: dict[UUID, list[ResearcherAffiliationModel]] = {}

    def build(
        self,
        *,
        triggered_by: str | None = None,
        include_isolated_nodes: bool = True,
    ) -> CoauthorshipBuildSummary:
        build = CoauthorshipGraphBuildModel(
            graph_type=GRAPH_TYPE,
            status=BUILD_STATUS_RUNNING,
            triggered_by=triggered_by or "api",
            build_params={"include_isolated_nodes": include_isolated_nodes},
            is_active=False,
        )
        self.session.add(build)
        self.session.commit()
        self.session.refresh(build)

        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            payload, graph, snapshot = self._build_materialized_graph(
                include_isolated_nodes=include_isolated_nodes,
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
            build.error_message = None

            self.session.execute(
                update(CoauthorshipGraphBuildModel)
                .where(
                    CoauthorshipGraphBuildModel.graph_type == GRAPH_TYPE,
                    CoauthorshipGraphBuildModel.id != build.id,
                    CoauthorshipGraphBuildModel.is_active.is_(True),
                )
                .values(is_active=False)
            )
            self.session.commit()
            self.session.refresh(build)
            return self._to_summary(build)
        except Exception as exc:
            self.session.rollback()
            failed_build = self.session.get(CoauthorshipGraphBuildModel, build.id)
            if failed_build is None:
                raise
            failed_build.status = BUILD_STATUS_FAILED
            failed_build.completed_at = datetime.now(UTC)
            failed_build.error_message = str(exc)
            failed_build.is_active = False
            self.session.commit()
            self.session.refresh(failed_build)
            return self._to_summary(failed_build)

    def get_status(self) -> CoauthorshipBuildSummary:
        build = self._latest_build()
        if build is None:
            return CoauthorshipBuildSummary(
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
        researcher_id: UUID | None = None,
        organization_id: UUID | None = None,
        max_nodes: int | None = None,
        min_edge_weight: int | None = None,
        community_id: int | None = None,
    ) -> dict[str, Any]:
        payload = self._load_materialized_payload()
        return self._filter_subgraph(
            payload,
            researcher_id=researcher_id,
            organization_id=organization_id,
            max_nodes=max_nodes,
            min_edge_weight=min_edge_weight,
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

    def get_node_metrics(self, researcher_id: UUID) -> dict[str, Any]:
        payload = self._load_materialized_payload()
        researcher_id_str = str(researcher_id)
        node = next(
            (item for item in payload["nodes"] if item["id"] == researcher_id_str),
            None,
        )
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Researcher node not found in the active coauthorship graph",
            )
        incident_edges = [
            edge
            for edge in payload["edges"]
            if edge["source"] == researcher_id_str or edge["target"] == researcher_id_str
        ]
        neighbors = sorted(
            (
                {
                    "researcher_id": (
                        edge["target"] if edge["source"] == researcher_id_str else edge["source"]
                    ),
                    "shared_publication_count": edge["shared_publication_count"],
                    "first_collaboration_year": edge["first_collaboration_year"],
                    "last_collaboration_year": edge["last_collaboration_year"],
                    "weight": edge["weight"],
                }
                for edge in incident_edges
            ),
            key=lambda item: (item["weight"], item["researcher_id"]),
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
                detail="No coauthorship graph visualization is available",
            )
        visualization_path = Path(build.artifact_paths["visualization"])
        if not visualization_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The persisted coauthorship graph visualization file is missing",
            )
        return visualization_path

    def _latest_build(self) -> CoauthorshipGraphBuildModel | None:
        query: Select[tuple[CoauthorshipGraphBuildModel]] = (
            select(CoauthorshipGraphBuildModel)
            .where(CoauthorshipGraphBuildModel.graph_type == GRAPH_TYPE)
            .order_by(CoauthorshipGraphBuildModel.started_at.desc())
        )
        return self.session.scalars(query).first()

    def _latest_successful_build(self) -> CoauthorshipGraphBuildModel | None:
        query: Select[tuple[CoauthorshipGraphBuildModel]] = (
            select(CoauthorshipGraphBuildModel)
            .where(
                CoauthorshipGraphBuildModel.graph_type == GRAPH_TYPE,
                CoauthorshipGraphBuildModel.status == BUILD_STATUS_COMPLETED,
                CoauthorshipGraphBuildModel.is_active.is_(True),
            )
            .order_by(CoauthorshipGraphBuildModel.started_at.desc())
        )
        build = self.session.scalars(query).first()
        if build is not None:
            return build
        fallback_query: Select[tuple[CoauthorshipGraphBuildModel]] = (
            select(CoauthorshipGraphBuildModel)
            .where(
                CoauthorshipGraphBuildModel.graph_type == GRAPH_TYPE,
                CoauthorshipGraphBuildModel.status == BUILD_STATUS_COMPLETED,
            )
            .order_by(CoauthorshipGraphBuildModel.started_at.desc())
        )
        return self.session.scalars(fallback_query).first()

    def _latest_successful_build_or_404(self) -> CoauthorshipGraphBuildModel:
        build = self._latest_successful_build()
        if build is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No completed coauthorship graph build is available",
            )
        return build

    def _to_summary(self, build: CoauthorshipGraphBuildModel) -> CoauthorshipBuildSummary:
        latest_successful_build = self._latest_successful_build()
        return CoauthorshipBuildSummary(
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
                latest_successful_build.id if latest_successful_build else None
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
                detail="No materialized coauthorship graph payload is available",
            )
        payload_path = Path(build.artifact_paths["api_payload"])
        if not payload_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The persisted coauthorship graph payload file is missing",
            )
        return cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))

    def _build_materialized_graph(
        self,
        *,
        include_isolated_nodes: bool,
    ) -> tuple[dict[str, Any], Any, dict[str, Any]]:
        node_map, edge_map = self._collect_graph_inputs(
            include_isolated_nodes=include_isolated_nodes,
        )
        nodes = sorted(node_map.values(), key=lambda node: (node["label"], node["id"]))
        edges = sorted(
            edge_map.values(),
            key=lambda edge: (edge["source"], edge["target"]),
        )
        graph, node_metrics, component_count, community_count = self._analyze_graph(nodes, edges)

        for node in nodes:
            metrics = node_metrics[node["id"]]
            node["degree"] = metrics["degree"]
            node["strength"] = metrics["strength"]
            node["betweenness"] = metrics["betweenness"]
            node["component_id"] = metrics["component_id"]
            node["community_id"] = metrics["community_id"]

        graph_version = self._compute_graph_version(nodes, edges)
        snapshot = self._build_data_snapshot()
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
        return payload, graph, snapshot

    def _collect_graph_inputs(
        self,
        *,
        include_isolated_nodes: bool,
    ) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
        query: Select[tuple[PublicationAuthorModel]] = (
            select(PublicationAuthorModel)
            .options(
                joinedload(PublicationAuthorModel.researcher).joinedload(
                    ResearcherModel.primary_organization,
                ),
                joinedload(PublicationAuthorModel.publication),
            )
            .order_by(PublicationAuthorModel.publication_id, PublicationAuthorModel.author_position)
        )
        authorships = list(self.session.scalars(query))

        node_map: dict[str, dict[str, Any]] = {}
        authors_by_publication: dict[UUID, list[PublicationAuthorModel]] = defaultdict(list)
        for authorship in authorships:
            researcher = authorship.researcher
            publication = authorship.publication
            researcher_id = str(researcher.id)
            primary_organization = researcher.primary_organization
            eunice_university = self._resolve_researcher_eunice_university(researcher)
            if include_isolated_nodes or publication is not None:
                node_map[researcher_id] = {
                    "id": researcher_id,
                    "label": researcher.display_name or researcher.full_name,
                    "full_name": researcher.full_name,
                    "normalized_name": researcher.normalized_name,
                    "primary_organization_id": (
                        str(primary_organization.id) if primary_organization is not None else None
                    ),
                    "primary_organization_name": (
                        primary_organization.name if primary_organization is not None else None
                    ),
                    "university_code": eunice_university.code if eunice_university else None,
                    "university_name": eunice_university.name if eunice_university else None,
                    "is_eunice_university": eunice_university is not None,
                }
            authors_by_publication[authorship.publication_id].append(authorship)

        edge_map: dict[tuple[str, str], dict[str, Any]] = {}
        for publication_id, publication_authors in authors_by_publication.items():
            deduplicated_authors: list[PublicationAuthorModel] = []
            seen_researchers: set[str] = set()
            for author in publication_authors:
                researcher_id = str(author.researcher_id)
                if researcher_id in seen_researchers:
                    continue
                seen_researchers.add(researcher_id)
                deduplicated_authors.append(author)

            if len(deduplicated_authors) < 2:
                continue

            publication = deduplicated_authors[0].publication
            publication_year = self._publication_year(publication)
            for left_index, left_author in enumerate(deduplicated_authors):
                for right_author in deduplicated_authors[left_index + 1 :]:
                    source_id, target_id = sorted(
                        (str(left_author.researcher_id), str(right_author.researcher_id)),
                    )
                    edge_key = (source_id, target_id)
                    edge = edge_map.setdefault(
                        edge_key,
                        {
                            "source": source_id,
                            "target": target_id,
                            "weight": 0,
                            "shared_publication_count": 0,
                            "first_collaboration_year": publication_year,
                            "last_collaboration_year": publication_year,
                            "shared_publication_ids": [],
                        },
                    )
                    edge["weight"] += 1
                    edge["shared_publication_count"] += 1
                    edge["shared_publication_ids"].append(str(publication_id))
                    if publication_year is not None:
                        if (
                            edge["first_collaboration_year"] is None
                            or publication_year < edge["first_collaboration_year"]
                        ):
                            edge["first_collaboration_year"] = publication_year
                        if (
                            edge["last_collaboration_year"] is None
                            or publication_year > edge["last_collaboration_year"]
                        ):
                            edge["last_collaboration_year"] = publication_year

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
        researcher_id_property = graph.new_vertex_property("string")
        label_property = graph.new_vertex_property("string")
        edge_weight_property = graph.new_edge_property("int")

        for index, node in enumerate(nodes):
            vertex = graph.vertex(index)
            vertex_index_by_node_id[node["id"]] = index
            researcher_id_property[vertex] = node["id"]
            label_property[vertex] = node["label"]

        for edge in edges:
            source_vertex = graph.vertex(vertex_index_by_node_id[edge["source"]])
            target_vertex = graph.vertex(vertex_index_by_node_id[edge["target"]])
            graph_edge = graph.add_edge(source_vertex, target_vertex)
            edge_weight_property[graph_edge] = int(edge["weight"])

        graph.vertex_properties["researcher_id"] = researcher_id_property
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
            strength = 0
            for edge in vertex.all_edges():
                strength += int(edge_weight_property[edge])
            node_metrics[node["id"]] = {
                "degree": int(vertex.out_degree()),
                "strength": strength,
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
        json_path = artifact_dir / "coauthorship.json"
        gt_path = artifact_dir / "coauthorship.gt"
        svg_path = artifact_dir / "coauthorship.svg"

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
                "No coauthorship graph has been materialized yet"
                "</text></svg>"
            )

        sorted_nodes = sorted(
            nodes,
            key=lambda node: (-node["strength"], -node["degree"], node["label"]),
        )
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
            stroke_width = 0.35 + min(edge["weight"], 6) * 0.35
            edge_elements.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                f'stroke="#94a3b8" stroke-opacity="0.28" stroke-width="{stroke_width:.2f}" />'
            )

        node_elements = []
        for node in sorted_nodes:
            x, y = positions[node["id"]]
            color = self._node_display_color(node)
            size = 1.8 + min(node["strength"], 12) * 0.3
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

    def _publication_year(self, publication: PublicationModel | None) -> int | None:
        if publication is None:
            return None
        if publication.publication_year is not None:
            return int(publication.publication_year)
        if publication.publication_date is not None:
            return int(publication.publication_date.year)
        return None

    def _compute_graph_version(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> str:
        stable_payload = {
            "nodes": sorted(
                (
                    {
                        "id": node["id"],
                        "primary_organization_id": node["primary_organization_id"],
                        "university_code": node.get("university_code"),
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
                        "first_collaboration_year": edge["first_collaboration_year"],
                        "last_collaboration_year": edge["last_collaboration_year"],
                    }
                    for edge in edges
                ),
                key=lambda edge: (edge["source"], edge["target"]),
            ),
        }
        payload_bytes = json.dumps(stable_payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload_bytes).hexdigest()

    def _build_data_snapshot(self) -> dict[str, Any]:
        researcher_count, researcher_last_updated = self.session.execute(
            select(func.count(ResearcherModel.id), func.max(ResearcherModel.updated_at)),
        ).one()
        publication_count, publication_last_updated = self.session.execute(
            select(func.count(PublicationModel.id), func.max(PublicationModel.updated_at)),
        ).one()
        authorship_count, authorship_last_created = self.session.execute(
            select(
                func.count(PublicationAuthorModel.id),
                func.max(PublicationAuthorModel.created_at),
            ),
        ).one()
        return {
            "researcher_count": int(researcher_count or 0),
            "publication_count": int(publication_count or 0),
            "publication_author_count": int(authorship_count or 0),
            "researcher_last_updated_at": self._isoformat_or_none(researcher_last_updated),
            "publication_last_updated_at": self._isoformat_or_none(publication_last_updated),
            "publication_author_last_created_at": self._isoformat_or_none(authorship_last_created),
        }

    def _filter_subgraph(
        self,
        payload: dict[str, Any],
        *,
        researcher_id: UUID | None,
        organization_id: UUID | None,
        max_nodes: int | None,
        min_edge_weight: int | None,
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
        if organization_id is not None:
            organization_id_str = str(organization_id)
            selected_node_ids &= {
                node["id"]
                for node in nodes
                if node.get("primary_organization_id") == organization_id_str
            }

        if researcher_id is not None:
            researcher_id_str = str(researcher_id)
            candidate_edges = [
                edge
                for edge in edges
                if researcher_id_str in (edge["source"], edge["target"])
                and edge["source"] in selected_node_ids
                and edge["target"] in selected_node_ids
            ]
            candidate_edges.sort(
                key=lambda edge: (
                    edge["weight"],
                    edge["shared_publication_count"],
                    edge["target"],
                    edge["source"],
                ),
                reverse=True,
            )
            selected_node_ids = {researcher_id_str}
            for edge in candidate_edges:
                if max_nodes is not None and len(selected_node_ids) >= max_nodes:
                    break
                selected_node_ids.add(edge["source"])
                if max_nodes is not None and len(selected_node_ids) >= max_nodes:
                    break
                selected_node_ids.add(edge["target"])
        elif max_nodes is not None:
            ranked_nodes = sorted(
                (
                    node
                    for node in nodes
                    if node["id"] in selected_node_ids
                ),
                key=lambda node: (node["strength"], node["degree"], node["label"]),
                reverse=True,
            )
            selected_node_ids = {node["id"] for node in ranked_nodes[:max_nodes]}

        filtered_nodes = [node for node in nodes if node["id"] in selected_node_ids]
        filtered_edges = [
            edge
            for edge in edges
            if edge["source"] in selected_node_ids and edge["target"] in selected_node_ids
        ]

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

    def _load_graph_tool(self) -> dict[str, Any]:
        try:
            graph_tool_module = importlib.import_module("graph_tool")
            centrality_module = importlib.import_module("graph_tool.centrality")
            inference_module = importlib.import_module("graph_tool.inference")
            topology_module = importlib.import_module("graph_tool.topology")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "graph-tool is not available in the backend runtime. Rebuild the backend container "
                "after the graph-tool environment fix before building the coauthorship graph."
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

    def _isoformat_or_none(self, value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    def _node_display_color(self, node: dict[str, Any]) -> str:
        university_code = node.get("university_code")
        if isinstance(university_code, str):
            for spec in EUNICE_UNIVERSITY_SPECS:
                if spec.code == university_code:
                    return spec.color
        return "#a1a1aa"

    def _resolve_researcher_eunice_university(
        self,
        researcher: ResearcherModel,
    ) -> EUNICEUniversitySpec | None:
        primary_match = self._resolve_organization_eunice_university(
            researcher.primary_organization,
        )
        if primary_match is not None:
            return primary_match

        affiliation_matches = {
            match.code: match
            for match in (
                self._resolve_organization_eunice_university(affiliation.organization)
                for affiliation in self._researcher_affiliations(researcher.id)
            )
            if match is not None
        }
        if len(affiliation_matches) == 1:
            return next(iter(affiliation_matches.values()))
        return None

    def _researcher_affiliations(self, researcher_id: UUID) -> list[ResearcherAffiliationModel]:
        cached = self._researcher_affiliation_cache.get(researcher_id)
        if cached is not None:
            return cached

        affiliations = list(
            self.session.scalars(
                select(ResearcherAffiliationModel)
                .options(joinedload(ResearcherAffiliationModel.organization))
                .where(ResearcherAffiliationModel.researcher_id == researcher_id)
            )
        )
        self._researcher_affiliation_cache[researcher_id] = affiliations
        return affiliations

    def _resolve_organization_eunice_university(
        self,
        organization: OrganizationModel | None,
    ) -> EUNICEUniversitySpec | None:
        if organization is None:
            return None

        lineage = self._organization_lineage(organization)
        scores: dict[str, tuple[int, EUNICEUniversitySpec]] = {}
        for candidate in lineage:
            candidate_name = normalize_text(candidate.name)
            if not candidate_name and candidate.normalized_name:
                candidate_name = candidate.normalized_name
            for spec in EUNICE_UNIVERSITY_SPECS:
                score = self._organization_match_score(candidate_name, candidate.country_code, spec)
                if score <= 0:
                    continue
                current = scores.get(spec.code)
                if current is None or score > current[0]:
                    scores[spec.code] = (score, spec)

        if not scores:
            return None

        ordered = sorted(scores.values(), key=lambda item: item[0], reverse=True)
        if len(ordered) > 1 and ordered[0][0] == ordered[1][0]:
            return None
        return ordered[0][1]

    def _organization_lineage(self, organization: OrganizationModel) -> list[OrganizationModel]:
        lineage: list[OrganizationModel] = []
        visited: set[UUID] = set()
        current: OrganizationModel | None = organization

        while current is not None and current.id not in visited:
            visited.add(current.id)
            lineage.append(current)
            if current.parent_organization is not None:
                current = current.parent_organization
                continue
            parent_id = current.parent_organization_id
            if parent_id is None:
                break
            current = self._cached_organization(parent_id)

        return lineage

    def _cached_organization(self, organization_id: UUID) -> OrganizationModel | None:
        if organization_id in self._organization_cache:
            return self._organization_cache[organization_id]
        organization = self.session.get(OrganizationModel, organization_id)
        self._organization_cache[organization_id] = organization
        return organization

    def _organization_match_score(
        self,
        candidate_name: str,
        country_code: str | None,
        spec: EUNICEUniversitySpec,
    ) -> int:
        if not candidate_name:
            return 0

        best_score = 0
        for alias in spec.normalized_aliases:
            if candidate_name == alias:
                best_score = max(best_score, 120)
                continue
            if alias in candidate_name:
                best_score = max(best_score, 100)
                continue
            if candidate_name in alias and len(candidate_name) >= 10:
                best_score = max(best_score, 80)

        if best_score == 0:
            return 0
        if spec.country_code and country_code == spec.country_code:
            best_score += 10
        elif spec.country_code and country_code and country_code != spec.country_code:
            best_score -= 25
        return best_score
