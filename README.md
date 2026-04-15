# EuniGraph

EuniGraph is a prototype platform for mapping research activity across EUNICE partner universities.

The repository is intentionally structured as a modular monolith from day one:
- FastAPI backend for APIs and application modules
- PostgreSQL as the canonical relational datastore
- Qdrant for semantic workflows and vector storage
- `graph-tool` for materialized graph analysis
- Next.js frontend for dashboard, browsing, graph exploration and admin workflows
- Docker-based local development and reproducible environments

## Repository Layout

```text
.
|-- backend/            # Python application, tests, migrations
|-- frontend/           # Next.js frontend application
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
2. Build and start the backend stack:
   `docker compose up --build`
3. Open the backend API docs:
   [http://localhost:8000/docs](http://localhost:8000/docs)

To start the full stack including the frontend:
- `docker compose --profile ui up --build`
- frontend application: [http://localhost:3000](http://localhost:3000)
- backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Frontend

The frontend lives in [frontend/](frontend/) and is built with:
- Next.js App Router
- Tailwind CSS
- TanStack Query
- Cytoscape.js for graph rendering
- React Hook Form for admin and manual data entry forms

Current frontend routes include:
- `/`: overview and integration status
- `/dashboard`: workflow and catalog snapshot
- `/entities`: canonical catalog hub
- `/entities/publications`, `/entities/researchers`, `/entities/organizations`: browsing and detail flows
- `/graphs`: unified coauthorship and semantic graph explorer
- `/admin`: admin console overview
- `/admin/operations`: seed, normalization, embeddings and graph build controls
- `/admin/data-entry`: manual creation forms for publications, researchers and organizations

The browser calls the backend through the frontend proxy route `/api/backend/*`. In Docker Compose the frontend container forwards those requests to `http://backend:8000`, so the backend does not need to be exposed separately for a frontend-only public tunnel.

## OpenAIRE Beginner's Kit Seed

The MVP seed expects the official OpenAIRE Beginner's Kit to be downloaded manually outside the application flow.

Configure the local dataset path with `OPENAIRE_BEGINNERS_KIT_PATH`. The default value in [`.env.example`](.env.example) points to:

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

See [docs/seed-and-api.md](docs/seed-and-api.md) for the current API surface and provenance behavior.

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

See [docs/coauthorship.md](docs/coauthorship.md) for build logic, artifact layout, metrics and current limitations.

## Embeddings Layer

Publication embeddings are generated through a provider abstraction and persisted across:
- PostgreSQL for canonical embedding metadata
- Qdrant for vector storage

The initial provider is:
- Gemini `gemini-embedding-001`

Key runtime settings:
- `EMBEDDINGS_ENABLED`
- `EMBEDDINGS_PROVIDER`
- `EMBEDDINGS_MODEL`
- `EMBEDDINGS_VERSION`
- `EMBEDDINGS_BATCH_SIZE`
- `EMBEDDINGS_REQUEST_TIMEOUT_SECONDS`
- `EMBEDDINGS_MAX_RETRIES`
- `EMBEDDINGS_CONTENT_FIELDS`
- `GEMINI_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_PUBLICATIONS`

`QDRANT_API_KEY` is optional in the default local Docker setup.

Main endpoints:
- `POST /api/v1/embeddings/build`
- `POST /api/v1/embeddings/load-all`
- `POST /api/v1/embeddings/reset`
- `GET /api/v1/embeddings/status`
- `GET /api/v1/embeddings/provider`
- `POST /api/v1/publications/{id}/embedding`
- `GET /api/v1/publications/{id}/embedding`

## Architecture Direction

- Start simple: one deployable unit, clean module boundaries
- Keep extraction paths open for ingestion, embeddings, and graph processing
- Avoid coupling API, domain, and persistence models
- Containerize early to reduce onboarding friction and environment drift

See [docs/architecture.md](docs/architecture.md) for the architecture baseline.
See [docs/backend-overview.md](docs/backend-overview.md) for the backend structure, API families and Swagger/OpenAPI entry points.
See [docs/frontend-overview.md](docs/frontend-overview.md) for the frontend shell, route structure and backend integration pattern.
See [docs/frontend-graph-explorer.md](docs/frontend-graph-explorer.md) for the unified coauthorship and semantic graph explorer.
See [docs/frontend-admin-console.md](docs/frontend-admin-console.md) for the admin operations and manual data entry frontend.
See [docs/seed-and-api.md](docs/seed-and-api.md) for the current seed and API development notes.
See [docs/normalization.md](docs/normalization.md) for the current normalization and deduplication rules.
See [docs/coauthorship.md](docs/coauthorship.md) for the materialized coauthorship graph pipeline.
See [docs/embeddings.md](docs/embeddings.md) for the provider-based embeddings layer and Qdrant integration.
See [docs/semantic-graph.md](docs/semantic-graph.md) for the materialized semantic similarity graph pipeline.
