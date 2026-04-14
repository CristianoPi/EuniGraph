"""Add semantic graph build tracking table.

Revision ID: 20260414_0005
Revises: 20260414_0004
Create Date: 2026-04-14 00:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260414_0005"
down_revision = "20260414_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "semantic_graph_build",
        sa.Column(
            "graph_type",
            sa.String(length=64),
            server_default=sa.text("'semantic_similarity'"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", sa.String(length=100), nullable=True),
        sa.Column("build_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("data_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("artifact_paths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("graph_version", sa.String(length=64), nullable=True),
        sa.Column("node_count", sa.Integer(), nullable=True),
        sa.Column("edge_count", sa.Integer(), nullable=True),
        sa.Column("component_count", sa.Integer(), nullable=True),
        sa.Column("community_count", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_semantic_graph_build")),
    )
    op.create_index(
        "ix_semantic_graph_build_status",
        "semantic_graph_build",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_semantic_graph_build_active",
        "semantic_graph_build",
        ["graph_type", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_semantic_graph_build_started_at",
        "semantic_graph_build",
        ["started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_semantic_graph_build_started_at", table_name="semantic_graph_build")
    op.drop_index("ix_semantic_graph_build_active", table_name="semantic_graph_build")
    op.drop_index("ix_semantic_graph_build_status", table_name="semantic_graph_build")
    op.drop_table("semantic_graph_build")
