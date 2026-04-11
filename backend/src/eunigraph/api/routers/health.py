from __future__ import annotations

from fastapi import APIRouter

from eunigraph.api.schemas.health import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Service health")
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", service="backend")
