from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from eunigraph.core.config import get_settings
from eunigraph.persistence.postgres import models  # noqa: F401

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def create_session() -> Session:
    return SessionLocal()
