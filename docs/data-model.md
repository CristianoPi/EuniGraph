# EuniGraph Data Model

## Purpose

This document defines the initial PostgreSQL schema for EuniGraph.

The schema is designed to:
- represent canonical research entities for the MVP
- preserve strong provenance of imported source records
- support OpenAIRE Beginner's Kit ingestion without mirroring the raw payload 1:1
- power authorship, affiliation, organization and co-authorship queries
- keep PostgreSQL as the structured system of record while Qdrant handles vectors

This document is the concrete relational complement to [docs/eunigraph_openaire_data_model.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/eunigraph_openaire_data_model.md), which remains the conceptual OpenAIRE alignment reference.

## Model Overview

The schema is intentionally split into two layers.

### Raw provenance layer

- `data_source`
- `ingestion_run`
- `source_record`

This layer keeps track of where the data came from, when it was ingested, and what the original raw payload looked like.

### Canonical application layer

- `organization`
- `researcher`
- `researcher_affiliation`
- `publication`
- `publication_author`
- `publication_organization`
- `external_identifier`
- `publication_embedding`

This layer supports the actual application queries and future API exposure.

## Main Tables

### `data_source`

Represents the logical source of the data, such as OpenAIRE or a manual upload.

Main fields:
- `id` UUID primary key
- `name` unique logical name
- `source_type` flexible textual source classification
- `base_url`, `description`
- `is_active`
- `created_at`, `updated_at`

### `ingestion_run`

Represents a single ingestion execution.

Main fields:
- `id`
- `data_source_id`
- `status`
- `started_at`, `completed_at`
- `triggered_by`
- `notes`
- `raw_config` JSONB for run-specific parameters

### `source_record`

Represents the raw source payload with strong provenance.

Main fields:
- `id`
- `data_source_id`
- `ingestion_run_id`
- `entity_type`
- `source_identifier`
- `source_version`
- `checksum`
- `raw_payload` JSONB
- `ingested_at`

Important note:
- the implemented uniqueness is per ingestion run: `(ingestion_run_id, entity_type, source_identifier)`
- this allows the same logical source identifier to be observed again in later runs without losing provenance history

### `organization`

Canonical organization entity for universities, departments, institutes, labs or centers.

Main fields:
- `id`
- `name`
- `normalized_name`
- `organization_type`
- `country_code`
- `city`
- `website`
- `parent_organization_id`
- `ror_id`
- `openaire_id`
- `created_at`, `updated_at`

### `researcher`

Canonical person entity.

Main fields:
- `id`
- `full_name`
- `given_name`
- `family_name`
- `normalized_name`
- `display_name`
- `orcid`
- `email`
- `profile_url`
- `primary_organization_id`
- `created_at`, `updated_at`

### `researcher_affiliation`

Represents the affiliation relationship between a researcher and an organization.

Main fields:
- `id`
- `researcher_id`
- `organization_id`
- `role_title`
- `start_date`
- `end_date`
- `is_primary`
- `source_record_id`
- `created_at`, `updated_at`

### `publication`

The central table of the MVP.

Main fields:
- `id`
- `title`
- `normalized_title`
- `abstract`
- `publication_year`
- `publication_date`
- `doi`
- `openaire_id`
- `publication_type`
- `language_code`
- `journal_name`
- `venue_name`
- `publisher`
- `open_access`
- `source_url`
- `canonical_source_record_id`
- `created_at`, `updated_at`

### `publication_author`

Associates a publication with a researcher while preserving author order.

Main fields:
- `id`
- `publication_id`
- `researcher_id`
- `author_position`
- `author_list_name`
- `is_corresponding`
- `source_record_id`
- `created_at`

### `publication_organization`

Associates a publication with an organization through a typed relation.

Main fields:
- `id`
- `publication_id`
- `organization_id`
- `relation_type`
- `source_record_id`
- `created_at`

### `external_identifier`

Stores additional external identifiers generically across canonical entities.

Main fields:
- `id`
- `entity_type`
- `entity_id`
- `identifier_type`
- `identifier_value`
- `is_primary`
- `source_record_id`
- `created_at`

