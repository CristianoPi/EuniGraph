from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    name: str
    organization_type: str | None = None
    country_code: str | None = None
    city: str | None = None
    website: str | None = None
    parent_organization_id: UUID | None = None
    ror_id: str | None = None
    openaire_id: str | None = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    organization_type: str | None = None
    country_code: str | None = None
    city: str | None = None
    website: str | None = None
    parent_organization_id: UUID | None = None
    ror_id: str | None = None
    openaire_id: str | None = None


class OrganizationResponse(OrganizationBase):
    id: UUID
    normalized_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
