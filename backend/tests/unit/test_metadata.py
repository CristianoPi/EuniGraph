from __future__ import annotations

from eunigraph.persistence.postgres import models  # noqa: F401
from eunigraph.persistence.postgres.base import Base


def test_metadata_contains_initial_tables() -> None:
    expected_tables = {
        "data_source",
        "ingestion_run",
        "source_record",
        "organization",
        "researcher",
        "researcher_affiliation",
        "publication",
        "publication_author",
        "publication_organization",
        "external_identifier",
        "publication_embedding",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))
