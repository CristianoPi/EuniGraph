# Seed And API Notes

## OpenAIRE Beginner's Kit Path

The local dataset path is configured through:

- `OPENAIRE_BEGINNERS_KIT_PATH`

Default development value:

- `data/openaire/beginners_kit/`

Required archive files for the MVP seed:
- `publication.tar`
- `organization.tar`
- `datasource.tar`
- `project.tar`
- `relation.tar`

If the path or any required archive is missing, the seed loader returns a clear validation error before ingesting data.

## Seed Execution

CLI commands:
- `make backend-seed-openaire`
- `make backend-reset-openaire-seed`
- `make backend-seed-status`

Direct module invocation:

```bash
cd backend
uv run python -m eunigraph.modules.ingestion.application.seed_cli load
uv run python -m eunigraph.modules.ingestion.application.seed_cli load --limit-per-file 100
uv run python -m eunigraph.modules.ingestion.application.seed_cli status
uv run python -m eunigraph.modules.ingestion.application.seed_cli reset
```

## Current Seed Scope

The seed currently reads and persists raw provenance from:
- publications
- organizations
- datasources
- projects
- relations

Canonical entities currently populated by the seed:
- `publication`
- `researcher`
- `organization`
- `publication_author`
- `publication_organization`
- `external_identifier`
- raw provenance tables

Current deliberate limit:
- `project.tar` and `datasource.tar` are preserved in `source_record` but not yet mapped to canonical tables beyond the logical `data_source` record used for ingestion provenance

## Available APIs

Main CRUD/demo endpoints:
- `GET /api/v1/publications`
- `GET /api/v1/publications/{id}`
- `POST /api/v1/publications`
- `PATCH /api/v1/publications/{id}`
- `GET /api/v1/publications/{id}/authors`
- `POST /api/v1/publications/{id}/authors`
- `GET /api/v1/publications/{id}/organizations`
- `POST /api/v1/publications/{id}/organizations`

- `GET /api/v1/researchers`
- `GET /api/v1/researchers/{id}`
- `POST /api/v1/researchers`
- `PATCH /api/v1/researchers/{id}`
- `GET /api/v1/researchers/{id}/affiliations`
- `POST /api/v1/researchers/{id}/affiliations`

- `GET /api/v1/organizations`
- `GET /api/v1/organizations/{id}`
- `POST /api/v1/organizations`
- `PATCH /api/v1/organizations/{id}`

- `GET /api/v1/source-records`
- `GET /api/v1/source-records/{id}`

Development seed/admin endpoints:
- `GET /api/v1/admin/seeds/openaire-beginners-kit/status`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/load`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/reset`
- `POST /api/v1/admin/normalization/run`
- `GET /api/v1/admin/normalization/status`
- `GET /api/v1/admin/normalization/findings`

## Manual Canonical Entity Management

The main domain endpoints are also the manual entity management APIs for the MVP.

Supported manual writes:
- create and patch `publication`
- create and patch `researcher`
- create and patch `organization`
- create `publication_author`
- create `researcher_affiliation`
- create `publication_organization`

Manual writes are validated at the API boundary with pragmatic checks such as:
- `publication_year` must stay in the supported canonical range
- `author_position` must be greater than or equal to 1
- `country_code` is normalized to ISO-like uppercase two-letter form
- empty identifiers such as DOI, OpenAIRE id, ORCID are normalized away
- affiliation date ranges reject `end_date < start_date`

Integrity and collision errors are returned as readable `400` responses instead of surfacing raw database failures.

## Manual Provenance

Manual API writes are tracked through the existing provenance layer.

Implementation choices:
- logical `data_source.source_type = manual_api_entry`
- one short `ingestion_run` per manual write operation
- one `source_record` per create/update request

The `source_record.raw_payload` stores:
- action type such as `create` or `update`
- canonical entity type
- canonical entity id
- original API payload

Direct linkage behavior:
- `publication` updates `canonical_source_record_id`
- `publication_author`, `researcher_affiliation`, and `publication_organization` store `source_record_id`
- `researcher` and `organization` provenance is recoverable via `source_record.raw_payload.canonical_entity_id`

This keeps manual data distinguishable from:
- OpenAIRE Beginner's Kit seed data
- future automated ingestion pipelines
- future development-only bootstrap data

Useful provenance filters on `GET /api/v1/source-records`:
- `source_type`
- `canonical_entity_id`
- `entity_type`
- `source_identifier`
- `data_source_id`
- `ingestion_run_id`

This makes it possible to inspect, for example:
- only manual API provenance with `source_type=manual_api_entry`
- all provenance rows linked to one canonical entity with `canonical_entity_id=<uuid>`

## Current Limitations

- no automatic download of the Beginner's Kit
- no canonical `project` API yet
- no canonical `datasource` entity API for OpenAIRE datasource records yet
- relation-to-affiliation mapping is intentionally conservative; publication-organization mapping is the primary relation materialized from `relation.tar` in the MVP
- manual provenance for `researcher` and `organization` is stored in `source_record` but those entities do not yet have a direct foreign key to the latest provenance row
