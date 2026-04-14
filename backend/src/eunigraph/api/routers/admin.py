from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_app_settings, get_db_session
from eunigraph.api.openapi import COMMON_ERROR_RESPONSES
from eunigraph.api.schemas.admin import (
    OpenAireSeedLoadRequest,
    OpenAireSeedLoadResponse,
    OpenAireSeedResetResponse,
    OpenAireSeedStatusResponse,
)
from eunigraph.core.config import Settings
from eunigraph.modules.ingestion.application.openaire_beginners_kit import (
    OpenAireBeginnersKitSeeder,
)

router = APIRouter(
    prefix="/admin/seeds/openaire-beginners-kit",
    tags=["admin"],
    responses={422: COMMON_ERROR_RESPONSES[422]},
)
DB_SESSION = Depends(get_db_session)
APP_SETTINGS = Depends(get_app_settings)


@router.get(
    "/status",
    response_model=OpenAireSeedStatusResponse,
    summary="Get OpenAIRE seed status",
    description=(
        "Return dataset availability and table counts for the local "
        "OpenAIRE Beginner's Kit seed workflow."
    ),
)
def get_seed_status(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> OpenAireSeedStatusResponse:
    status_payload = OpenAireBeginnersKitSeeder(session, settings).get_status()
    return OpenAireSeedStatusResponse(**asdict(status_payload))


@router.post(
    "/load",
    response_model=OpenAireSeedLoadResponse,
    summary="Load OpenAIRE Beginner's Kit seed",
    description=(
        "Run the local OpenAIRE Beginner's Kit seed workflow using "
        "the configured dataset path."
    ),
    responses={400: COMMON_ERROR_RESPONSES[400]},
)
def load_seed(
    payload: OpenAireSeedLoadRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> OpenAireSeedLoadResponse:
    return OpenAireSeedLoadResponse.model_validate(
        OpenAireBeginnersKitSeeder(session, settings).load(
            limit_per_file=payload.limit_per_file,
        ),
    )


@router.post(
    "/reset",
    response_model=OpenAireSeedResetResponse,
    summary="Reset OpenAIRE seed data",
    description=(
        "Delete seeded canonical records and provenance rows created by "
        "the OpenAIRE Beginner's Kit workflow."
    ),
)
def reset_seed(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> OpenAireSeedResetResponse:
    return OpenAireSeedResetResponse.model_validate(
        OpenAireBeginnersKitSeeder(session, settings).reset(),
    )
