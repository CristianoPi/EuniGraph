from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_app_settings, get_db_session
from eunigraph.api.openapi import COMMON_ERROR_RESPONSES
from eunigraph.api.schemas.admin import (
    OpenAireGraphEuniceSeedLoadRequest,
    OpenAireGraphEuniceSeedLoadResponse,
    OpenAireGraphEuniceSeedStatusResponse,
)
from eunigraph.core.config import Settings
from eunigraph.modules.ingestion.application.openaire_graph_eunice import (
    OpenAireGraphEuniceSeeder,
)

router = APIRouter(
    prefix="/admin/seeds/openaire-graph-eunice",
    tags=["admin"],
    responses={422: COMMON_ERROR_RESPONSES[422]},
)
DB_SESSION = Depends(get_db_session)
APP_SETTINGS = Depends(get_app_settings)


@router.get(
    "/status",
    response_model=OpenAireGraphEuniceSeedStatusResponse,
    summary="Get OpenAIRE Graph EUNICE seed status",
    description=(
        "Return configured target organizations, backend counts and the latest "
        "ingestion status for the targeted EUNICE seed workflow."
    ),
)
def get_eunice_seed_status(
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> OpenAireGraphEuniceSeedStatusResponse:
    status_payload = OpenAireGraphEuniceSeeder(session, settings).get_status()
    return OpenAireGraphEuniceSeedStatusResponse(**asdict(status_payload))


@router.post(
    "/load",
    response_model=OpenAireGraphEuniceSeedLoadResponse,
    summary="Load EUNICE seed from the OpenAIRE Graph API",
    description=(
        "Resolve configured EUNICE target organizations through the OpenAIRE Graph API "
        "and ingest a compact publication-centered demo dataset."
    ),
    responses={
        400: COMMON_ERROR_RESPONSES[400],
        409: COMMON_ERROR_RESPONSES[409],
        503: COMMON_ERROR_RESPONSES[503],
    },
)
def load_eunice_seed(
    payload: OpenAireGraphEuniceSeedLoadRequest,
    session: Session = DB_SESSION,
    settings: Settings = APP_SETTINGS,
) -> OpenAireGraphEuniceSeedLoadResponse:
    return OpenAireGraphEuniceSeedLoadResponse.model_validate(
        OpenAireGraphEuniceSeeder(session, settings).load(
            target_organization_keys=payload.target_organization_keys,
            max_publications_per_organization=payload.max_publications_per_organization,
            publication_year_from=payload.publication_year_from,
            publication_year_to=payload.publication_year_to,
        ),
    )
