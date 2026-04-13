from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eunigraph.persistence.postgres.base import Base
from eunigraph.persistence.postgres.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from eunigraph.modules.catalog.infrastructure.models import (
        ExternalIdentifierModel,
        PublicationAuthorModel,
        PublicationModel,
        PublicationOrganizationModel,
        ResearcherAffiliationModel,
    )


class DataSourceModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "data_source"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    ingestion_runs: Mapped[list[IngestionRunModel]] = relationship(back_populates="data_source")
    source_records: Mapped[list[SourceRecordModel]] = relationship(back_populates="data_source")


class IngestionRunModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_run"
    __table_args__ = (Index("ix_ingestion_run_data_source_status", "data_source_id", "status"),)

    data_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"),
        nullable=False,
    )
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

    data_source: Mapped[DataSourceModel] = relationship(back_populates="ingestion_runs")
    source_records: Mapped[list[SourceRecordModel]] = relationship(back_populates="ingestion_run")


class SourceRecordModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint(
            "ingestion_run_id",
            "entity_type",
            "source_identifier",
            name="uq_source_record_run_entity_identifier",
        ),
        Index(
            "ix_source_record_source_entity_identifier",
            "data_source_id",
            "entity_type",
            "source_identifier",
        ),
        Index("ix_source_record_checksum", "checksum"),
    )

    data_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingestion_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(100))
    checksum: Mapped[str | None] = mapped_column(String(128))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    data_source: Mapped[DataSourceModel] = relationship(back_populates="source_records")
    ingestion_run: Mapped[IngestionRunModel] = relationship(back_populates="source_records")
    canonical_publications: Mapped[list[PublicationModel]] = relationship(
        back_populates="canonical_source_record"
    )
    publication_authors: Mapped[list[PublicationAuthorModel]] = relationship(
        back_populates="source_record"
    )
    publication_organizations: Mapped[list[PublicationOrganizationModel]] = relationship(
        back_populates="source_record"
    )
    researcher_affiliations: Mapped[list[ResearcherAffiliationModel]] = relationship(
        back_populates="source_record"
    )
    external_identifiers: Mapped[list[ExternalIdentifierModel]] = relationship(
        back_populates="source_record"
    )
