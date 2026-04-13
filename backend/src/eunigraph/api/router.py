from __future__ import annotations

from fastapi import APIRouter

from eunigraph.api.routers.admin import router as admin_router
from eunigraph.api.routers.health import router as health_router
from eunigraph.api.routers.organizations import router as organizations_router
from eunigraph.api.routers.publications import router as publications_router
from eunigraph.api.routers.researchers import router as researchers_router
from eunigraph.api.routers.source_records import router as source_records_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(publications_router)
api_router.include_router(researchers_router)
api_router.include_router(organizations_router)
api_router.include_router(source_records_router)
api_router.include_router(admin_router)
