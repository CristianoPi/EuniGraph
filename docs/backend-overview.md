# Backend Overview

## 1. Purpose

The EuniGraph backend is the application layer that:
- exposes canonical research data through HTTP APIs
- coordinates ingestion and provenance workflows
- manages semantic enrichment and graph materialization
- serves persisted graph artifacts and technical workflow status

It is the main integration point between:
- PostgreSQL for canonical structured data
- Qdrant for publication embeddings and vector similarity
- persistent file storage for graph artifacts

## 2. Backend Architecture

The backend follows the modular monolith structure already defined for the project.

At a high level:
- FastAPI exposes HTTP routes and OpenAPI documentation
- application services orchestrate use cases
- SQLAlchemy models persist canonical data and build tracking metadata
- module boundaries separate domain concerns without introducing service fragmentation too early

The backend entrypoint is:
- [backend/src/eunigraph/main.py](/Users/cristianopistorio/Code/GitHub/EuniGraph/backend/src/eunigraph/main.py)

The API router registry is:
- [backend/src/eunigraph/api/router.py](/Users/cristianopistorio/Code/GitHub/EuniGraph/backend/src/eunigraph/api/router.py)

## 3. Main Modules

The main backend modules are:
- `catalog`: canonical entities such as publications, researchers, organizations, authorship and affiliations
- `ingestion`: OpenAIRE Beginner's Kit seed workflow and provenance handling
- `normalization`: deterministic normalization, deduplication and anomaly tracking
- `embeddings`: provider-based embedding generation and Qdrant integration
- `coauthorship`: materialized coauthorship graph build, persistence and retrieval
- `semantic_graph`: materialized publication-publication semantic similarity graph derived from Qdrant
- `persistence`: shared PostgreSQL and Qdrant adapters
- `core`: configuration, app lifecycle and runtime wiring
- `shared`: shared types, small utilities and cross-cutting helpers

## 4. Datastores and Storage Roles

### PostgreSQL

PostgreSQL is the canonical system of record for:
- publications
- researchers
- organizations
- affiliations and authorship bridges
- provenance entities such as `data_source`, `ingestion_run` and `source_record`
- workflow metadata such as normalization runs and graph build tracking
- embedding metadata in `publication_embedding`

### Qdrant

Qdrant stores publication vectors and semantic publication payloads used for:
- nearest-neighbor retrieval
- semantic graph construction
- future semantic exploration APIs

### File Storage

Persistent file storage under `data/graphs/` is used for materialized graph artifacts:
- `coauthorship`
- `semantic`

Each graph build persists:
- a `graph-tool` binary file
- a JSON payload used by retrieval APIs
- a static SVG visualization

## 5. API Families

The backend currently exposes these main endpoint families:

### Core and Canonical Data
- `/api/v1/health`
- `/api/v1/publications`
- `/api/v1/researchers`
- `/api/v1/organizations`
- `/api/v1/source-records`

### Workflow and Admin
- `/api/v1/admin/seeds/openaire-beginners-kit/*`
- `/api/v1/admin/normalization/*`

### Embeddings
- `/api/v1/embeddings/*`
- `/api/v1/publications/{id}/embedding`

### Graphs
- `/api/v1/coauthorship-graph/*`
- `/api/v1/semantic-graph/*`

## 6. Swagger and OpenAPI

FastAPI exposes the backend API documentation directly:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

Swagger/OpenAPI metadata is configured to make the API easier to navigate:
- tag descriptions group endpoint families
- route summaries and descriptions explain intent
- request and response models document canonical payloads
- common error responses document the standard FastAPI `detail` shape and validation failures

## 7. Where to Find Technical Documentation

Backend-related project documents are split by concern:
- [docs/architecture.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/architecture.md): overall system architecture
- [docs/data-model.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/data-model.md): canonical PostgreSQL data model
- [docs/seed-and-api.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/seed-and-api.md): seed workflow and API notes
- [docs/embeddings.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/embeddings.md): provider-based embeddings layer
- [docs/coauthorship.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/coauthorship.md): coauthorship graph pipeline
- [docs/semantic-graph.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/semantic-graph.md): semantic similarity graph pipeline
- [docs/normalization.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/normalization.md): normalization and deduplication rules

## 8. Significant Architectural Choices

The backend currently follows these important choices:
- modular monolith instead of microservices
- canonical relational model in PostgreSQL, not direct exposure of raw OpenAIRE payloads
- strong provenance via `source_record`
- provider-based embeddings abstraction
- materialized graph pipelines rather than live rebuilds on every request
- Qdrant used as vector infrastructure, not as the canonical metadata store
- graph artifacts served from persisted files, not generated on demand

## 9. Error Handling Model

The backend currently uses:
- standard FastAPI `HTTPException` responses for application-level errors
- standard FastAPI validation errors for request and query validation failures

In practice this means:
- application errors return a `detail` string
- validation errors return the default FastAPI `detail` list with field-level issues

This is intentionally simple for the MVP and avoids introducing a custom error envelope prematurely.

## 10. Current Limits

Current backend limitations include:
- no automatic workflow orchestration after seed, normalization, embedding refresh or graph rebuild
- no frontend-specific API shaping yet beyond graph JSON payloads
- no semantic search endpoint for free-text queries yet
- graph rebuilds are explicit administrative operations
- runtime compatibility warnings between Qdrant client and server versions still need cleanup in a separate infrastructure pass

## 11. Likely Next Backend Steps

The most likely next backend evolutions are:
- semantic search endpoints on top of Qdrant
- tighter background execution for long-running workflows
- more explicit API-level filtering for provenance and graph findings
- stronger contract tests for OpenAPI and major endpoint families
