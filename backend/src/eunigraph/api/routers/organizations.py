from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_db_session
from eunigraph.api.schemas.organizations import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from eunigraph.modules.catalog.application.services import (
    OrganizationFilters,
    create_organization,
    get_organization_or_404,
    list_organizations,
    update_organization,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])
DB_SESSION = Depends(get_db_session)
LIMIT_QUERY = Query(default=50, le=500)
OFFSET_QUERY = Query(default=0, ge=0)


def _organization_response(organization: object) -> OrganizationResponse:
    return OrganizationResponse.model_validate(organization)


@router.get("", response_model=list[OrganizationResponse])
def get_organizations(
    name: str | None = None,
    organization_type: str | None = None,
    parent_organization_id: UUID | None = None,
    limit: int = LIMIT_QUERY,
    offset: int = OFFSET_QUERY,
    session: Session = DB_SESSION,
) -> list[OrganizationResponse]:
    organizations = list_organizations(
        session,
        OrganizationFilters(
            name=name,
            organization_type=organization_type,
            parent_organization_id=parent_organization_id,
        ),
        limit=limit,
        offset=offset,
    )
    return [_organization_response(organization) for organization in organizations]


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: UUID,
    session: Session = DB_SESSION,
) -> OrganizationResponse:
    return _organization_response(get_organization_or_404(session, organization_id))


@router.post("", response_model=OrganizationResponse, status_code=201)
def post_organization(
    payload: OrganizationCreate,
    session: Session = DB_SESSION,
) -> OrganizationResponse:
    organization = create_organization(session, **payload.model_dump())
    return _organization_response(organization)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
def patch_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    session: Session = DB_SESSION,
) -> OrganizationResponse:
    organization = get_organization_or_404(session, organization_id)
    updated_organization = update_organization(
        session,
        organization,
        **payload.model_dump(exclude_unset=True),
    )
    return _organization_response(updated_organization)
