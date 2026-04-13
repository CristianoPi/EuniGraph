"""Add normalization run and finding tables.

Revision ID: 20260413_0002
Revises: 20260412_0001
Create Date: 2026-04-13 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_0002"
down_revision = "20260412_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "normalization_run",
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalization_run")),
    )
    op.create_index("ix_normalization_run_status", "normalization_run", ["status"], unique=False)

    op.create_table(
        "normalization_finding",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("finding_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.String(length=32), nullable=False),
        sa.Column("auto_applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["normalization_run.id"],
            name=op.f("fk_normalization_finding_run_id_normalization_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalization_finding")),
    )
    op.create_index(
        "ix_normalization_finding_run_id",
        "normalization_finding",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_normalization_finding_entity_lookup",
        "normalization_finding",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_normalization_finding_confidence",
        "normalization_finding",
        ["confidence"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_normalization_finding_confidence", table_name="normalization_finding")
    op.drop_index("ix_normalization_finding_entity_lookup", table_name="normalization_finding")
    op.drop_index("ix_normalization_finding_run_id", table_name="normalization_finding")
    op.drop_table("normalization_finding")
    op.drop_index("ix_normalization_run_status", table_name="normalization_run")
    op.drop_table("normalization_run")
