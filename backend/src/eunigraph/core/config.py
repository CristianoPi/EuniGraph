from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    qdrant_url: str = Field(default="http://localhost:6333", alias="EUNIGRAPH_QDRANT_URL")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
