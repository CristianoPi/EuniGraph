"""Initial PostgreSQL schema for canonical OpenAIRE-aligned entities.

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "data_source",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_source")),
        sa.UniqueConstraint("name", name=op.f("uq_data_source_name")),
    )

    op.create_table(
        "organization",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("organization_type", sa.String(length=64), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("parent_organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ror_id", sa.String(length=255), nullable=True),
        sa.Column("openaire_id", sa.String(length=255), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_organization_id"],
            ["organization.id"],
            name=op.f("fk_organization_parent_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization")),
        sa.UniqueConstraint("openaire_id", name=op.f("uq_organization_openaire_id")),
        sa.UniqueConstraint("ror_id", name=op.f("uq_organization_ror_id")),
    )
    op.create_index("ix_organization_country_code", "organization", ["country_code"], unique=False)
    op.create_index("ix_organization_normalized_name", "organization", ["normalized_name"], unique=False)

    op.create_table(
        "ingestion_run",
        sa.Column("data_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["data_source_id"],
            ["data_source.id"],
            name=op.f("fk_ingestion_run_data_source_id_data_source"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_run")),
    )
    op.create_index(
        "ix_ingestion_run_data_source_status",
        "ingestion_run",
        ["data_source_id", "status"],
        unique=False,
    )

    op.create_table(
        "researcher",
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("given_name", sa.String(length=120), nullable=True),
        sa.Column("family_name", sa.String(length=120), nullable=True),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("orcid", sa.String(length=19), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("profile_url", sa.Text(), nullable=True),
        sa.Column("primary_organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["primary_organization_id"],
            ["organization.id"],
            name=op.f("fk_researcher_primary_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_researcher")),
        sa.UniqueConstraint("orcid", name=op.f("uq_researcher_orcid")),
    )
    op.create_index("ix_researcher_normalized_name", "researcher", ["normalized_name"], unique=False)

    op.create_table(
        "source_record",
        sa.Column("data_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_identifier", sa.String(length=255), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["data_source_id"],
            ["data_source.id"],
            name=op.f("fk_source_record_data_source_id_data_source"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_run.id"],
            name=op.f("fk_source_record_ingestion_run_id_ingestion_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_record")),
        sa.UniqueConstraint(
            "ingestion_run_id",
            "entity_type",
            "source_identifier",
            name="uq_source_record_run_entity_identifier",
        ),
    )
    op.create_index("ix_source_record_checksum", "source_record", ["checksum"], unique=False)
    op.create_index(
        "ix_source_record_source_entity_identifier",
        "source_record",
        ["data_source_id", "entity_type", "source_identifier"],
        unique=False,
    )

    op.create_table(
        "publication",
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("publication_year", sa.SmallInteger(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("doi", sa.String(length=255), nullable=True),
        sa.Column("openaire_id", sa.String(length=255), nullable=True),
        sa.Column("publication_type", sa.String(length=64), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("journal_name", sa.String(length=255), nullable=True),
        sa.Column("venue_name", sa.String(length=255), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("open_access", sa.Boolean(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("canonical_source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "publication_year IS NULL OR publication_year BETWEEN 1000 AND 3000",
            name=op.f("ck_publication_publication_year_range"),
        ),
        sa.ForeignKeyConstraint(
            ["canonical_source_record_id"],
            ["source_record.id"],
            name=op.f("fk_publication_canonical_source_record_id_source_record"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publication")),
        sa.UniqueConstraint(
            "canonical_source_record_id",
            name=op.f("uq_publication_canonical_source_record_id"),
        ),
        sa.UniqueConstraint("doi", name=op.f("uq_publication_doi")),
        sa.UniqueConstraint("openaire_id", name=op.f("uq_publication_openaire_id")),
    )
    op.create_index("ix_publication_normalized_title", "publication", ["normalized_title"], unique=False)
    op.create_index("ix_publication_publication_year", "publication", ["publication_year"], unique=False)

    op.create_table(
        "external_identifier",
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identifier_type", sa.String(length=64), nullable=False),
        sa.Column("identifier_value", sa.String(length=255), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["source_record.id"],
            name=op.f("fk_external_identifier_source_record_id_source_record"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_external_identifier")),
        sa.UniqueConstraint(
            "entity_type",
            "identifier_type",
            "identifier_value",
            name="uq_external_identifier_value",
        ),
    )
    op.create_index(
        "ix_external_identifier_entity_lookup",
        "external_identifier",
        ["entity_type", "entity_id"],
        unique=False,
    )

    op.create_table(
        "publication_author",
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("researcher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_position", sa.Integer(), nullable=False),
        sa.Column("author_list_name", sa.String(length=255), nullable=True),
        sa.Column("is_corresponding", sa.Boolean(), nullable=True),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["publication.id"],
            name=op.f("fk_publication_author_publication_id_publication"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["researcher_id"],
            ["researcher.id"],
            name=op.f("fk_publication_author_researcher_id_researcher"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["source_record.id"],
            name=op.f("fk_publication_author_source_record_id_source_record"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publication_author")),
        sa.UniqueConstraint("publication_id", "author_position", name="uq_publication_author_position"),
        sa.UniqueConstraint("publication_id", "researcher_id", name="uq_publication_author_pair"),
    )
    op.create_index(
        "ix_publication_author_researcher_id", "publication_author", ["researcher_id"], unique=False
    )

    op.create_table(
        "publication_embedding",
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qdrant_collection", sa.String(length=128), nullable=False),
        sa.Column("qdrant_point_id", sa.String(length=255), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("embedding_version", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["publication.id"],
            name=op.f("fk_publication_embedding_publication_id_publication"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publication_embedding")),
        sa.UniqueConstraint(
            "publication_id",
            "embedding_model",
            "embedding_version",
            name="uq_publication_embedding_version",
        ),
        sa.UniqueConstraint(
            "qdrant_collection",
            "qdrant_point_id",
            name="uq_publication_embedding_qdrant_point",
        ),
    )
    op.create_index(
        "ix_publication_embedding_publication_id",
        "publication_embedding",
        ["publication_id"],
        unique=False,
    )

    op.create_table(
        "publication_organization",
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_publication_organization_organization_id_organization"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["publication.id"],
            name=op.f("fk_publication_organization_publication_id_publication"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["source_record.id"],
            name=op.f("fk_publication_organization_source_record_id_source_record"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publication_organization")),
        sa.UniqueConstraint(
            "publication_id",
            "organization_id",
            "relation_type",
            name="uq_publication_organization_relation",
        ),
    )
    op.create_index(
        "ix_publication_organization_organization_id",
        "publication_organization",
        ["organization_id"],
        unique=False,
    )

    op.create_table(
        "researcher_affiliation",
        sa.Column("researcher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_title", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_researcher_affiliation_organization_id_organization"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["researcher_id"],
            ["researcher.id"],
            name=op.f("fk_researcher_affiliation_researcher_id_researcher"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["source_record.id"],
            name=op.f("fk_researcher_affiliation_source_record_id_source_record"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_researcher_affiliation")),
    )
    op.create_index(
        "ix_researcher_affiliation_organization_id",
        "researcher_affiliation",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_researcher_affiliation_researcher_primary",
        "researcher_affiliation",
        ["researcher_id", "is_primary"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_researcher_affiliation_researcher_primary", table_name="researcher_affiliation")
    op.drop_index("ix_researcher_affiliation_organization_id", table_name="researcher_affiliation")
    op.drop_table("researcher_affiliation")

    op.drop_index("ix_publication_organization_organization_id", table_name="publication_organization")
    op.drop_table("publication_organization")

    op.drop_index("ix_publication_embedding_publication_id", table_name="publication_embedding")
    op.drop_table("publication_embedding")

    op.drop_index("ix_publication_author_researcher_id", table_name="publication_author")
    op.drop_table("publication_author")

    op.drop_index("ix_external_identifier_entity_lookup", table_name="external_identifier")
    op.drop_table("external_identifier")

    op.drop_index("ix_publication_publication_year", table_name="publication")
    op.drop_index("ix_publication_normalized_title", table_name="publication")
    op.drop_table("publication")

    op.drop_index("ix_source_record_source_entity_identifier", table_name="source_record")
    op.drop_index("ix_source_record_checksum", table_name="source_record")
    op.drop_table("source_record")

    op.drop_index("ix_researcher_normalized_name", table_name="researcher")
    op.drop_table("researcher")

    op.drop_index("ix_ingestion_run_data_source_status", table_name="ingestion_run")
    op.drop_table("ingestion_run")

    op.drop_index("ix_organization_normalized_name", table_name="organization")
    op.drop_index("ix_organization_country_code", table_name="organization")
    op.drop_table("organization")

    op.drop_table("data_source")
