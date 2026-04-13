from __future__ import annotations

from collections.abc import Iterable
from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    ResearcherModel,
)
from eunigraph.modules.normalization.application import (
    MANUAL_REVIEW_NEEDED,
    POSSIBLE_MATCH,
    NormalizationService,
)
from eunigraph.modules.normalization.infrastructure.models import (
    NormalizationFindingModel,
    NormalizationRunModel,
)
from eunigraph.shared.utils import normalize_text


class FakeSession:
    def __init__(self, values: Iterable[object]) -> None:
        self._values = list(values)
        self.added: list[object] = []

    def scalars(self, _query: object) -> list[object]:
        return self._values

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        return None


def test_normalize_text_handles_unicode_spacing_and_punctuation() -> None:
    assert normalize_text("  Università  di   Torino! ") == "universita di torino"
    assert normalize_text("Smash: Flexible, Fast.") == "smash flexible fast"


def test_clean_text_value_preserves_readable_text_while_trimming() -> None:
    service = NormalizationService(MagicMock())

    assert service._clean_text_value("  Ada   Lovelace  ") == "Ada Lovelace"
    assert service._clean_text_value("Université\tde Turin") == "Université de Turin"


def test_publication_author_overlap_uses_normalized_researcher_names() -> None:
    left_author = PublicationAuthorModel(
        author_position=1,
        researcher=ResearcherModel(full_name="Ada Lovelace", normalized_name="ada lovelace"),
    )
    right_author = PublicationAuthorModel(
        author_position=1,
        researcher=ResearcherModel(full_name="Ada  Lovelace", normalized_name="ada lovelace"),
    )
    left = PublicationModel(title="Left", normalized_title="left")
    right = PublicationModel(title="Right", normalized_title="right")
    left.authors = [left_author]
    right.authors = [right_author]

    service = NormalizationService(MagicMock())

    assert service._publication_author_overlap(left, right) == 1


def test_can_merge_publications_rejects_position_conflicts() -> None:
    target = PublicationModel(title="Target", normalized_title="target")
    candidate = PublicationModel(title="Candidate", normalized_title="candidate")

    target.authors = [
        PublicationAuthorModel(
            author_position=1,
            researcher_id=uuid4(),
        ),
    ]
    candidate.authors = [
        PublicationAuthorModel(
            author_position=1,
            researcher_id=uuid4(),
        ),
    ]

    service = NormalizationService(MagicMock())

    assert service._can_merge_publications(target, candidate) is False


def test_record_anomalies_creates_findings_for_malformed_and_incomplete_records() -> None:
    publication = PublicationModel(
        id=uuid4(),
        title="Untitled",
        normalized_title="untitled",
        doi="bad-doi",
    )
    researcher = ResearcherModel(
        id=uuid4(),
        full_name="Ada",
        normalized_name="ada",
        orcid="bad-orcid",
    )
    organization = OrganizationModel(
        id=uuid4(),
        name="Uni Torino",
        normalized_name="uni torino",
        ror_id="bad-ror",
    )
    session = FakeSession([publication])
    service = NormalizationService(cast(Session, session))

    publication_findings = service._record_publication_anomalies(uuid4())

    assert publication_findings == 1
    assert all(isinstance(item, NormalizationFindingModel) for item in session.added)

    session = FakeSession([researcher])
    service = NormalizationService(cast(Session, session))
    researcher_findings = service._record_researcher_anomalies(uuid4())
    assert researcher_findings == 2

    session = FakeSession([organization])
    service = NormalizationService(cast(Session, session))
    organization_findings = service._record_organization_anomalies(uuid4())
    assert organization_findings == 1


def test_to_summary_maps_json_summary_to_response_shape() -> None:
    service = NormalizationService(MagicMock())
    run = NormalizationRunModel(id=uuid4(), status="completed")
    summary = service._to_summary(
        run,
        {
            "normalized_publications": 1,
            "normalized_researchers": 2,
            "normalized_organizations": 3,
            "auto_merged_publications": 4,
            "auto_merged_researchers": 5,
            "auto_merged_organizations": 6,
            "findings_count": 7,
        },
    )

    assert summary.status == "completed"
    assert summary.findings_count == 7
    assert summary.auto_merged_publications == 4
    assert POSSIBLE_MATCH == "possible_match"
    assert MANUAL_REVIEW_NEEDED == "manual_review_needed"
