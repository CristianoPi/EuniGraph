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


class OpenAireSeedLoadResponse(BaseModel):
    dataset_path: str
    ingestion_run_id: str | None
    limit_per_file: int | None
    datasource_records: int
    organization_records: int
    publication_records: int
    project_records: int
    relation_records: int


class OpenAireSeedResetResponse(BaseModel):
    publication_author: int
    publication_organization: int
    external_identifier: int
    publication: int
    researcher: int
    organization: int
    source_record: int
    ingestion_run: int
    data_source: int
