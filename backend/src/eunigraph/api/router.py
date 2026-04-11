from __future__ import annotations

from fastapi import APIRouter

from eunigraph.api.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
