from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PublicationBase(BaseModel):
    title: str = Field(min_length=1, max_length=2000)
    abstract: str | None = None
    publication_year: int | None = Field(default=None, ge=1000, le=3000)
    publication_date: date | None = None
    doi: str | None = Field(default=None, max_length=255)
    openaire_id: str | None = Field(default=None, max_length=255)
    publication_type: str | None = None
    language_code: str | None = None
    journal_name: str | None = None
    venue_name: str | None = None
    publisher: str | None = None
    open_access: bool | None = None
    source_url: str | None = None

    @field_validator("doi", "openaire_id", mode="before")
    @classmethod
    def normalize_optional_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=2000)
    abstract: str | None = None
    publication_year: int | None = Field(default=None, ge=1000, le=3000)
    publication_date: date | None = None
    doi: str | None = Field(default=None, max_length=255)
    openaire_id: str | None = Field(default=None, max_length=255)
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
    author_position: int = Field(ge=1)
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
    relation_type: str = Field(min_length=1, max_length=64)


class PublicationOrganizationResponse(BaseModel):
    id: UUID
    publication_id: UUID
    organization_id: UUID
    relation_type: str
    source_record_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
