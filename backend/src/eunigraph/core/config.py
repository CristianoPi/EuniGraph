from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="EuniGraph", alias="EUNIGRAPH_APP_NAME")
    env: str = Field(default="development", alias="EUNIGRAPH_ENV")
    log_level: str = Field(default="INFO", alias="EUNIGRAPH_LOG_LEVEL")
    api_v1_prefix: str = Field(default="/api/v1", alias="EUNIGRAPH_API_V1_PREFIX")
    docs_enabled: bool = Field(default=True, alias="EUNIGRAPH_DOCS_ENABLED")
    database_url: str = Field(
        default="postgresql+psycopg://eunigraph:eunigraph@localhost:5432/eunigraph",
        alias="EUNIGRAPH_DATABASE_URL",
    )
    qdrant_url: str = Field(
        default="http://localhost:6333",
        validation_alias=AliasChoices("QDRANT_URL", "EUNIGRAPH_QDRANT_URL"),
    )
    qdrant_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("QDRANT_API_KEY", "EUNIGRAPH_QDRANT_API_KEY"),
    )
    qdrant_collection_publications: str = Field(
        default="publication_embeddings",
        alias="QDRANT_COLLECTION_PUBLICATIONS",
    )
    embeddings_enabled: bool = Field(default=True, alias="EMBEDDINGS_ENABLED")
    embeddings_provider: str = Field(default="gemini", alias="EMBEDDINGS_PROVIDER")
    embeddings_model: str = Field(default="gemini-embedding-001", alias="EMBEDDINGS_MODEL")
    embeddings_version: str = Field(default="v1", alias="EMBEDDINGS_VERSION")
    embeddings_batch_size: int = Field(default=16, alias="EMBEDDINGS_BATCH_SIZE")
    embeddings_request_timeout_seconds: int = Field(
        default=60,
        alias="EMBEDDINGS_REQUEST_TIMEOUT_SECONDS",
    )
    embeddings_max_retries: int = Field(default=3, alias="EMBEDDINGS_MAX_RETRIES")
    embeddings_content_fields: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("title", "authors", "abstract"),
        alias="EMBEDDINGS_CONTENT_FIELDS",
    )
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openaire_beginners_kit_path: Path = Field(
        default=Path("./data/openaire/beginners_kit"),
        alias="OPENAIRE_BEGINNERS_KIT_PATH",
    )
    openaire_graph_api_base_url: str = Field(
        default="https://api.openaire.eu/graph",
        alias="OPENAIRE_GRAPH_API_BASE_URL",
    )
    openaire_graph_api_timeout_seconds: int = Field(
        default=30,
        alias="OPENAIRE_GRAPH_API_TIMEOUT_SECONDS",
    )
    openaire_graph_api_page_size: int = Field(
        default=25,
        alias="OPENAIRE_GRAPH_API_PAGE_SIZE",
    )
    openaire_eunice_seed_max_publications_per_organization: int = Field(
        default=50,
        alias="OPENAIRE_EUNICE_SEED_MAX_PUBLICATIONS_PER_ORGANIZATION",
    )
    coauthorship_graph_storage_path: Path = Field(
        default=Path("./data/graphs/coauthorship"),
        alias="EUNIGRAPH_COAUTHORSHIP_GRAPH_STORAGE_PATH",
    )
    semantic_graph_storage_path: Path = Field(
        default=Path("./data/graphs/semantic"),
        alias="EUNIGRAPH_SEMANTIC_GRAPH_STORAGE_PATH",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "qdrant_api_key",
        "gemini_api_key",
        mode="before",
    )
    @classmethod
    def normalize_optional_secrets(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator(
        "embeddings_provider",
        "embeddings_model",
        "embeddings_version",
        "openaire_graph_api_base_url",
        mode="before",
    )
    @classmethod
    def normalize_embedding_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("embeddings_content_fields", mode="before")
    @classmethod
    def parse_embeddings_content_fields(
        cls,
        value: str | tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        if isinstance(value, str):
            fields = tuple(
                item.strip().lower()
                for item in value.split(",")
                if item.strip()
            )
            return fields or ("title", "authors", "abstract")
        if isinstance(value, list):
            return tuple(item.strip().lower() for item in value if item.strip())
        return tuple(item.strip().lower() for item in value if item.strip())

    def model_post_init(self, __context: Any) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        if not self.openaire_beginners_kit_path.is_absolute():
            self.openaire_beginners_kit_path = (
                repo_root / self.openaire_beginners_kit_path
            ).resolve()
        if not self.coauthorship_graph_storage_path.is_absolute():
            self.coauthorship_graph_storage_path = (
                repo_root / self.coauthorship_graph_storage_path
            ).resolve()
        if not self.semantic_graph_storage_path.is_absolute():
            self.semantic_graph_storage_path = (
                repo_root / self.semantic_graph_storage_path
            ).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
