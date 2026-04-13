from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from eunigraph.core.config import Settings, get_settings
from eunigraph.persistence.postgres.session import create_session


def get_app_settings() -> Settings:
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    session = create_session()
    try:
        yield session
    finally:
        session.close()
