from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from eunigraph.modules.catalog.infrastructure.models import (
    ExternalIdentifierModel,
    OrganizationModel,
    PublicationAuthorModel,
    PublicationModel,
    PublicationOrganizationModel,
    ResearcherModel,
)
from eunigraph.modules.embeddings.infrastructure.models import PublicationEmbeddingModel
from eunigraph.modules.normalization.infrastructure.models import (
    NormalizationFindingModel,
    NormalizationRunModel,
)
from eunigraph.shared.utils import normalize_text

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:a-z0-9]+$", re.IGNORECASE)
ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", re.IGNORECASE)
ROR_PATTERN = re.compile(r"^https://ror\.org/[a-z0-9]{9}$", re.IGNORECASE)

EXACT_MATCH = "exact_match"
STRONG_MATCH = "strong_match"
POSSIBLE_MATCH = "possible_match"
MANUAL_REVIEW_NEEDED = "manual_review_needed"


@dataclass(slots=True)
class NormalizationRunSummary:
    run_id: UUID
    status: str
    normalized_publications: int
    normalized_researchers: int
    normalized_organizations: int
    auto_merged_publications: int
    auto_merged_researchers: int
    auto_merged_organizations: int
    findings_count: int
    completed_at: datetime | None


class NormalizationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_summary(self) -> NormalizationRunSummary | None:
        run = self.session.scalar(
            select(NormalizationRunModel).order_by(
                NormalizationRunModel.started_at.desc(),
            ).limit(1),
        )
        if run is None:
            return None
        summary = run.summary or {}
        return self._to_summary(run, summary)

    def list_findings(
        self,
        *,
        run_id: UUID | None = None,
        entity_type: str | None = None,
        confidence: str | None = None,
        auto_applied: bool | None = None,
        limit: int = 100,
    ) -> list[NormalizationFindingModel]:
        query = select(NormalizationFindingModel).order_by(
            NormalizationFindingModel.created_at.desc(),
        )
        if run_id is not None:
            query = query.where(NormalizationFindingModel.run_id == run_id)
        if entity_type:
            query = query.where(NormalizationFindingModel.entity_type == entity_type)
        if confidence:
            query = query.where(NormalizationFindingModel.confidence == confidence)
        if auto_applied is not None:
            query = query.where(NormalizationFindingModel.auto_applied == auto_applied)
        return list(self.session.scalars(query.limit(limit)))

    def run(
        self,
        *,
        triggered_by: str = "admin-api",
        notes: str | None = None,
    ) -> NormalizationRunSummary:
        run = NormalizationRunModel(
            status="running",
            triggered_by=triggered_by,
            notes=notes,
        )
        self.session.add(run)
        self.session.flush()

        counters = {
            "normalized_publications": 0,
            "normalized_researchers": 0,
            "normalized_organizations": 0,
            "auto_merged_publications": 0,
            "auto_merged_researchers": 0,
            "auto_merged_organizations": 0,
            "findings_count": 0,
        }

        try:
            counters["normalized_publications"] = self._normalize_publications()
            counters["normalized_researchers"] = self._normalize_researchers()
            counters["normalized_organizations"] = self._normalize_organizations()

            counters["findings_count"] += self._record_publication_anomalies(run.id)
            counters["findings_count"] += self._record_researcher_anomalies(run.id)
            counters["findings_count"] += self._record_organization_anomalies(run.id)

            merged_publications, publication_findings = self._deduplicate_publications(
                run.id,
            )
            counters["auto_merged_publications"] = merged_publications
            counters["findings_count"] += publication_findings

            merged_researchers, researcher_findings = self._deduplicate_researchers(
                run.id,
            )
            counters["auto_merged_researchers"] = merged_researchers
            counters["findings_count"] += researcher_findings

            merged_organizations, organization_findings = self._deduplicate_organizations(
                run.id,
            )
            counters["auto_merged_organizations"] = merged_organizations
            counters["findings_count"] += organization_findings

            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.summary = counters
            self.session.commit()
        except Exception:
            self.session.rollback()
            failed_run = self.session.get(NormalizationRunModel, run.id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.completed_at = datetime.now(UTC)
                self.session.commit()
            raise

        self.session.refresh(run)
        return self._to_summary(run, counters)

    def _normalize_publications(self) -> int:
        count = 0
        for publication in self.session.scalars(select(PublicationModel)):
            changed = False
            clean_title = self._clean_text_value(publication.title)
            if clean_title != publication.title:
                publication.title = clean_title or publication.title
                changed = True
            normalized_title = normalize_text(clean_title)
            if normalized_title != publication.normalized_title:
                publication.normalized_title = normalized_title
                changed = True
            clean_journal = self._clean_text_value(publication.journal_name)
            if clean_journal != publication.journal_name:
                publication.journal_name = clean_journal
                changed = True
            clean_venue = self._clean_text_value(publication.venue_name)
            if clean_venue != publication.venue_name:
                publication.venue_name = clean_venue
                changed = True
            if changed:
                count += 1
        self.session.flush()
        return count

    def _normalize_researchers(self) -> int:
        count = 0
        for researcher in self.session.scalars(select(ResearcherModel)):
            changed = False
            clean_full_name = self._clean_text_value(researcher.full_name)
            if clean_full_name != researcher.full_name:
                researcher.full_name = clean_full_name or researcher.full_name
                changed = True
            normalized_name = normalize_text(clean_full_name)
            if normalized_name != researcher.normalized_name:
                researcher.normalized_name = normalized_name
                changed = True
            clean_display_name = self._clean_text_value(researcher.display_name)
            if clean_display_name != researcher.display_name:
                researcher.display_name = clean_display_name
                changed = True
            if changed:
                count += 1
        self.session.flush()
        return count

    def _normalize_organizations(self) -> int:
        count = 0
        for organization in self.session.scalars(select(OrganizationModel)):
            changed = False
            clean_name = self._clean_text_value(organization.name)
            if clean_name != organization.name:
                organization.name = clean_name or organization.name
                changed = True
            normalized_name = normalize_text(clean_name)
            if normalized_name != organization.normalized_name:
                organization.normalized_name = normalized_name
                changed = True
            clean_city = self._clean_text_value(organization.city)
            if clean_city != organization.city:
                organization.city = clean_city
                changed = True
            if changed:
                count += 1
        self.session.flush()
        return count

    def _record_publication_anomalies(self, run_id: UUID) -> int:
        findings = 0
        for publication in self.session.scalars(select(PublicationModel)):
            if (
                not publication.doi
                and not publication.openaire_id
                and publication.publication_year is None
            ):
                self._add_finding(
                    run_id=run_id,
                    entity_type="publication",
                    entity_id=publication.id,
                    finding_type="incomplete_record",
                    confidence=MANUAL_REVIEW_NEEDED,
                    auto_applied=False,
                    message="Publication is missing stable identifiers and publication year",
                    details={"title": publication.title},
                )
                findings += 1
            if publication.doi and not DOI_PATTERN.match(publication.doi):
                self._add_finding(
                    run_id=run_id,
                    entity_type="publication",
                    entity_id=publication.id,
                    finding_type="malformed_identifier",
                    confidence=MANUAL_REVIEW_NEEDED,
                    auto_applied=False,
                    message="Publication DOI appears malformed",
                    details={"doi": publication.doi},
                )
                findings += 1
        return findings

    def _record_researcher_anomalies(self, run_id: UUID) -> int:
        findings = 0
        for researcher in self.session.scalars(select(ResearcherModel)):
            if researcher.orcid and not ORCID_PATTERN.match(researcher.orcid):
                self._add_finding(
                    run_id=run_id,
                    entity_type="researcher",
                    entity_id=researcher.id,
                    finding_type="malformed_identifier",
                    confidence=MANUAL_REVIEW_NEEDED,
                    auto_applied=False,
                    message="Researcher ORCID appears malformed",
                    details={"orcid": researcher.orcid},
                )
                findings += 1
            if len(researcher.normalized_name.split()) < 2:
                self._add_finding(
                    run_id=run_id,
                    entity_type="researcher",
                    entity_id=researcher.id,
                    finding_type="incomplete_record",
                    confidence=POSSIBLE_MATCH,
                    auto_applied=False,
                    message="Researcher name is weak for stable matching",
                    details={"full_name": researcher.full_name},
                )
                findings += 1
        return findings

    def _record_organization_anomalies(self, run_id: UUID) -> int:
        findings = 0
        for organization in self.session.scalars(select(OrganizationModel)):
            if organization.ror_id and not ROR_PATTERN.match(organization.ror_id):
                self._add_finding(
                    run_id=run_id,
                    entity_type="organization",
                    entity_id=organization.id,
                    finding_type="malformed_identifier",
                    confidence=MANUAL_REVIEW_NEEDED,
                    auto_applied=False,
                    message="Organization ROR identifier appears malformed",
                    details={"ror_id": organization.ror_id},
                )
                findings += 1
            if not organization.normalized_name:
                self._add_finding(
                    run_id=run_id,
                    entity_type="organization",
                    entity_id=organization.id,
                    finding_type="incomplete_record",
                    confidence=MANUAL_REVIEW_NEEDED,
                    auto_applied=False,
                    message="Organization record is missing a stable normalized name",
                )
                findings += 1
        return findings

    def _deduplicate_publications(self, run_id: UUID) -> tuple[int, int]:
        merged = 0
        findings = 0
        publications = list(
            self.session.scalars(
                select(PublicationModel).order_by(PublicationModel.created_at.asc()),
            ),
        )
        merged += self._merge_exact_publication_groups(run_id, publications, "doi")
        merged += self._merge_exact_publication_groups(run_id, publications, "openaire_id")
        self.session.flush()

        groups: dict[tuple[str, int | None], list[PublicationModel]] = {}
        for publication in self.session.scalars(select(PublicationModel)):
            key = (publication.normalized_title, publication.publication_year)
            if publication.normalized_title:
                groups.setdefault(key, []).append(publication)

        for group in groups.values():
            if len(group) < 2:
                continue
            target = group[0]
            for candidate in group[1:]:
                venue_match = self._normalized_optional(
                    target.journal_name or target.venue_name,
                ) == self._normalized_optional(candidate.journal_name or candidate.venue_name)
                author_overlap = self._publication_author_overlap(target, candidate)
                confidence = STRONG_MATCH if venue_match or author_overlap > 0 else POSSIBLE_MATCH
                auto_applied = False
                if confidence == STRONG_MATCH and self._can_merge_publications(
                    target,
                    candidate,
                ):
                    self._merge_publication_records(target, candidate)
                    merged += 1
                    auto_applied = True
                self._add_finding(
                    run_id=run_id,
                    entity_type="publication",
                    entity_id=target.id,
                    candidate_entity_id=candidate.id,
                    finding_type="duplicate_candidate",
                    confidence=confidence,
                    auto_applied=auto_applied,
                    message="Publication duplicate candidate detected",
                    details={
                        "title": target.title,
                        "candidate_title": candidate.title,
                        "venue_match": venue_match,
                        "author_overlap": author_overlap,
                    },
                )
                findings += 1
        return merged, findings

    def _deduplicate_researchers(self, run_id: UUID) -> tuple[int, int]:
        merged = 0
        findings = 0
        researchers = list(
            self.session.scalars(
                select(ResearcherModel).order_by(ResearcherModel.created_at.asc()),
            ),
        )
        merged += self._merge_exact_researcher_groups(run_id, researchers)
        self.session.flush()

        groups: dict[str, list[ResearcherModel]] = {}
        for researcher in self.session.scalars(select(ResearcherModel)):
            if researcher.normalized_name:
                groups.setdefault(researcher.normalized_name, []).append(researcher)

        for group in groups.values():
            if len(group) < 2:
                continue
            target = group[0]
            for candidate in group[1:]:
                same_primary_org = (
                    target.primary_organization_id is not None
                    and target.primary_organization_id == candidate.primary_organization_id
                )
                shared_publications = self._shared_publications(target, candidate)
                confidence = (
                    STRONG_MATCH
                    if same_primary_org or shared_publications > 0
                    else POSSIBLE_MATCH
                )
                auto_applied = False
                if same_primary_org and self._can_merge_researchers(target, candidate):
                    self._merge_researcher_records(target, candidate)
                    merged += 1
                    auto_applied = True
                self._add_finding(
                    run_id=run_id,
                    entity_type="researcher",
                    entity_id=target.id,
                    candidate_entity_id=candidate.id,
                    finding_type="duplicate_candidate",
                    confidence=confidence,
                    auto_applied=auto_applied,
                    message="Researcher duplicate candidate detected",
                    details={
                        "normalized_name": target.normalized_name,
                        "same_primary_organization": same_primary_org,
                        "shared_publications": shared_publications,
                    },
                )
                findings += 1
        return merged, findings

    def _deduplicate_organizations(self, run_id: UUID) -> tuple[int, int]:
        merged = 0
        findings = 0
        organizations = list(
            self.session.scalars(
                select(OrganizationModel).order_by(OrganizationModel.created_at.asc()),
            ),
        )
        merged += self._merge_exact_organization_groups(run_id, organizations, "ror_id")
        merged += self._merge_exact_organization_groups(run_id, organizations, "openaire_id")
        self.session.flush()

        groups: dict[str, list[OrganizationModel]] = {}
        for organization in self.session.scalars(select(OrganizationModel)):
            if organization.normalized_name:
                groups.setdefault(organization.normalized_name, []).append(organization)

        for group in groups.values():
            if len(group) < 2:
                continue
            target = group[0]
            for candidate in group[1:]:
                same_parent = target.parent_organization_id == candidate.parent_organization_id
                same_location = (
                    self._normalized_optional(target.city)
                    == self._normalized_optional(candidate.city)
                    and target.country_code == candidate.country_code
                )
                confidence = STRONG_MATCH if same_parent or same_location else POSSIBLE_MATCH
                auto_applied = False
                if (same_parent or same_location) and self._can_merge_organizations(
                    target,
                    candidate,
                ):
                    self._merge_organization_records(target, candidate)
                    merged += 1
                    auto_applied = True
                self._add_finding(
                    run_id=run_id,
                    entity_type="organization",
                    entity_id=target.id,
                    candidate_entity_id=candidate.id,
                    finding_type="duplicate_candidate",
                    confidence=confidence,
                    auto_applied=auto_applied,
                    message="Organization duplicate candidate detected",
                    details={
                        "normalized_name": target.normalized_name,
                        "same_parent": same_parent,
                        "same_location": same_location,
                    },
                )
                findings += 1
        return merged, findings

    def _merge_exact_publication_groups(
        self,
        run_id: UUID,
        publications: list[PublicationModel],
        identifier_field: str,
    ) -> int:
        groups: dict[str, list[PublicationModel]] = {}
        for publication in publications:
            value = getattr(publication, identifier_field)
            if value:
                groups.setdefault(value, []).append(publication)

        merged = 0
        for identifier_value, group in groups.items():
            if len(group) < 2:
                continue
            target = group[0]
            for candidate in group[1:]:
                auto_applied = False
                confidence = EXACT_MATCH
                if self._can_merge_publications(target, candidate):
                    self._merge_publication_records(target, candidate)
                    merged += 1
                    auto_applied = True
                else:
                    confidence = MANUAL_REVIEW_NEEDED
                self._add_finding(
                    run_id=run_id,
                    entity_type="publication",
                    entity_id=target.id,
                    candidate_entity_id=candidate.id,
                    finding_type="duplicate_candidate",
                    confidence=confidence,
                    auto_applied=auto_applied,
                    message=f"Publication duplicate candidate detected by {identifier_field}",
                    details={identifier_field: identifier_value},
                )
        return merged

    def _merge_exact_researcher_groups(
        self,
        run_id: UUID,
        researchers: list[ResearcherModel],
    ) -> int:
        groups: dict[str, list[ResearcherModel]] = {}
        for researcher in researchers:
            if researcher.orcid:
                groups.setdefault(researcher.orcid, []).append(researcher)

        merged = 0
        for identifier_value, group in groups.items():
            if len(group) < 2:
                continue
            target = group[0]
            for candidate in group[1:]:
                auto_applied = False
                confidence = EXACT_MATCH
                if self._can_merge_researchers(target, candidate):
                    self._merge_researcher_records(target, candidate)
                    merged += 1
                    auto_applied = True
                else:
                    confidence = MANUAL_REVIEW_NEEDED
                self._add_finding(
                    run_id=run_id,
                    entity_type="researcher",
                    entity_id=target.id,
                    candidate_entity_id=candidate.id,
                    finding_type="duplicate_candidate",
                    confidence=confidence,
                    auto_applied=auto_applied,
                    message="Researcher duplicate candidate detected by orcid",
                    details={"orcid": identifier_value},
                )
        return merged

    def _merge_exact_organization_groups(
        self,
        run_id: UUID,
        organizations: list[OrganizationModel],
        identifier_field: str,
    ) -> int:
        groups: dict[str, list[OrganizationModel]] = {}
        for organization in organizations:
            value = getattr(organization, identifier_field)
            if value:
                groups.setdefault(value, []).append(organization)

        merged = 0
        for identifier_value, group in groups.items():
            if len(group) < 2:
                continue
            target = group[0]
            for candidate in group[1:]:
                auto_applied = False
                confidence = EXACT_MATCH
                if self._can_merge_organizations(target, candidate):
                    self._merge_organization_records(target, candidate)
                    merged += 1
                    auto_applied = True
                else:
                    confidence = MANUAL_REVIEW_NEEDED
                self._add_finding(
                    run_id=run_id,
                    entity_type="organization",
                    entity_id=target.id,
                    candidate_entity_id=candidate.id,
                    finding_type="duplicate_candidate",
                    confidence=confidence,
                    auto_applied=auto_applied,
                    message=f"Organization duplicate candidate detected by {identifier_field}",
                    details={identifier_field: identifier_value},
                )
        return merged

    def _can_merge_publications(
        self,
        target: PublicationModel,
        candidate: PublicationModel,
    ) -> bool:
        target_positions = {item.author_position: item.researcher_id for item in target.authors}
        for author in candidate.authors:
            if (
                author.author_position in target_positions
                and target_positions[author.author_position] != author.researcher_id
            ):
                return False
        return True

    def _can_merge_researchers(self, target: ResearcherModel, candidate: ResearcherModel) -> bool:
        for candidate_author in candidate.authored_publications:
            for target_author in target.authored_publications:
                if (
                    target_author.publication_id == candidate_author.publication_id
                    and target_author.author_position != candidate_author.author_position
                ):
                    return False
        return True

    def _can_merge_organizations(
        self,
        target: OrganizationModel,
        candidate: OrganizationModel,
    ) -> bool:
        return target.id != candidate.id

    def _merge_publication_records(
        self,
        target: PublicationModel,
        candidate: PublicationModel,
    ) -> None:
        if target.canonical_source_record_id is None:
            target.canonical_source_record_id = candidate.canonical_source_record_id
        if target.abstract is None:
            target.abstract = candidate.abstract
        if target.publication_year is None:
            target.publication_year = candidate.publication_year
        if target.publication_date is None:
            target.publication_date = candidate.publication_date
        if target.journal_name is None:
            target.journal_name = candidate.journal_name
        if target.venue_name is None:
            target.venue_name = candidate.venue_name
        if target.publisher is None:
            target.publisher = candidate.publisher

        for author in list(candidate.authors):
            duplicate_author = self.session.scalar(
                select(PublicationAuthorModel).where(
                    PublicationAuthorModel.publication_id == target.id,
                    PublicationAuthorModel.researcher_id == author.researcher_id,
                ),
            )
            if duplicate_author is not None:
                self.session.delete(author)
                continue
            author.publication_id = target.id

        for organization in list(candidate.organizations):
            duplicate_organization = self.session.scalar(
                select(PublicationOrganizationModel).where(
                    PublicationOrganizationModel.publication_id == target.id,
                    PublicationOrganizationModel.organization_id == organization.organization_id,
                    PublicationOrganizationModel.relation_type == organization.relation_type,
                ),
            )
            if duplicate_organization is not None:
                self.session.delete(organization)
                continue
            organization.publication_id = target.id

        for embedding in list(candidate.embeddings):
            duplicate_embedding = self.session.scalar(
                select(PublicationEmbeddingModel).where(
                    PublicationEmbeddingModel.publication_id == target.id,
                    PublicationEmbeddingModel.embedding_model == embedding.embedding_model,
                    PublicationEmbeddingModel.embedding_version == embedding.embedding_version,
                ),
            )
            if duplicate_embedding is not None:
                self.session.delete(embedding)
                continue
            embedding.publication_id = target.id

        for identifier in list(
            self.session.scalars(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "publication",
                    ExternalIdentifierModel.entity_id == candidate.id,
                ),
            ),
        ):
            duplicate_identifier = self.session.scalar(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "publication",
                    ExternalIdentifierModel.entity_id == target.id,
                    ExternalIdentifierModel.identifier_type == identifier.identifier_type,
                    ExternalIdentifierModel.identifier_value == identifier.identifier_value,
                ),
            )
            if duplicate_identifier is not None:
                self.session.delete(identifier)
                continue
            identifier.entity_id = target.id

        self.session.delete(candidate)
        self.session.flush()

    def _merge_researcher_records(
        self,
        target: ResearcherModel,
        candidate: ResearcherModel,
    ) -> None:
        if target.display_name is None:
            target.display_name = candidate.display_name
        if target.email is None:
            target.email = candidate.email
        if target.profile_url is None:
            target.profile_url = candidate.profile_url
        if target.primary_organization_id is None:
            target.primary_organization_id = candidate.primary_organization_id

        for author in list(candidate.authored_publications):
            duplicate_author = self.session.scalar(
                select(PublicationAuthorModel).where(
                    PublicationAuthorModel.publication_id == author.publication_id,
                    PublicationAuthorModel.researcher_id == target.id,
                ),
            )
            if duplicate_author is not None:
                self.session.delete(author)
                continue
            author.researcher_id = target.id

        for affiliation in candidate.affiliations:
            affiliation.researcher_id = target.id

        for identifier in list(
            self.session.scalars(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "researcher",
                    ExternalIdentifierModel.entity_id == candidate.id,
                ),
            ),
        ):
            duplicate_identifier = self.session.scalar(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "researcher",
                    ExternalIdentifierModel.entity_id == target.id,
                    ExternalIdentifierModel.identifier_type == identifier.identifier_type,
                    ExternalIdentifierModel.identifier_value == identifier.identifier_value,
                ),
            )
            if duplicate_identifier is not None:
                self.session.delete(identifier)
                continue
            identifier.entity_id = target.id

        self.session.delete(candidate)
        self.session.flush()

    def _merge_organization_records(
        self,
        target: OrganizationModel,
        candidate: OrganizationModel,
    ) -> None:
        if target.website is None:
            target.website = candidate.website
        if target.country_code is None:
            target.country_code = candidate.country_code
        if target.city is None:
            target.city = candidate.city
        if target.parent_organization_id is None:
            target.parent_organization_id = candidate.parent_organization_id

        for researcher in candidate.primary_researchers:
            if researcher.primary_organization_id == candidate.id:
                researcher.primary_organization_id = target.id

        for affiliation in candidate.affiliations:
            affiliation.organization_id = target.id

        for publication_org in list(candidate.publications):
            duplicate_publication_org = self.session.scalar(
                select(PublicationOrganizationModel).where(
                    PublicationOrganizationModel.publication_id == publication_org.publication_id,
                    PublicationOrganizationModel.organization_id == target.id,
                    PublicationOrganizationModel.relation_type == publication_org.relation_type,
                ),
            )
            if duplicate_publication_org is not None:
                self.session.delete(publication_org)
                continue
            publication_org.organization_id = target.id

        for child in candidate.child_organizations:
            child.parent_organization_id = target.id

        for identifier in list(
            self.session.scalars(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "organization",
                    ExternalIdentifierModel.entity_id == candidate.id,
                ),
            ),
        ):
            duplicate_identifier = self.session.scalar(
                select(ExternalIdentifierModel).where(
                    ExternalIdentifierModel.entity_type == "organization",
                    ExternalIdentifierModel.entity_id == target.id,
                    ExternalIdentifierModel.identifier_type == identifier.identifier_type,
                    ExternalIdentifierModel.identifier_value == identifier.identifier_value,
                ),
            )
            if duplicate_identifier is not None:
                self.session.delete(identifier)
                continue
            identifier.entity_id = target.id

        self.session.delete(candidate)
        self.session.flush()

    def _publication_author_overlap(self, left: PublicationModel, right: PublicationModel) -> int:
        left_names = {item.researcher.normalized_name for item in left.authors}
        right_names = {item.researcher.normalized_name for item in right.authors}
        return len(left_names & right_names)

    def _shared_publications(self, left: ResearcherModel, right: ResearcherModel) -> int:
        left_publications = {item.publication_id for item in left.authored_publications}
        right_publications = {item.publication_id for item in right.authored_publications}
        return len(left_publications & right_publications)

    def _normalized_optional(self, value: str | None) -> str:
        return normalize_text(value)

    def _clean_text_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = unicodedata.normalize("NFKC", value)
        return " ".join(normalized.split()).strip() or None

    def _add_finding(
        self,
        *,
        run_id: UUID,
        entity_type: str,
        entity_id: UUID | None,
        candidate_entity_id: UUID | None = None,
        finding_type: str,
        confidence: str,
        auto_applied: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.session.add(
            NormalizationFindingModel(
                run_id=run_id,
                entity_type=entity_type,
                entity_id=entity_id,
                candidate_entity_id=candidate_entity_id,
                finding_type=finding_type,
                confidence=confidence,
                auto_applied=auto_applied,
                message=message,
                details=details,
            ),
        )

    def _to_summary(
        self,
        run: NormalizationRunModel,
        summary: dict[str, Any],
    ) -> NormalizationRunSummary:
        return NormalizationRunSummary(
            run_id=run.id,
            status=run.status,
            normalized_publications=int(summary.get("normalized_publications", 0)),
            normalized_researchers=int(summary.get("normalized_researchers", 0)),
            normalized_organizations=int(summary.get("normalized_organizations", 0)),
            auto_merged_publications=int(summary.get("auto_merged_publications", 0)),
            auto_merged_researchers=int(summary.get("auto_merged_researchers", 0)),
            auto_merged_organizations=int(summary.get("auto_merged_organizations", 0)),
            findings_count=int(summary.get("findings_count", 0)),
            completed_at=run.completed_at,
        )
