from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NormalizationRunRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class NormalizationRunResponse(BaseModel):
    run_id: UUID
    status: str
    normalized_publications: int
    normalized_researchers: int
    normalized_organizations: int
    auto_merged_publications: int
    auto_merged_researchers: int
    auto_merged_organizations: int
    findings_count: int
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class NormalizationFindingResponse(BaseModel):
    id: UUID
    run_id: UUID
    entity_type: str
    entity_id: UUID | None
    candidate_entity_id: UUID | None
    finding_type: str
    confidence: str
    auto_applied: bool
    message: str
    details: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
