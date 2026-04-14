# EuniGraph

EuniGraph is a prototype platform for mapping research activity across EUNICE partner universities.

The repository is intentionally structured as a modular monolith from day one:
- FastAPI backend for APIs and application modules
- PostgreSQL as the canonical relational datastore
- Qdrant for semantic search and vector storage
- `graph-tool` for co-authorship graph analysis
- Docker-based local development and reproducible environments

## Repository Layout

```text
.
|-- backend/            # Python application, tests, migrations
|-- frontend/           # Frontend workspace placeholder for future UI work
|-- docs/               # Architecture, ADRs, diagrams
|-- infra/              # Dockerfiles and infrastructure-oriented assets
|-- scripts/            # Bootstrap and helper scripts
|-- data/               # Demo and sample datasets
|-- .env.example        # Local environment template
|-- docker-compose.yml  # Development stack
|-- Makefile            # Common development commands
```

## Quick Start

1. Copy the environment template:
   `cp .env.example .env`
2. Build and start the local stack:
   `docker compose up --build`
3. Open the backend API docs:
   [http://localhost:8000/docs](http://localhost:8000/docs)

## OpenAIRE Beginner's Kit Seed

The MVP seed expects the official OpenAIRE Beginner's Kit to be downloaded manually outside the application flow.

Configure the local dataset path with `OPENAIRE_BEGINNERS_KIT_PATH`. The default value in [`.env.example`](/Users/cristianopistorio/Code/GitHub/EuniGraph/.env.example) points to:

`data/openaire/beginners_kit/`

The current seed reads these archives directly from that directory:
- `publication.tar`
- `organization.tar`
- `datasource.tar`
- `project.tar`
- `relation.tar`

The loader does not download or unpack a single monolithic zip for you. It reads the local `.tar` archives already present on disk.

Useful commands:
- Seed load: `make backend-seed-openaire`
- Seed reset: `make backend-reset-openaire-seed`
- Seed status: `make backend-seed-status`

The same functionality is also available through development admin endpoints:
- `POST /api/v1/admin/seeds/openaire-beginners-kit/load`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/reset`
- `GET /api/v1/admin/seeds/openaire-beginners-kit/status`

For fast local checks, the seed loader supports `limit_per_file` so you can import only a subset of each archive.

## Manual Entity Management APIs

The backend also exposes manual entity management APIs for canonical data:
- publications
- researchers
- organizations
- publication authors
- researcher affiliations
- publication organizations

These endpoints are intended for demo data entry, corrections, and controlled enrichment of the canonical dataset.

Manual writes are tracked through the provenance layer with a dedicated logical source:
- `manual_api_entry`

See [docs/seed-and-api.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/seed-and-api.md) for the current API surface and provenance behavior.

## Coauthorship Graph Pipeline

The coauthorship graph is materialized explicitly and is not rebuilt on every API request.

Runtime behavior:
- `POST /api/v1/coauthorship-graph/build` builds the graph from canonical PostgreSQL data
- the build persists graph artifacts under `EUNIGRAPH_COAUTHORSHIP_GRAPH_STORAGE_PATH`
- retrieval endpoints serve the latest successful materialized build
- the backend stores build metadata in PostgreSQL so failed and obsolete builds stay distinguishable

Default artifact path:

`data/graphs/coauthorship/`

Main endpoints:
- `POST /api/v1/coauthorship-graph/build`
- `GET /api/v1/coauthorship-graph/status`
- `GET /api/v1/coauthorship-graph`
- `GET /api/v1/coauthorship-graph/subgraph`
- `GET /api/v1/coauthorship-graph/metrics`
- `GET /api/v1/coauthorship-graph/nodes/{researcher_id}`
- `GET /api/v1/coauthorship-graph/visualization`

See [docs/coauthorship.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/coauthorship.md) for build logic, artifact layout, metrics and current limitations.

## Architecture Direction

- Start simple: one deployable unit, clean module boundaries
- Keep extraction paths open for ingestion, embeddings, and graph processing
- Avoid coupling API, domain, and persistence models
- Containerize early to reduce onboarding friction and environment drift

See [docs/architecture.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/architecture.md) for the initial architecture baseline.
See [docs/seed-and-api.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/seed-and-api.md) for the current seed and API development notes.
See [docs/normalization.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/normalization.md) for the current normalization and deduplication rules.
See [docs/coauthorship.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/coauthorship.md) for the materialized coauthorship graph pipeline.
