from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PublicationBase(BaseModel):
    title: str
    abstract: str | None = None
    publication_year: int | None = None
    publication_date: date | None = None
    doi: str | None = None
    openaire_id: str | None = None
    publication_type: str | None = None
    language_code: str | None = None
    journal_name: str | None = None
    venue_name: str | None = None
    publisher: str | None = None
    open_access: bool | None = None
    source_url: str | None = None


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    title: str | None = None
    abstract: str | None = None
    publication_year: int | None = None
    publication_date: date | None = None
    doi: str | None = None
    openaire_id: str | None = None
    publication_type: str | None = None
    language_code: str | None = None
    journal_name: str | None = None
    venue_name: str | None = None
    publisher: str | None = None
    open_access: bool | None = None
    source_url: str | None = None


class PublicationResponse(PublicationBase):
    id: UUID
    normalized_title: str
    canonical_source_record_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAuthorCreate(BaseModel):
    researcher_id: UUID
    author_position: int
    author_list_name: str | None = None
    is_corresponding: bool | None = None


class PublicationAuthorResponse(BaseModel):
    id: UUID
    publication_id: UUID
    researcher_id: UUID
    author_position: int
    author_list_name: str | None
    is_corresponding: bool | None
    source_record_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationOrganizationCreate(BaseModel):
    organization_id: UUID
    relation_type: str


class PublicationOrganizationResponse(BaseModel):
    id: UUID
    publication_id: UUID
    organization_id: UUID
    relation_type: str
    source_record_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
