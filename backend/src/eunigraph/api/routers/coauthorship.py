from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_app_settings, get_db_session
from eunigraph.api.openapi import COMMON_ERROR_RESPONSES
from eunigraph.api.schemas.coauthorship import (
    CoauthorshipGraphBuildRequest,
    CoauthorshipGraphBuildStatusResponse,
    CoauthorshipGraphMetricsResponse,
    CoauthorshipGraphPayloadResponse,
    CoauthorshipNodeMetricsResponse,
)
from eunigraph.core.config import Settings
from eunigraph.modules.coauthorship.application import CoauthorshipGraphService

router = APIRouter(
    prefix="/coauthorship-graph",
    tags=["coauthorship"],
    responses={422: COMMON_ERROR_RESPONSES[422]},
)
DB_SESSION = Depends(get_db_session)
APP_SETTINGS = Depends(get_app_settings)
MAX_NODES_QUERY = Query(default=None, ge=1)
MIN_EDGE_WEIGHT_QUERY = Query(default=None, ge=1, le=1000)
MIN_DEGREE_QUERY = Query(default=None, ge=0, le=10000)


def _service(session: Session, settings: Settings) -> CoauthorshipGraphService:
    return CoauthorshipGraphService(session, settings)


@router.post(
    "/build",
    response_model=CoauthorshipGraphBuildStatusResponse,
    summary="Build coauthorship graph",
    description=(
        "Materialize the coauthorship graph from canonical publication "
        "authorship data and persist its artifacts."
    ),
)
def build_coauthorship_graph(
    payload: CoauthorshipGraphBuildRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> CoauthorshipGraphBuildStatusResponse:
    summary = _service(session, settings).build(
        triggered_by=payload.triggered_by,
        include_isolated_nodes=payload.include_isolated_nodes,
    )
    return CoauthorshipGraphBuildStatusResponse(**asdict(summary))


@router.get(
    "/status",
    response_model=CoauthorshipGraphBuildStatusResponse,
    summary="Get coauthorship graph status",
    description=(
        "Return metadata for the latest coauthorship graph build, "
        "including artifact paths and counts."
    ),
)
def get_coauthorship_graph_status(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> CoauthorshipGraphBuildStatusResponse:
    return CoauthorshipGraphBuildStatusResponse(
        **asdict(_service(session, settings).get_status()),
    )


@router.get(
    "",
    response_model=CoauthorshipGraphPayloadResponse,
    summary="Get coauthorship graph",
    description=(
        "Return the persisted JSON payload of the latest successful "
        "coauthorship graph build."
    ),
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_coauthorship_graph(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> CoauthorshipGraphPayloadResponse:
    return CoauthorshipGraphPayloadResponse(**_service(session, settings).get_graph())


@router.get(
    "/subgraph",
    response_model=CoauthorshipGraphPayloadResponse,
    summary="Get coauthorship subgraph",
    description="Return a filtered coauthorship subgraph from the persisted materialized payload.",
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_coauthorship_subgraph(
    researcher_id: UUID | None = None,
    organization_id: UUID | None = None,
    max_nodes: int | None = MAX_NODES_QUERY,
    min_edge_weight: int | None = MIN_EDGE_WEIGHT_QUERY,
    min_degree: int | None = MIN_DEGREE_QUERY,
    largest_component_only: bool = False,
    community_id: int | None = Query(default=None, ge=0),
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> CoauthorshipGraphPayloadResponse:
    payload = _service(session, settings).get_subgraph(
        researcher_id=researcher_id,
        organization_id=organization_id,
        max_nodes=max_nodes,
        min_edge_weight=min_edge_weight,
        min_degree=min_degree,
        largest_component_only=largest_component_only,
        community_id=community_id,
    )
    return CoauthorshipGraphPayloadResponse(**payload)


@router.get(
    "/metrics",
    response_model=CoauthorshipGraphMetricsResponse,
    summary="Get coauthorship metrics",
    description="Return graph-level metrics and top nodes for the latest coauthorship build.",
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_coauthorship_metrics(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> CoauthorshipGraphMetricsResponse:
    return CoauthorshipGraphMetricsResponse(**_service(session, settings).get_metrics())


@router.get(
    "/nodes/{researcher_id}",
    response_model=CoauthorshipNodeMetricsResponse,
    summary="Get coauthorship node metrics",
    description=(
        "Return one researcher node plus incident edges and neighbors "
        "from the persisted coauthorship graph."
    ),
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_coauthorship_node_metrics(
    researcher_id: UUID,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> CoauthorshipNodeMetricsResponse:
    return CoauthorshipNodeMetricsResponse(
        **_service(session, settings).get_node_metrics(researcher_id),
    )


@router.get(
    "/visualization",
    summary="Get coauthorship visualization",
    description="Serve the persisted static SVG artifact for the active coauthorship graph build.",
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_coauthorship_visualization(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> FileResponse:
    visualization_path = _service(session, settings).get_visualization_path()
    return FileResponse(
        visualization_path,
        media_type="image/svg+xml",
        filename=visualization_path.name,
    )
