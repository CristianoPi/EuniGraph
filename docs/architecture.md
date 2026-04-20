# EuniGraph Architecture

## Vision

EuniGraph is a prototype platform for acquiring, organizing, analyzing, and visualizing research data across EUNICE partner universities.

The system is designed to:
- ingest publication metadata and related research entities
- store canonical data in PostgreSQL
- derive a co-authorship graph for analysis
- manage article embeddings and semantic similarity workflows through Qdrant
- expose capabilities through APIs
- provide an interactive web frontend for browsing, graph exploration and prototype administration

## Architectural Rationale

### Why a Modular Monolith

The initial delivery target is an MVP for a contest. The system therefore optimizes for:
- fast delivery
- low operational overhead
- simple onboarding for a small team
- clear boundaries that reduce future rework

A modular monolith is the best fit for this stage because it avoids premature distributed-system complexity while still enforcing separation between business capabilities.

### Why Not Microservices Yet

At this stage, introducing multiple independently deployed services would increase:
- deployment complexity
- local development friction
- observability and operational burden
- coordination overhead for a small team

The chosen structure keeps service extraction possible later, but does not pay that cost now.

## Core Components

### Backend

The backend is a FastAPI application organized into domain-oriented modules:
- `catalog`: canonical entities such as publications, researchers, organizations, authorship and affiliations
- `ingestion`: source adapters and import workflows
- `normalization`: data cleanup, canonicalization, deduplication, mapping
- `embeddings`: semantic enrichment and vector search integration
- `coauthorship`: graph projection and analysis workflows
- `semantic_graph`: semantic publication-publication graph materialization
- `tasks`: internal orchestration for long-running processes
- `api`: HTTP exposure and request/response schemas
- `core`: configuration, lifecycle, logging, bootstrap
- `shared`: minimal cross-module primitives
- `persistence`: shared PostgreSQL and Qdrant adapters

### Frontend

The frontend is a Next.js application in the same monorepo. It provides:
- the application shell and navigation
- dashboard and canonical entity browsing
- publication, researcher and organization detail views
- unified coauthorship and semantic graph exploration
- an admin console for workflow operations and manual canonical data entry

The frontend uses a Next.js API proxy route to call the backend, keeping browser-facing API paths stable while allowing the actual backend origin to remain server-side configurable.

### PostgreSQL

PostgreSQL is the system of record for canonical structured data:
- publications
- researchers
- organizations
- authorship and affiliation bridges
- provenance records
- workflow metadata
- linking tables and metadata required for application workflows

This datastore should remain the authoritative source for the normalized research model.

### Qdrant

Qdrant stores vector representations of articles and supports semantic similarity queries. It complements PostgreSQL rather than replacing it.

### graph-tool

`graph-tool` is the chosen library for materialized graph analysis because graph operations and network analytics are a first-class concern of the platform.

## Design Principles

### Module Boundaries First

The primary architectural boundary is the application module, not the technical layer. Each module owns its application logic and grows independently.

### Internal Layering Within Modules

Inside each module, the code is separated into:
- `application/`
- `domain/`
- `infrastructure/`
- `interfaces/`

This keeps domain logic insulated from frameworks and storage details while avoiding global layer sprawl.

### Explicit Separation of Concerns

The following concerns must remain distinct:
- API schemas
- domain objects and business rules
- persistence models and repositories
- infrastructure configuration
- architectural documentation

### Operational Simplicity

The local stack must stay easy to run with Docker Compose. This is critical for reproducibility, onboarding, and contest delivery speed.

## Technology Choices

### FastAPI

Chosen for:
- strong typing and Pydantic integration
- fast API bootstrap
- modular routing
- good developer ergonomics for a small team

### PostgreSQL

Chosen for:
- strong relational modeling
- transactional guarantees
- good fit for canonical research metadata
- mature ecosystem and migration tooling

### Qdrant

Chosen for:
- dedicated vector search capabilities
- clean integration path for semantic exploration of articles
- good separation between canonical data and vector indexing concerns

### graph-tool

Chosen for:
- efficient graph analytics
- fit for co-authorship networks and derived metrics

### Docker / Docker Compose

Chosen for:
- reproducible development environments
- reduced setup drift across collaborators
- early alignment with deployment concerns

### Frontend Stack

Chosen frontend technologies:
- Next.js with App Router for route and layout composition
- Tailwind CSS for rapid, consistent styling
- TanStack Query for server-state queries and mutations
- Cytoscape.js for interactive graph rendering
- React Hook Form for admin and manual data entry forms

These choices are already implemented in `frontend/` and documented in [frontend-overview.md](frontend-overview.md), [frontend-graph-explorer.md](frontend-graph-explorer.md) and [frontend-admin-console.md](frontend-admin-console.md).

## Path Toward Future Service Extraction

The current monolith is intentionally shaped to support future separation if justified by scale, performance, or team topology.

Likely future extraction candidates:
- ingestion pipelines
- embeddings and vector indexing workflows
- graph analysis workloads

Extraction should happen only when one or more of these become true:
- significantly different scaling profiles
- operational isolation is required
- independent release cadence becomes valuable
- ownership boundaries in the team become stable

## Initial Technical Risks

### Metadata Quality and Entity Resolution

Author disambiguation, affiliation normalization, and inconsistent source metadata will likely be one of the hardest parts of the system.

### `graph-tool` Containerization

`graph-tool` is a valid technology choice, but it is also the most sensitive dependency from an environment-management perspective. The project structure already isolates graph logic so the packaging problem stays localized.

### Cross-Store Consistency

The system will eventually span PostgreSQL, Qdrant, and graph-derived projections. Synchronization rules must remain explicit to avoid silent drift.

### Long-Running Processing

Ingestion, embedding generation, and graph rebuilding may become slower than synchronous API request lifecycles allow. The `tasks` module is reserved early to absorb that growth without an architectural rewrite.

## Decisions Already Made

- modular monolith as the initial architecture
- FastAPI as the backend framework
- PostgreSQL as the canonical relational datastore
- Qdrant as the vector database
- `graph-tool` as the graph analytics library
- Docker-based containerization from the start
- frontend kept in the monorepo from day one
- backend structured domain-first, with internal layering per module
- no separate worker in Issue 1
- `uv` for Python dependency and environment management
- SQLAlchemy 2 plus Alembic as the relational persistence baseline
- lightweight but complete quality baseline: pytest, Ruff, mypy, pre-commit
- canonical PostgreSQL schema for publications, researchers, organizations, provenance, embeddings and graph build tracking
- OpenAIRE Graph API v2 EUNICE seed as the main demo ingestion path, with the Beginner's Kit retained as a secondary archive-based path
- manual entity management APIs with provenance tracking
- deterministic normalization and deduplication workflow
- provider-based publication embeddings with Gemini as the first implementation
- materialized coauthorship and semantic graph pipelines
- Next.js, Tailwind CSS, TanStack Query, Cytoscape.js and React Hook Form as the frontend baseline
- frontend proxy route for backend API access instead of direct browser-to-FastAPI calls

## Decisions Deferred

The following topics are intentionally deferred to later issues:
- source-specific ingestion adapters
- full entity resolution beyond the current deterministic normalization workflow
- additional embedding providers beyond Gemini
- background workers or scheduled orchestration for long-running workflows
- semantic free-text search endpoints
- authentication, authorization and role management
- advanced entity editing and relation management UI
- deeper CI coverage beyond the current quality gate
