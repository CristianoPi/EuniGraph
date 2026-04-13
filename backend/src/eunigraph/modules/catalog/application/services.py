from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
    ResearcherAffiliationModel,
    ResearcherModel,
)
from eunigraph.shared.utils import normalize_text


@dataclass(slots=True)
class PublicationFilters:
    doi: str | None = None
    publication_year: int | None = None
    title: str | None = None
    openaire_id: str | None = None


@dataclass(slots=True)
class ResearcherFilters:
    name: str | None = None
    orcid: str | None = None
    primary_organization_id: UUID | None = None


@dataclass(slots=True)
class OrganizationFilters:
    name: str | None = None
    organization_type: str | None = None
    parent_organization_id: UUID | None = None


def _commit_or_400(session: Session, detail: str) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from exc


def get_publication_or_404(session: Session, publication_id: UUID) -> PublicationModel:
    publication = session.get(PublicationModel, publication_id)
    if publication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
    return publication


def get_researcher_or_404(session: Session, researcher_id: UUID) -> ResearcherModel:
    researcher = session.get(ResearcherModel, researcher_id)
    if researcher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found")
    return researcher


def get_organization_or_404(session: Session, organization_id: UUID) -> OrganizationModel:
    organization = session.get(OrganizationModel, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


def list_publications(
    session: Session,
    filters: PublicationFilters,
    limit: int = 50,
    offset: int = 0,
) -> list[PublicationModel]:
    query: Select[tuple[PublicationModel]] = select(PublicationModel).order_by(
        PublicationModel.created_at.desc(),
    )

    if filters.doi:
        query = query.where(PublicationModel.doi == filters.doi)
    if filters.publication_year is not None:
        query = query.where(PublicationModel.publication_year == filters.publication_year)
    if filters.openaire_id:
        query = query.where(PublicationModel.openaire_id == filters.openaire_id)
    if filters.title:
        query = query.where(
            PublicationModel.normalized_title.contains(normalize_text(filters.title)),
        )

    return list(session.scalars(query.limit(limit).offset(offset)))


def list_researchers(
    session: Session,
    filters: ResearcherFilters,
    limit: int = 50,
    offset: int = 0,
) -> list[ResearcherModel]:
    query: Select[tuple[ResearcherModel]] = select(ResearcherModel).order_by(
        ResearcherModel.created_at.desc(),
    )

    if filters.orcid:
        query = query.where(ResearcherModel.orcid == filters.orcid)
    if filters.primary_organization_id:
        query = query.where(
            ResearcherModel.primary_organization_id == filters.primary_organization_id,
        )
    if filters.name:
        query = query.where(
            ResearcherModel.normalized_name.contains(normalize_text(filters.name)),
        )

    return list(session.scalars(query.limit(limit).offset(offset)))


def list_organizations(
    session: Session,
    filters: OrganizationFilters,
    limit: int = 50,
    offset: int = 0,
) -> list[OrganizationModel]:
    query: Select[tuple[OrganizationModel]] = select(OrganizationModel).order_by(
        OrganizationModel.created_at.desc(),
    )

    if filters.organization_type:
        query = query.where(OrganizationModel.organization_type == filters.organization_type)
    if filters.parent_organization_id:
        query = query.where(
            OrganizationModel.parent_organization_id == filters.parent_organization_id,
        )
    if filters.name:
        query = query.where(
            OrganizationModel.normalized_name.contains(normalize_text(filters.name)),
        )

    return list(session.scalars(query.limit(limit).offset(offset)))


def create_publication(
    session: Session,
    *,
    title: str,
    abstract: str | None = None,
    publication_year: int | None = None,
    publication_date: date | None = None,
    doi: str | None = None,
    openaire_id: str | None = None,
    publication_type: str | None = None,
    language_code: str | None = None,
    journal_name: str | None = None,
    venue_name: str | None = None,
    publisher: str | None = None,
    open_access: bool | None = None,
    source_url: str | None = None,
) -> PublicationModel:
    publication = PublicationModel(
        title=title,
        normalized_title=normalize_text(title),
        abstract=abstract,
        publication_year=publication_year,
        publication_date=publication_date,
        doi=doi,
        openaire_id=openaire_id,
        publication_type=publication_type,
        language_code=language_code,
        journal_name=journal_name,
        venue_name=venue_name,
        publisher=publisher,
        open_access=open_access,
        source_url=source_url,
    )
    session.add(publication)
    _commit_or_400(session, "Invalid publication payload or conflicting publication data")
    session.refresh(publication)
    return publication


def update_publication(
    session: Session,
    publication: PublicationModel,
    **changes: object,
) -> PublicationModel:
    for field, value in changes.items():
        if value is not None:
            setattr(publication, field, value)

    if changes.get("title") is not None:
        publication.normalized_title = normalize_text(publication.title)

    _commit_or_400(session, "Invalid publication update or conflicting publication data")
    session.refresh(publication)
    return publication


def create_researcher(
    session: Session,
    *,
    full_name: str,
    given_name: str | None = None,
    family_name: str | None = None,
    display_name: str | None = None,
    orcid: str | None = None,
    email: str | None = None,
    profile_url: str | None = None,
    primary_organization_id: UUID | None = None,
) -> ResearcherModel:
    if primary_organization_id is not None:
        get_organization_or_404(session, primary_organization_id)

    researcher = ResearcherModel(
        full_name=full_name,
        given_name=given_name,
        family_name=family_name,
        normalized_name=normalize_text(full_name),
        display_name=display_name,
        orcid=orcid,
        email=email,
        profile_url=profile_url,
        primary_organization_id=primary_organization_id,
    )
    session.add(researcher)
    _commit_or_400(session, "Invalid researcher payload or conflicting researcher data")
    session.refresh(researcher)
    return researcher


def update_researcher(
    session: Session,
    researcher: ResearcherModel,
    **changes: object,
) -> ResearcherModel:
    if changes.get("primary_organization_id") is not None:
        get_organization_or_404(session, changes["primary_organization_id"])  # type: ignore[arg-type]

    for field, value in changes.items():
        if value is not None:
            setattr(researcher, field, value)

    if changes.get("full_name") is not None:
        researcher.normalized_name = normalize_text(researcher.full_name)

    _commit_or_400(session, "Invalid researcher update or conflicting researcher data")
    session.refresh(researcher)
    return researcher


def create_organization(
    session: Session,
    *,
    name: str,
    organization_type: str | None = None,
    country_code: str | None = None,
    city: str | None = None,
    website: str | None = None,
    parent_organization_id: UUID | None = None,
    ror_id: str | None = None,
    openaire_id: str | None = None,
) -> OrganizationModel:
    if parent_organization_id is not None:
        get_organization_or_404(session, parent_organization_id)

    organization = OrganizationModel(
        name=name,
        normalized_name=normalize_text(name),
        organization_type=organization_type,
        country_code=country_code,
        city=city,
        website=website,
        parent_organization_id=parent_organization_id,
        ror_id=ror_id,
        openaire_id=openaire_id,
    )
    session.add(organization)
    _commit_or_400(session, "Invalid organization payload or conflicting organization data")
    session.refresh(organization)
    return organization


def update_organization(
    session: Session,
    organization: OrganizationModel,
    **changes: object,
) -> OrganizationModel:
    if changes.get("parent_organization_id") is not None:
        get_organization_or_404(session, changes["parent_organization_id"])  # type: ignore[arg-type]

    for field, value in changes.items():
        if value is not None:
            setattr(organization, field, value)

    if changes.get("name") is not None:
        organization.normalized_name = normalize_text(organization.name)

    _commit_or_400(session, "Invalid organization update or conflicting organization data")
    session.refresh(organization)
    return organization


def list_publication_authors(
    session: Session,
    publication_id: UUID,
) -> list[PublicationAuthorModel]:
    get_publication_or_404(session, publication_id)
    query = (
        select(PublicationAuthorModel)
        .where(PublicationAuthorModel.publication_id == publication_id)
        .order_by(PublicationAuthorModel.author_position.asc())
    )
    return list(session.scalars(query))


def add_publication_author(
    session: Session,
    *,
    publication_id: UUID,
    researcher_id: UUID,
    author_position: int,
    author_list_name: str | None = None,
    is_corresponding: bool | None = None,
) -> PublicationAuthorModel:
    get_publication_or_404(session, publication_id)
    get_researcher_or_404(session, researcher_id)

    relation = PublicationAuthorModel(
        publication_id=publication_id,
        researcher_id=researcher_id,
        author_position=author_position,
        author_list_name=author_list_name,
        is_corresponding=is_corresponding,
    )
    session.add(relation)
    _commit_or_400(
        session,
        "Invalid publication author payload or conflicting publication author data",
    )
    session.refresh(relation)
    return relation


def list_researcher_affiliations(
    session: Session,
    researcher_id: UUID,
) -> list[ResearcherAffiliationModel]:
    get_researcher_or_404(session, researcher_id)
    query = (
        select(ResearcherAffiliationModel)
        .where(ResearcherAffiliationModel.researcher_id == researcher_id)
        .order_by(
            ResearcherAffiliationModel.is_primary.desc(),
            ResearcherAffiliationModel.created_at.desc(),
        )
    )
    return list(session.scalars(query))


def add_researcher_affiliation(
    session: Session,
    *,
    researcher_id: UUID,
    organization_id: UUID,
    role_title: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    is_primary: bool = False,
) -> ResearcherAffiliationModel:
    get_researcher_or_404(session, researcher_id)
    get_organization_or_404(session, organization_id)

    affiliation = ResearcherAffiliationModel(
        researcher_id=researcher_id,
        organization_id=organization_id,
        role_title=role_title,
        start_date=start_date,
        end_date=end_date,
        is_primary=is_primary,
    )
    session.add(affiliation)
    _commit_or_400(
        session,
        "Invalid researcher affiliation payload or conflicting affiliation data",
    )
    session.refresh(affiliation)
    return affiliation


def list_publication_organizations(
    session: Session,
    publication_id: UUID,
) -> list[PublicationOrganizationModel]:
    get_publication_or_404(session, publication_id)
    query = (
        select(PublicationOrganizationModel)
        .where(PublicationOrganizationModel.publication_id == publication_id)
        .order_by(PublicationOrganizationModel.created_at.asc())
    )
    return list(session.scalars(query))


def add_publication_organization(
    session: Session,
    *,
    publication_id: UUID,
    organization_id: UUID,
    relation_type: str,
) -> PublicationOrganizationModel:
    get_publication_or_404(session, publication_id)
    get_organization_or_404(session, organization_id)

    relation = PublicationOrganizationModel(
        publication_id=publication_id,
        organization_id=organization_id,
        relation_type=relation_type,
    )
    session.add(relation)
    _commit_or_400(
        session,
        "Invalid publication organization payload or conflicting relation data",
    )
    session.refresh(relation)
    return relation
