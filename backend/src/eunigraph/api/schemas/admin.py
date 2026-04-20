from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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
    researcher_affiliation: int
    external_identifier: int
    publication: int
    researcher: int
    organization: int
    source_record: int
    ingestion_run: int
    data_source: int


class OpenAireGraphEuniceSeedStatusResponse(BaseModel):
    api_base_url: str
    community_id: str
    product_type: str
    default_max_publications: int
    table_counts: dict[str, int]
    latest_ingestion_run_id: str | None
    latest_ingestion_status: str | None


class OpenAireGraphEuniceSeedLoadRequest(BaseModel):
    max_publications: int | None = Field(default=None, ge=1, le=2000)
    publication_year_from: int | None = Field(default=None, ge=1000, le=3000)
    publication_year_to: int | None = Field(default=None, ge=1000, le=3000)

    @model_validator(mode="after")
    def validate_year_range(self) -> OpenAireGraphEuniceSeedLoadRequest:
        if (
            self.publication_year_from is not None
            and self.publication_year_to is not None
            and self.publication_year_from > self.publication_year_to
        ):
            raise ValueError("publication_year_from cannot be greater than publication_year_to")
        return self


class OpenAireGraphEuniceSeedLoadResponse(BaseModel):
    api_base_url: str
    community_id: str
    ingestion_run_id: str | None
    max_publications: int | None
    publication_records_processed: int
    new_organizations: int
    new_researchers: int
    new_publications: int
    new_publication_organization_relations: int
    new_researcher_affiliations: int
    ambiguous_publications: int
