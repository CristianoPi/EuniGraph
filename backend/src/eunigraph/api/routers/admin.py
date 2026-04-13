from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_app_settings, get_db_session
from eunigraph.api.schemas.admin import OpenAireSeedLoadRequest, OpenAireSeedStatusResponse
from eunigraph.core.config import Settings
from eunigraph.modules.ingestion.application.openaire_beginners_kit import (
    OpenAireBeginnersKitSeeder,
)

router = APIRouter(prefix="/admin/seeds/openaire-beginners-kit", tags=["admin"])
DB_SESSION = Depends(get_db_session)
APP_SETTINGS = Depends(get_app_settings)


@router.get("/status", response_model=OpenAireSeedStatusResponse)
def get_seed_status(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> OpenAireSeedStatusResponse:
    status_payload = OpenAireBeginnersKitSeeder(session, settings).get_status()
    return OpenAireSeedStatusResponse(**asdict(status_payload))


@router.post("/load")
def load_seed(
    payload: OpenAireSeedLoadRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> dict[str, int | str | None]:
    return OpenAireBeginnersKitSeeder(session, settings).load(limit_per_file=payload.limit_per_file)


@router.post("/reset")
def reset_seed(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> dict[str, int]:
    return OpenAireBeginnersKitSeeder(session, settings).reset()
