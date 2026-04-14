from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SemanticGraphBuildRequest(BaseModel):
    triggered_by: str | None = Field(default=None, max_length=100)
    top_k: int = Field(default=5, ge=1, le=50)
    score_threshold: float | None = 0.75
    edge_symmetry_policy: str = Field(default="max_score_union", max_length=64)
    mutual_knn: bool = False
    include_isolated_nodes: bool = False
    publication_type: str | None = Field(default=None, max_length=64)
    language_code: str | None = Field(default=None, max_length=16)
    year_from: int | None = None
    year_to: int | None = None


class SemanticGraphBuildStatusResponse(BaseModel):
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


class SemanticGraphNodeResponse(BaseModel):
    id: str
    label: str
    title: str
    normalized_title: str
    publication_year: int | None
    doi: str | None
    openaire_id: str | None
    publication_type: str | None
    language_code: str | None
    journal_name: str | None
    venue_name: str | None
    authors: list[str]
    organization_ids: list[str]
    organization_names: list[str]
    degree: int
    strength: float
    betweenness: float
    component_id: int | None
    community_id: int | None


class SemanticGraphEdgeResponse(BaseModel):
    source: str
    target: str
    weight: float
    similarity_score: float
    rank: int
    mutual_match: bool
    source_rank: int | None
    target_rank: int | None
    source_score: float | None
    target_score: float | None


class SemanticGraphPayloadResponse(BaseModel):
    build_id: str | None
    graph_type: str
    generated_at: datetime
    summary: dict[str, Any]
    nodes: list[SemanticGraphNodeResponse]
    edges: list[SemanticGraphEdgeResponse]
    data_snapshot: dict[str, Any]


class SemanticGraphMetricsResponse(BaseModel):
    build_id: str | None
    graph_version: str
    node_count: int
    edge_count: int
    component_count: int
    community_count: int | None
    top_degree_nodes: list[SemanticGraphNodeResponse]
    top_strength_nodes: list[SemanticGraphNodeResponse]
    top_betweenness_nodes: list[SemanticGraphNodeResponse]


class SemanticGraphNodeMetricsNeighborResponse(BaseModel):
    publication_id: str
    weight: float
    similarity_score: float
    rank: int
    mutual_match: bool


class SemanticGraphNodeMetricsResponse(BaseModel):
    build_id: str | None
    node: SemanticGraphNodeResponse
    incident_edges: list[SemanticGraphEdgeResponse]
    neighbors: list[SemanticGraphNodeMetricsNeighborResponse]
