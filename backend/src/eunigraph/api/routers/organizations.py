from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_db_session
from eunigraph.api.openapi import COMMON_ERROR_RESPONSES
from eunigraph.api.schemas.common import CountResponse
from eunigraph.api.schemas.organizations import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from eunigraph.modules.catalog.application.services import (
    OrganizationFilters,
    count_organizations,
    create_organization,
    get_organization_or_404,
    list_organizations,
    update_organization,
)

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    responses={422: COMMON_ERROR_RESPONSES[422]},
)
DB_SESSION = Depends(get_db_session)
LIMIT_QUERY = Query(default=50, le=500)
OFFSET_QUERY = Query(default=0, ge=0)


def _organization_response(organization: object) -> OrganizationResponse:
    return OrganizationResponse.model_validate(organization)


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List organizations",
    description=(
        "Return canonical organizations with optional filters on name, "
        "organization type or parent organization."
    ),
)
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


@router.get(
    "/count",
    response_model=CountResponse,
    summary="Count organizations",
    description="Return the total number of canonical organizations matching the optional filters.",
)
def get_organizations_count(
    name: str | None = None,
    organization_type: str | None = None,
    parent_organization_id: UUID | None = None,
    session: Session = DB_SESSION,
) -> CountResponse:
    return CountResponse(
        count=count_organizations(
            session,
            OrganizationFilters(
                name=name,
                organization_type=organization_type,
                parent_organization_id=parent_organization_id,
            ),
        ),
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
    description="Return one canonical organization by UUID.",
    responses={404: COMMON_ERROR_RESPONSES[404]},
)
def get_organization(
    organization_id: UUID,
    session: Session = DB_SESSION,
) -> OrganizationResponse:
    return _organization_response(get_organization_or_404(session, organization_id))


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=201,
    summary="Create organization",
    description=(
        "Create a canonical organization and persist manual provenance "
        "through the existing application services."
    ),
    responses={400: COMMON_ERROR_RESPONSES[400]},
)
def post_organization(
    payload: OrganizationCreate,
    session: Session = DB_SESSION,
) -> OrganizationResponse:
    organization = create_organization(session, **payload.model_dump())
    return _organization_response(organization)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Apply a partial update to a canonical organization.",
    responses={
        400: COMMON_ERROR_RESPONSES[400],
        404: COMMON_ERROR_RESPONSES[404],
    },
)
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
