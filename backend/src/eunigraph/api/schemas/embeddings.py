from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingsBuildRequest(BaseModel):
    publication_ids: list[UUID] | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)
    force: bool = False


class PublicationEmbeddingBuildRequest(BaseModel):
    force: bool = False


class EmbeddingsLoadAllRequest(BaseModel):
    force: bool = False


class EmbeddingsResetResponse(BaseModel):
    collection_name: str
    collection_deleted: bool
    deleted_metadata_count: int
    provider: str
    model: str
    embedding_version: str


class PublicationEmbeddingBuildOutcomeResponse(BaseModel):
    publication_id: UUID
    status: str
    reason: str | None
    embedding_id: UUID | None
    qdrant_point_id: str | None


class EmbeddingsBuildResponse(BaseModel):
    provider: str
    model: str
    embedding_version: str
    collection_name: str
    processed_count: int
    generated_count: int
    skipped_count: int
    failed_count: int
    results: list[PublicationEmbeddingBuildOutcomeResponse]


class PublicationEmbeddingResponse(BaseModel):
    id: UUID
    publication_id: UUID
    embedding_provider: str
    qdrant_collection: str
    qdrant_point_id: str
    embedding_model: str
    embedding_version: str
    content_hash: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmbeddingsProviderResponse(BaseModel):
    enabled: bool
    provider: str
    model: str
    embedding_version: str
    batch_size: int
    request_timeout_seconds: int
    max_retries: int
    content_fields: tuple[str, ...]
    qdrant_collection: str
    qdrant_api_key_configured: bool
    gemini_api_key_configured: bool


class EmbeddingsStatusResponse(BaseModel):
    enabled: bool
    provider: str
    model: str
    embedding_version: str
    qdrant_collection: str
    qdrant_collection_exists: bool
    qdrant_points_count: int
    qdrant_collection_status: str | None
    total_publications: int
    active_embeddings_count: int
    latest_embedding_updated_at: datetime | None
