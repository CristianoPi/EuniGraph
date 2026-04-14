from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_app_settings, get_db_session
from eunigraph.api.openapi import COMMON_ERROR_RESPONSES
from eunigraph.api.schemas.semantic_graph import (
    SemanticGraphBuildRequest,
    SemanticGraphBuildStatusResponse,
    SemanticGraphMetricsResponse,
    SemanticGraphNodeMetricsResponse,
    SemanticGraphPayloadResponse,
)
from eunigraph.core.config import Settings
from eunigraph.modules.semantic_graph.application import SemanticGraphService

router = APIRouter(
    prefix="/semantic-graph",
    tags=["semantic-graph"],
    responses={422: COMMON_ERROR_RESPONSES[422]},
)
DB_SESSION = Depends(get_db_session)
APP_SETTINGS = Depends(get_app_settings)


def _service(session: Session, settings: Settings) -> SemanticGraphService:
    return SemanticGraphService(session, settings)


@router.post(
    "/build",
    response_model=SemanticGraphBuildStatusResponse,
    summary="Build semantic graph",
    description=(
        "Materialize the semantic similarity graph from publication "
        "embeddings stored in Qdrant."
    ),
)
def build_semantic_graph(
    payload: SemanticGraphBuildRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> SemanticGraphBuildStatusResponse:
    summary = _service(session, settings).build(
        triggered_by=payload.triggered_by,
        top_k=payload.top_k,
        score_threshold=payload.score_threshold,
        edge_symmetry_policy=payload.edge_symmetry_policy,
        mutual_knn=payload.mutual_knn,
        include_isolated_nodes=payload.include_isolated_nodes,
        publication_type=payload.publication_type,
        language_code=payload.language_code,
        year_from=payload.year_from,
        year_to=payload.year_to,
    )
    return SemanticGraphBuildStatusResponse(**asdict(summary))


@router.get(
    "/status",
    response_model=SemanticGraphBuildStatusResponse,
    summary="Get semantic graph status",
    description=(
        "Return metadata for the latest semantic graph build, "
        "including artifact paths and resolved build parameters."
    ),
)
def get_semantic_graph_status(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> SemanticGraphBuildStatusResponse:
    return SemanticGraphBuildStatusResponse(**asdict(_service(session, settings).get_status()))


@router.get(
    "",
    response_model=SemanticGraphPayloadResponse,
    summary="Get semantic graph",
    description=(
        "Return the persisted JSON payload of the latest successful "
        "semantic similarity graph build."
    ),
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_semantic_graph(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> SemanticGraphPayloadResponse:
    return SemanticGraphPayloadResponse(**_service(session, settings).get_graph())


@router.get(
    "/subgraph",
    response_model=SemanticGraphPayloadResponse,
    summary="Get semantic subgraph",
    description=(
        "Return a filtered semantic similarity subgraph from the "
        "persisted materialized payload."
    ),
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_semantic_subgraph(
    publication_id: UUID | None = None,
    organization_id: UUID | None = None,
    publication_year: int | None = None,
    max_nodes: int | None = None,
    min_edge_weight: float | None = None,
    community_id: int | None = None,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> SemanticGraphPayloadResponse:
    payload = _service(session, settings).get_subgraph(
        publication_id=publication_id,
        organization_id=organization_id,
        publication_year=publication_year,
        max_nodes=max_nodes,
        min_edge_weight=min_edge_weight,
        community_id=community_id,
    )
    return SemanticGraphPayloadResponse(**payload)


@router.get(
    "/metrics",
    response_model=SemanticGraphMetricsResponse,
    summary="Get semantic graph metrics",
    description="Return graph-level metrics and top nodes for the latest semantic graph build.",
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_semantic_metrics(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> SemanticGraphMetricsResponse:
    return SemanticGraphMetricsResponse(**_service(session, settings).get_metrics())


@router.get(
    "/nodes/{publication_id}",
    response_model=SemanticGraphNodeMetricsResponse,
    summary="Get semantic node metrics",
    description=(
        "Return one publication node plus incident edges and neighbors "
        "from the persisted semantic graph."
    ),
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_semantic_node_metrics(
    publication_id: UUID,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> SemanticGraphNodeMetricsResponse:
    return SemanticGraphNodeMetricsResponse(
        **_service(session, settings).get_node_metrics(publication_id),
    )


@router.get(
    "/visualization",
    summary="Get semantic graph visualization",
    description="Serve the persisted static SVG artifact for the active semantic graph build.",
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_semantic_visualization(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> FileResponse:
    visualization_path = _service(session, settings).get_visualization_path()
    return FileResponse(
        visualization_path,
        media_type="image/svg+xml",
        filename=visualization_path.name,
    )
