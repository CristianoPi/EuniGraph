from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from eunigraph.api.deps import get_db_session
from eunigraph.api.schemas.publications import (
    PublicationAuthorCreate,
    PublicationAuthorResponse,
    PublicationCreate,
    PublicationOrganizationCreate,
    PublicationOrganizationResponse,
    PublicationResponse,
    PublicationUpdate,
)
from eunigraph.modules.catalog.application.services import (
    PublicationFilters,
    add_publication_author,
    add_publication_organization,
    create_publication,
    get_publication_or_404,
    list_publication_authors,
    list_publication_organizations,
    list_publications,
    update_publication,
)

router = APIRouter(prefix="/publications", tags=["publications"])
DB_SESSION = Depends(get_db_session)
LIMIT_QUERY = Query(default=50, le=500)
OFFSET_QUERY = Query(default=0, ge=0)


def _publication_response(publication: object) -> PublicationResponse:
    return PublicationResponse.model_validate(publication)


def _publication_author_response(author: object) -> PublicationAuthorResponse:
    return PublicationAuthorResponse.model_validate(author)


def _publication_organization_response(
    organization: object,
) -> PublicationOrganizationResponse:
    return PublicationOrganizationResponse.model_validate(organization)


@router.get("", response_model=list[PublicationResponse])
def get_publications(
    doi: str | None = None,
    publication_year: int | None = None,
    title: str | None = None,
    openaire_id: str | None = None,
    limit: int = LIMIT_QUERY,
    offset: int = OFFSET_QUERY,
    session: Session = DB_SESSION,
) -> list[PublicationResponse]:
    publications = list_publications(
        session,
        PublicationFilters(
            doi=doi,
            publication_year=publication_year,
            title=title,
            openaire_id=openaire_id,
        ),
        limit=limit,
        offset=offset,
    )
    return [_publication_response(publication) for publication in publications]


@router.get("/{publication_id}", response_model=PublicationResponse)
def get_publication(
    publication_id: UUID,
    session: Session = DB_SESSION,
) -> PublicationResponse:
    return _publication_response(get_publication_or_404(session, publication_id))


@router.post("", response_model=PublicationResponse, status_code=201)
def post_publication(
    payload: PublicationCreate,
    session: Session = DB_SESSION,
) -> PublicationResponse:
    publication = create_publication(session, **payload.model_dump())
    return _publication_response(publication)


@router.patch("/{publication_id}", response_model=PublicationResponse)
def patch_publication(
    publication_id: UUID,
    payload: PublicationUpdate,
    session: Session = DB_SESSION,
) -> PublicationResponse:
    publication = get_publication_or_404(session, publication_id)
    updated_publication = update_publication(
        session,
        publication,
        **payload.model_dump(exclude_unset=True),
    )
    return _publication_response(updated_publication)


@router.get("/{publication_id}/authors", response_model=list[PublicationAuthorResponse])
def get_publication_authors(
    publication_id: UUID,
    session: Session = DB_SESSION,
) -> list[PublicationAuthorResponse]:
    authors = list_publication_authors(session, publication_id)
    return [_publication_author_response(author) for author in authors]


@router.post("/{publication_id}/authors", response_model=PublicationAuthorResponse, status_code=201)
def post_publication_author(
    publication_id: UUID,
    payload: PublicationAuthorCreate,
    session: Session = DB_SESSION,
) -> PublicationAuthorResponse:
    author = add_publication_author(
        session,
        publication_id=publication_id,
        **payload.model_dump(),
    )
    return _publication_author_response(author)


@router.get("/{publication_id}/organizations", response_model=list[PublicationOrganizationResponse])
def get_publication_organizations(
    publication_id: UUID,
    session: Session = DB_SESSION,
) -> list[PublicationOrganizationResponse]:
    organizations = list_publication_organizations(session, publication_id)
    return [
        _publication_organization_response(organization)
        for organization in organizations
    ]


@router.post(
    "/{publication_id}/organizations",
    response_model=PublicationOrganizationResponse,
    status_code=201,
)
def post_publication_organization(
    publication_id: UUID,
    payload: PublicationOrganizationCreate,
    session: Session = DB_SESSION,
) -> PublicationOrganizationResponse:
    organization = add_publication_organization(
        session,
        publication_id=publication_id,
        **payload.model_dump(),
    )
    return _publication_organization_response(organization)
