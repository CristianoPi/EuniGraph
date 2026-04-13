# Normalization And Deduplication

## Purpose

This document describes the first deterministic normalization and deduplication workflow implemented in EuniGraph.

The goal is not to provide full entity resolution. The goal is to:
- normalize canonical text fields into stable comparison keys
- reduce trivial duplicates safely
- surface ambiguous cases for later review
- improve downstream graph, analytics, and semantic workflows

## Module Boundary

The implementation lives in the `normalization` module and remains separate from:
- ingestion adapters
- API request schemas
- canonical persistence models
- vector and graph layers

The normalization workflow can be triggered explicitly through admin endpoints and writes its own run metadata and findings.

## Text Normalization Rules

The shared normalization logic is deterministic and intentionally simple.

Applied rules:
- trim leading and trailing whitespace
- collapse repeated internal whitespace
- Unicode normalization
- accent stripping for comparison keys
- casefolding for stable matching
- replace punctuation and separator noise with spaces
- collapse resulting spaces into a single token separator

Examples:
- `Università di Torino` -> `universita di torino`
- `Smash: Flexible, Fast.` -> `smash flexible fast`

Operational distinction:
- human-readable fields such as `title`, `full_name`, `organization.name` keep readable text after trim/collapse
- canonical comparison fields such as `normalized_title` and `normalized_name` use the fully normalized comparison form

## Deduplication Strategy

The workflow is hierarchical and explainable.

### Publications

Signals used:
- DOI
- OpenAIRE ID
- normalized title
- publication year
- journal or venue
- overlap in linked authors

Decision logic:
- `exact_match` for duplicate candidates detected by DOI or OpenAIRE ID
- `strong_match` for normalized title + year reinforced by venue or author overlap
- `possible_match` for title/year candidates without enough reinforcement
- `manual_review_needed` when a candidate exists but automatic merge is unsafe

Automatic merge policy:
- automatic merge is attempted only when there are no unsafe authorship conflicts
- otherwise the candidate is recorded as a finding without merge

### Researchers

Signals used:
- ORCID
- normalized name
- primary organization
- shared publications

Decision logic:
- `exact_match` for ORCID duplicates
- `strong_match` for normalized name plus same primary organization or shared bibliography
- `possible_match` for normalized-name-only cases

Automatic merge policy:
- automatic merge is attempted for ORCID duplicates and same-name same-primary-organization cases when authorship conflicts are absent
- ambiguous cases are recorded as findings

### Organizations

Signals used:
- ROR ID
- OpenAIRE ID
- normalized name
- parent organization
- city and country

Decision logic:
- `exact_match` for ROR or OpenAIRE ID duplicates
- `strong_match` for same normalized name plus same parent or same location
- `possible_match` for name-only duplicates

Automatic merge policy:
- automatic merge is attempted for exact identifier matches and conservative strong matches
- weaker cases remain findings

## Anomalies Tracked

The workflow records at least these anomaly classes:
- `incomplete_record`
- `malformed_identifier`
- `duplicate_candidate`

Examples:
- publication without DOI, OpenAIRE ID, and year
- malformed DOI, ORCID, or ROR
- duplicate candidates not auto-merged because confidence is too low or conflicts exist

## Confidence Levels

The current implementation uses these confidence labels:
- `exact_match`
- `strong_match`
- `possible_match`
- `manual_review_needed`

These are stored explicitly in normalization findings so the logic remains inspectable and testable.

## Persistence And Traceability

Each normalization execution creates:
- one `normalization_run`
- multiple `normalization_finding` rows

Tracked metadata includes:
- execution status
- trigger source
- summary counters
- entity ids involved
- candidate ids when relevant
- confidence class
- whether a merge was auto-applied
- structured details payload

## Admin Endpoints

Current endpoints:
- `POST /api/v1/admin/normalization/run`
- `GET /api/v1/admin/normalization/status`
- `GET /api/v1/admin/normalization/findings`

Useful filters for findings:
- `run_id`
- `entity_type`
- `confidence`
- `auto_applied`

## Current Limits

This first version is intentionally conservative.

Known limits:
- no ML-based entity resolution
- no review UI
- no fuzzy string library beyond deterministic normalization and simple heuristics
- automatic merge is limited to cases considered structurally safe
- exact duplicate matching by unique identifiers is mostly relevant to future relaxed loads or historical pre-canonical cleanup, because canonical constraints already block many trivial duplicates on insert
