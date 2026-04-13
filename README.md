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

## Architecture Direction

- Start simple: one deployable unit, clean module boundaries
- Keep extraction paths open for ingestion, embeddings, and graph processing
- Avoid coupling API, domain, and persistence models
- Containerize early to reduce onboarding friction and environment drift

See [docs/architecture.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/architecture.md) for the initial architecture baseline.
See [docs/seed-and-api.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/seed-and-api.md) for the current seed and API development notes.