### `publication_embedding`

Links a canonical publication to its vector representation in Qdrant.

Main fields:
- `id`
- `publication_id`
- `qdrant_collection`
- `qdrant_point_id`
- `embedding_model`
- `embedding_version`
- `content_hash`
- `created_at`, `updated_at`

## Main Relationships

- `data_source 1:N ingestion_run`
- `data_source 1:N source_record`
- `ingestion_run 1:N source_record`
- `organization 1:N organization` through `parent_organization_id`
- `organization 1:N researcher` through `primary_organization_id`
- `researcher N:M organization` through `researcher_affiliation`
- `publication N:M researcher` through `publication_author`
- `publication N:M organization` through `publication_organization`
- `publication 1:N publication_embedding`
- `source_record 1:N` toward affiliation, authorship, publication-organization and identifiers
- `source_record 1:0..1 publication` through `canonical_source_record_id`

## OpenAIRE Beginner's Kit Mapping

Primary mapping used by the MVP:

- OpenAIRE `publication` or `result`
  maps to `publication`, `publication_author`, `external_identifier`, `source_record`
- OpenAIRE `organization`
  maps to `organization`, `external_identifier`, `source_record`
- OpenAIRE `datasource`
  maps to `data_source`, `source_record`
- OpenAIRE `relation`
  maps to `publication_organization`, `researcher_affiliation`, plus `source_record`

The canonical PostgreSQL model intentionally does not mirror each OpenAIRE payload structure directly.

Instead:
- raw payloads are preserved in `source_record.raw_payload`
- canonical entities simplify the application layer
- multiple OpenAIRE identifiers are preserved through first-class columns when operationally important and through `external_identifier` for everything else
- OpenAIRE relation semantics that matter immediately to the MVP are materialized in dedicated bridge tables

## Query Support

The schema and indexes are chosen to support these queries efficiently:

- publications of a researcher:
  `publication_author.researcher_id -> publication`
- authors of a publication in order:
  `publication_author.publication_id + author_position`
- publications of an organization:
  `publication_organization.organization_id -> publication`
- co-authorship graph construction:
  self-joins over `publication_author`
- publication lookup by DOI or normalized title:
  unique `doi`, indexed `normalized_title`
- researcher lookup by normalized name or ORCID:
  indexed `normalized_name`, unique `orcid`
- provenance lookup of a canonical row:
  canonical foreign keys to `source_record`
- publication to Qdrant resolution:
  `publication_embedding.publication_id`

## Motivation For The Main Choices

- UUID primary keys keep the model source-agnostic and safe for future multi-source ingestion
- one `organization` table keeps the MVP flexible while still allowing hierarchical structures
- `publication_author` preserves author order and directly supports co-authorship graph derivation
- `external_identifier` absorbs heterogeneous OpenAIRE and future identifiers without schema churn
- `publication_embedding` keeps the canonical-to-vector link explicit and versionable
- textual classification fields are preferred over rigid PostgreSQL enums in the MVP

## Assumptions

- OpenAIRE identifiers can coexist with additional identifiers stored in `external_identifier`
- organization hierarchy can be represented with a single self-reference
- a canonical publication may point to one preferred source record, while provenance history remains in `source_record`
- the same logical source record may appear again in future ingestion runs, so `source_record` uniqueness is scoped to the run
- relation semantics such as `isAuthorInstitutionOf` are preserved as textual `relation_type` values in the canonical bridge table

## MVP Limits

- `project`, `community`, and full OpenAIRE relation coverage are not yet materialized as canonical tables
- publication venues and journals are not normalized into dedicated entities
- `external_identifier.entity_id` is polymorphic and therefore not protected by a database foreign key
- topic and subject vocabularies remain outside the canonical relational core in this phase
- no attempt is made yet to model full result-to-result citations in PostgreSQL

## Deferred Topics

Explicitly postponed:
- canonical `project` model
- citation and related-result tables
- full field-by-field mapping tables for every OpenAIRE payload variant
- deduplication and identity resolution strategy for researchers and organizations
- subject normalization and controlled vocabulary support
- materialized views or denormalized analytics tables
