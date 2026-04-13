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

## Current Limitations

- no automatic download of the Beginner's Kit
- no canonical `project` API yet
- no canonical `datasource` entity API for OpenAIRE datasource records yet
- relation-to-affiliation mapping is intentionally conservative; publication-organization mapping is the primary relation materialized from `relation.tar` in the MVP
