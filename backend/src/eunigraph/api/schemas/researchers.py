from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ResearcherBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    given_name: str | None = None
    family_name: str | None = None
    display_name: str | None = None
    orcid: str | None = Field(default=None, max_length=19)
    email: str | None = None
    profile_url: str | None = None
    primary_organization_id: UUID | None = None

    @field_validator("orcid", mode="before")
    @classmethod
    def normalize_orcid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ResearcherCreate(ResearcherBase):
    pass


class ResearcherUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    given_name: str | None = None
    family_name: str | None = None
    display_name: str | None = None
    orcid: str | None = Field(default=None, max_length=19)
    email: str | None = None
    profile_url: str | None = None
    primary_organization_id: UUID | None = None

class ResearcherResponse(ResearcherBase):
    id: UUID
    normalized_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearcherAffiliationCreate(BaseModel):
    organization_id: UUID
    role_title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_primary: bool = False

    @model_validator(mode="after")
    def validate_date_range(self) -> ResearcherAffiliationCreate:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class ResearcherAffiliationResponse(BaseModel):
    id: UUID
    researcher_id: UUID
    organization_id: UUID
    role_title: str | None
    start_date: date | None
    end_date: date | None
    is_primary: bool
    source_record_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
