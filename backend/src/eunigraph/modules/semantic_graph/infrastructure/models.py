from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from eunigraph.persistence.postgres.base import Base
from eunigraph.persistence.postgres.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SemanticGraphBuildModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semantic_graph_build"
    __table_args__ = (
        Index("ix_semantic_graph_build_status", "status"),
        Index("ix_semantic_graph_build_active", "graph_type", "is_active"),
        Index("ix_semantic_graph_build_started_at", "started_at"),
    )

    graph_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="semantic_similarity",
        server_default="semantic_similarity",
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_by: Mapped[str | None] = mapped_column(String(100))
    build_params: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    data_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    artifact_paths: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    graph_version: Mapped[str | None] = mapped_column(String(64))
    node_count: Mapped[int | None] = mapped_column(Integer)
    edge_count: Mapped[int | None] = mapped_column(Integer)
    component_count: Mapped[int | None] = mapped_column(Integer)
    community_count: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    error_message: Mapped[str | None] = mapped_column(Text)
