from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eunigraph.modules.catalog.infrastructure.models import PublicationModel
from eunigraph.persistence.postgres.base import Base
from eunigraph.persistence.postgres.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PublicationEmbeddingModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publication_embedding"
    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "embedding_model",
            "embedding_version",
            name="uq_publication_embedding_version",
        ),
        UniqueConstraint(
            "qdrant_collection",
            "qdrant_point_id",
            name="uq_publication_embedding_qdrant_point",
        ),
        Index("ix_publication_embedding_publication_id", "publication_id"),
    )

    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("publication.id", ondelete="CASCADE"),
        nullable=False,
    )
    qdrant_collection: Mapped[str] = mapped_column(String(128), nullable=False)
    qdrant_point_id: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    publication: Mapped[PublicationModel] = relationship(back_populates="embeddings")
