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

## Architecture Direction

- Start simple: one deployable unit, clean module boundaries
- Keep extraction paths open for ingestion, embeddings, and graph processing
- Avoid coupling API, domain, and persistence models
- Containerize early to reduce onboarding friction and environment drift

See [docs/architecture.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/architecture.md) for the initial architecture baseline.
