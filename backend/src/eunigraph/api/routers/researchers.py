from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_db_session
from eunigraph.api.schemas.researchers import (
    ResearcherAffiliationCreate,
    ResearcherAffiliationResponse,
    ResearcherCreate,
    ResearcherResponse,
    ResearcherUpdate,
)
from eunigraph.modules.catalog.application.services import (
    ResearcherFilters,
    add_researcher_affiliation,
    create_researcher,
    get_researcher_or_404,
    list_researcher_affiliations,
    list_researchers,
    update_researcher,
)

router = APIRouter(prefix="/researchers", tags=["researchers"])
DB_SESSION = Depends(get_db_session)
LIMIT_QUERY = Query(default=50, le=500)
OFFSET_QUERY = Query(default=0, ge=0)


def _researcher_response(researcher: object) -> ResearcherResponse:
    return ResearcherResponse.model_validate(researcher)


def _affiliation_response(affiliation: object) -> ResearcherAffiliationResponse:
    return ResearcherAffiliationResponse.model_validate(affiliation)


@router.get("", response_model=list[ResearcherResponse])
def get_researchers(
    name: str | None = None,
    orcid: str | None = None,
    primary_organization_id: UUID | None = None,
    limit: int = LIMIT_QUERY,
    offset: int = OFFSET_QUERY,
    session: Session = DB_SESSION,
) -> list[ResearcherResponse]:
    researchers = list_researchers(
        session,
        ResearcherFilters(
            name=name,
            orcid=orcid,
            primary_organization_id=primary_organization_id,
        ),
        limit=limit,
        offset=offset,
    )
    return [_researcher_response(researcher) for researcher in researchers]


@router.get("/{researcher_id}", response_model=ResearcherResponse)
def get_researcher(
    researcher_id: UUID,
    session: Session = DB_SESSION,
) -> ResearcherResponse:
    return _researcher_response(get_researcher_or_404(session, researcher_id))


@router.post("", response_model=ResearcherResponse, status_code=201)
def post_researcher(
    payload: ResearcherCreate,
    session: Session = DB_SESSION,
) -> ResearcherResponse:
    researcher = create_researcher(session, **payload.model_dump())
    return _researcher_response(researcher)


@router.patch("/{researcher_id}", response_model=ResearcherResponse)
def patch_researcher(
    researcher_id: UUID,
    payload: ResearcherUpdate,
    session: Session = DB_SESSION,
) -> ResearcherResponse:
    researcher = get_researcher_or_404(session, researcher_id)
    updated_researcher = update_researcher(
        session,
        researcher,
        **payload.model_dump(exclude_unset=True),
    )
    return _researcher_response(updated_researcher)


@router.get("/{researcher_id}/affiliations", response_model=list[ResearcherAffiliationResponse])
def get_affiliations(
    researcher_id: UUID,
    session: Session = DB_SESSION,
) -> list[ResearcherAffiliationResponse]:
    affiliations = list_researcher_affiliations(session, researcher_id)
    return [_affiliation_response(affiliation) for affiliation in affiliations]


@router.post(
    "/{researcher_id}/affiliations",
    response_model=ResearcherAffiliationResponse,
    status_code=201,
)
def post_affiliation(
    researcher_id: UUID,
    payload: ResearcherAffiliationCreate,
    session: Session = DB_SESSION,
) -> ResearcherAffiliationResponse:
    affiliation = add_researcher_affiliation(
        session,
        researcher_id=researcher_id,
        **payload.model_dump(),
    )
    return _affiliation_response(affiliation)
