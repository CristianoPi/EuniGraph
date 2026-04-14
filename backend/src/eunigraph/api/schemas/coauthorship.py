from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoauthorshipGraphBuildRequest(BaseModel):
    triggered_by: str | None = Field(default=None, max_length=100)
    include_isolated_nodes: bool = True


class CoauthorshipGraphBuildStatusResponse(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class CoauthorshipNodeResponse(BaseModel):
    id: str
    label: str
    full_name: str
    normalized_name: str
    primary_organization_id: str | None
    primary_organization_name: str | None
    degree: int
    strength: int
    betweenness: float
    component_id: int | None
    community_id: int | None


class CoauthorshipEdgeResponse(BaseModel):
    source: str
    target: str
    weight: int
    shared_publication_count: int
    first_collaboration_year: int | None
    last_collaboration_year: int | None
    shared_publication_ids: list[str]


class CoauthorshipGraphPayloadResponse(BaseModel):
    build_id: str | None
    graph_type: str
    generated_at: datetime
    summary: dict[str, Any]
    nodes: list[CoauthorshipNodeResponse]
    edges: list[CoauthorshipEdgeResponse]
    data_snapshot: dict[str, Any]


class CoauthorshipGraphMetricsResponse(BaseModel):
    build_id: str | None
    graph_version: str
    node_count: int
    edge_count: int
    component_count: int
    community_count: int | None
    top_degree_nodes: list[CoauthorshipNodeResponse]
    top_strength_nodes: list[CoauthorshipNodeResponse]
    top_betweenness_nodes: list[CoauthorshipNodeResponse]


class CoauthorshipNodeMetricsNeighborResponse(BaseModel):
    researcher_id: str
    shared_publication_count: int
    first_collaboration_year: int | None
    last_collaboration_year: int | None
    weight: int


class CoauthorshipNodeMetricsResponse(BaseModel):
    build_id: str | None
    node: CoauthorshipNodeResponse
    incident_edges: list[CoauthorshipEdgeResponse]
    neighbors: list[CoauthorshipNodeMetricsNeighborResponse]
