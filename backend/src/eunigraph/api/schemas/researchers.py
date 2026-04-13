from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResearcherBase(BaseModel):
    full_name: str
    given_name: str | None = None
    family_name: str | None = None
    display_name: str | None = None
    orcid: str | None = None
    email: str | None = None
    profile_url: str | None = None
    primary_organization_id: UUID | None = None


class ResearcherCreate(ResearcherBase):
    pass


class ResearcherUpdate(BaseModel):
    full_name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    display_name: str | None = None
    orcid: str | None = None
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
