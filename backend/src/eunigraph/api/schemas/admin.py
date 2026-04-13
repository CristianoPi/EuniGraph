from __future__ import annotations

from pydantic import BaseModel


class OpenAireSeedLoadRequest(BaseModel):
    limit_per_file: int | None = None


class OpenAireSeedStatusResponse(BaseModel):
    dataset_path: str
    dataset_path_exists: bool
    required_files: dict[str, bool]
    table_counts: dict[str, int]
    latest_ingestion_run_id: str | None
    latest_ingestion_status: str | None
