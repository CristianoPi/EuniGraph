"""Add embedding provider metadata to publication_embedding.

Revision ID: 20260414_0004
Revises: 20260413_0003
Create Date: 2026-04-14 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260414_0004"
down_revision = "20260413_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "publication_embedding",
        sa.Column("embedding_provider", sa.String(length=64), nullable=True),
    )
    op.execute(
        "UPDATE publication_embedding SET embedding_provider = 'unknown' "
        "WHERE embedding_provider IS NULL"
    )
    op.alter_column(
        "publication_embedding",
        "embedding_provider",
        nullable=False,
    )
    op.drop_constraint(
        "uq_publication_embedding_version",
        "publication_embedding",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_publication_embedding_version",
        "publication_embedding",
        ["publication_id", "embedding_provider", "embedding_model", "embedding_version"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_publication_embedding_version",
        "publication_embedding",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_publication_embedding_version",
        "publication_embedding",
        ["publication_id", "embedding_model", "embedding_version"],
    )
    op.drop_column("publication_embedding", "embedding_provider")
