from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eunigraph.persistence.postgres.base import Base
from eunigraph.persistence.postgres.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from eunigraph.modules.embeddings.infrastructure.models import PublicationEmbeddingModel
    from eunigraph.modules.ingestion.infrastructure.models import SourceRecordModel


class OrganizationModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organization"
    __table_args__ = (
        Index("ix_organization_normalized_name", "normalized_name"),
        Index("ix_organization_country_code", "country_code"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[str | None] = mapped_column(String(64))
    country_code: Mapped[str | None] = mapped_column(String(2))
    city: Mapped[str | None] = mapped_column(String(120))
    website: Mapped[str | None] = mapped_column(Text)
    parent_organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organization.id", ondelete="SET NULL")
    )
    ror_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    openaire_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    parent_organization: Mapped[OrganizationModel | None] = relationship(
        remote_side="OrganizationModel.id",
        back_populates="child_organizations",
    )
    child_organizations: Mapped[list[OrganizationModel]] = relationship(
        back_populates="parent_organization"
    )
    primary_researchers: Mapped[list[ResearcherModel]] = relationship(
        back_populates="primary_organization"
    )
    affiliations: Mapped[list[ResearcherAffiliationModel]] = relationship(
        back_populates="organization"
    )
    publications: Mapped[list[PublicationOrganizationModel]] = relationship(
        back_populates="organization"
    )


class ResearcherModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "researcher"
    __table_args__ = (Index("ix_researcher_normalized_name", "normalized_name"),)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    given_name: Mapped[str | None] = mapped_column(String(120))
    family_name: Mapped[str | None] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    orcid: Mapped[str | None] = mapped_column(String(19), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    profile_url: Mapped[str | None] = mapped_column(Text)
    primary_organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organization.id", ondelete="SET NULL")
    )

    primary_organization: Mapped[OrganizationModel | None] = relationship(
        back_populates="primary_researchers"
    )
    affiliations: Mapped[list[ResearcherAffiliationModel]] = relationship(
        back_populates="researcher"
    )
    authored_publications: Mapped[list[PublicationAuthorModel]] = relationship(
        back_populates="researcher"
    )


class ResearcherAffiliationModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "researcher_affiliation"
    __table_args__ = (
        Index("ix_researcher_affiliation_researcher_primary", "researcher_id", "is_primary"),
        Index("ix_researcher_affiliation_organization_id", "organization_id"),
    )

    researcher_id: Mapped[UUID] = mapped_column(
        ForeignKey("researcher.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_title: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    source_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("source_record.id", ondelete="SET NULL")
    )

    researcher: Mapped[ResearcherModel] = relationship(back_populates="affiliations")
    organization: Mapped[OrganizationModel] = relationship(back_populates="affiliations")
    source_record: Mapped[SourceRecordModel | None] = relationship(
        back_populates="researcher_affiliations"
    )


class PublicationModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publication"
    __table_args__ = (
        CheckConstraint(
            "publication_year IS NULL OR publication_year BETWEEN 1000 AND 3000",
            name="publication_year_range",
        ),
        Index("ix_publication_normalized_title", "normalized_title"),
        Index("ix_publication_publication_year", "publication_year"),
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(SmallInteger)
    publication_date: Mapped[date | None] = mapped_column(Date)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True)
    openaire_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    publication_type: Mapped[str | None] = mapped_column(String(64))
    language_code: Mapped[str | None] = mapped_column(String(16))
    journal_name: Mapped[str | None] = mapped_column(String(255))
    venue_name: Mapped[str | None] = mapped_column(String(255))
    publisher: Mapped[str | None] = mapped_column(String(255))
    open_access: Mapped[bool | None] = mapped_column(Boolean)
    source_url: Mapped[str | None] = mapped_column(Text)
    canonical_source_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("source_record.id", ondelete="SET NULL"),
        unique=True,
    )

    canonical_source_record: Mapped[SourceRecordModel | None] = relationship(
        back_populates="canonical_publications"
    )
    authors: Mapped[list[PublicationAuthorModel]] = relationship(back_populates="publication")
    organizations: Mapped[list[PublicationOrganizationModel]] = relationship(
        back_populates="publication"
    )
    embeddings: Mapped[list[PublicationEmbeddingModel]] = relationship(
        back_populates="publication"
    )


class PublicationAuthorModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "publication_author"
    __table_args__ = (
        UniqueConstraint("publication_id", "researcher_id", name="uq_publication_author_pair"),
        UniqueConstraint(
            "publication_id",
            "author_position",
            name="uq_publication_author_position",
        ),
        Index("ix_publication_author_researcher_id", "researcher_id"),
    )

    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("publication.id", ondelete="CASCADE"),
        nullable=False,
    )
    researcher_id: Mapped[UUID] = mapped_column(
        ForeignKey("researcher.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_position: Mapped[int] = mapped_column(Integer, nullable=False)
    author_list_name: Mapped[str | None] = mapped_column(String(255))
    is_corresponding: Mapped[bool | None] = mapped_column(Boolean)
    source_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("source_record.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    publication: Mapped[PublicationModel] = relationship(back_populates="authors")
    researcher: Mapped[ResearcherModel] = relationship(back_populates="authored_publications")
    source_record: Mapped[SourceRecordModel | None] = relationship(
        back_populates="publication_authors"
    )


class PublicationOrganizationModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "publication_organization"
    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "organization_id",
            "relation_type",
            name="uq_publication_organization_relation",
        ),
        Index("ix_publication_organization_organization_id", "organization_id"),
    )

    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("publication.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("source_record.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    publication: Mapped[PublicationModel] = relationship(back_populates="organizations")
    organization: Mapped[OrganizationModel] = relationship(back_populates="publications")
    source_record: Mapped[SourceRecordModel | None] = relationship(
        back_populates="publication_organizations"
    )


class ExternalIdentifierModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "external_identifier"
    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "identifier_type",
            "identifier_value",
            name="uq_external_identifier_value",
        ),
        Index("ix_external_identifier_entity_lookup", "entity_type", "entity_id"),
    )

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(64), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    source_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("source_record.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    source_record: Mapped[SourceRecordModel | None] = relationship(
        back_populates="external_identifiers"
    )
