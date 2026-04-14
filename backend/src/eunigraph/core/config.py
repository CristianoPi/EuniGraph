from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

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
    openaire_beginners_kit_path: Path = Field(
        default=Path("./data/openaire/beginners_kit"),
        alias="OPENAIRE_BEGINNERS_KIT_PATH",
    )
    coauthorship_graph_storage_path: Path = Field(
        default=Path("./data/graphs/coauthorship"),
        alias="EUNIGRAPH_COAUTHORSHIP_GRAPH_STORAGE_PATH",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
