from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceRecordResponse(BaseModel):
    id: UUID
    data_source_id: UUID
    ingestion_run_id: UUID
    entity_type: str
    source_identifier: str
    source_version: str | None
    checksum: str | None
    raw_payload: dict[str, Any]
    ingested_at: datetime

    model_config = ConfigDict(from_attributes=True)
