from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_app_settings, get_db_session
from eunigraph.api.schemas.embeddings import (
    EmbeddingsBuildRequest,
    EmbeddingsBuildResponse,
    EmbeddingsLoadAllRequest,
    EmbeddingsProviderResponse,
    EmbeddingsResetResponse,
    EmbeddingsStatusResponse,
    PublicationEmbeddingBuildOutcomeResponse,
    PublicationEmbeddingBuildRequest,
    PublicationEmbeddingResponse,
)
from eunigraph.core.config import Settings
from eunigraph.modules.embeddings.application import PublicationEmbeddingService

router = APIRouter(tags=["embeddings"])
DB_SESSION = Depends(get_db_session)
APP_SETTINGS = Depends(get_app_settings)


def _service(session: Session, settings: Settings) -> PublicationEmbeddingService:
    return PublicationEmbeddingService(session, settings)


@router.get("/embeddings/provider", response_model=EmbeddingsProviderResponse)
def get_embeddings_provider(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> EmbeddingsProviderResponse:
    return EmbeddingsProviderResponse(**asdict(_service(session, settings).get_provider_info()))


@router.get("/embeddings/status", response_model=EmbeddingsStatusResponse)
def get_embeddings_status(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> EmbeddingsStatusResponse:
    return EmbeddingsStatusResponse(**asdict(_service(session, settings).get_status()))


@router.post("/embeddings/build", response_model=EmbeddingsBuildResponse)
def post_embeddings_build(
    payload: EmbeddingsBuildRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> EmbeddingsBuildResponse:
    summary = _service(session, settings).build_embeddings(
        publication_ids=payload.publication_ids,
        limit=payload.limit,
        force=payload.force,
    )
    return EmbeddingsBuildResponse(**asdict(summary))


@router.post("/embeddings/load-all", response_model=EmbeddingsBuildResponse)
def post_embeddings_load_all(
    payload: EmbeddingsLoadAllRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> EmbeddingsBuildResponse:
    summary = _service(session, settings).load_all_embeddings(force=payload.force)
    return EmbeddingsBuildResponse(**asdict(summary))


@router.post("/embeddings/reset", response_model=EmbeddingsResetResponse)
def post_embeddings_reset(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> EmbeddingsResetResponse:
    summary = _service(session, settings).reset_embeddings()
    return EmbeddingsResetResponse(**asdict(summary))


@router.post(
    "/publications/{publication_id}/embedding",
    response_model=PublicationEmbeddingBuildOutcomeResponse,
    status_code=201,
)
def post_publication_embedding(
    publication_id: UUID,
    payload: PublicationEmbeddingBuildRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> PublicationEmbeddingBuildOutcomeResponse:
    result = _service(session, settings).build_publication_embedding(
        publication_id,
        force=payload.force,
    )
    return PublicationEmbeddingBuildOutcomeResponse(**asdict(result))


@router.get(
    "/publications/{publication_id}/embedding",
    response_model=PublicationEmbeddingResponse,
)
def get_publication_embedding(
    publication_id: UUID,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> PublicationEmbeddingResponse:
    embedding = _service(session, settings).get_publication_embedding(publication_id)
    return PublicationEmbeddingResponse.model_validate(embedding)
