from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eunigraph.persistence.postgres.base import Base
from eunigraph.persistence.postgres.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class NormalizationRunModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "normalization_run"
    __table_args__ = (Index("ix_normalization_run_status", "status"),)

    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_by: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    raw_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    findings: Mapped[list[NormalizationFindingModel]] = relationship(
        back_populates="run",
    )


class NormalizationFindingModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "normalization_finding"
    __table_args__ = (
        Index("ix_normalization_finding_run_id", "run_id"),
        Index("ix_normalization_finding_entity_lookup", "entity_type", "entity_id"),
        Index("ix_normalization_finding_confidence", "confidence"),
    )

    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("normalization_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    candidate_entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False)
    auto_applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped[NormalizationRunModel] = relationship(back_populates="findings")
