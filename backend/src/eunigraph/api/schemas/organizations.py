from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrganizationBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    organization_type: str | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = None
    website: str | None = None
    parent_organization_id: UUID | None = None
    ror_id: str | None = Field(default=None, max_length=255)
    openaire_id: str | None = Field(default=None, max_length=255)

    @field_validator("country_code", mode="before")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    organization_type: str | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = None
    website: str | None = None
    parent_organization_id: UUID | None = None
    ror_id: str | None = Field(default=None, max_length=255)
    openaire_id: str | None = Field(default=None, max_length=255)

class OrganizationResponse(OrganizationBase):
    id: UUID
    normalized_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
