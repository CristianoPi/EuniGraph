from __future__ import annotations

from fastapi import FastAPI

from eunigraph.api.router import api_router
from eunigraph.core.config import get_settings
from eunigraph.core.lifecycle import lifespan

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)
