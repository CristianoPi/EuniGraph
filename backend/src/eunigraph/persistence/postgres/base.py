from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

from eunigraph.persistence.postgres.mixins import metadata


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""

    metadata = metadata
