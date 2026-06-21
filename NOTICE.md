# Notices and Third-Party Components

EuniGraph is an original prototype developed by Cristiano Pistorio for mapping
research activity across EUNICE partner universities.

The project source code is distributed under the MIT License. See
[LICENSE](LICENSE).

This notice summarizes the main third-party software, services, and data
sources used by the prototype. It is intended as a practical compliance aid and
does not replace the official license texts or terms of service of each
component.

## Runtime and Infrastructure

| Component | Purpose | License / Terms |
| --- | --- | --- |
| Python | Backend runtime | Python Software Foundation License |
| Debian | Backend container base image | Debian Free Software Guidelines packages |
| Docker / Docker Compose | Containerized deployment | Docker terms and component licenses |
| PostgreSQL | Relational database | PostgreSQL License |
| Qdrant | Vector database | Apache License 2.0 |
| graph-tool | Graph analytics library | GPL-3.0-or-later |

`graph-tool` is installed in the backend container as a system package and is
used for materialized graph analytics. Before redistributing production images
or derivative packaged releases, downstream users should verify the applicable
GPL obligations for their distribution model.

## Backend Dependencies

The backend is a FastAPI application declared in
[backend/pyproject.toml](backend/pyproject.toml). Main dependencies include:

| Component | Purpose | Common License |
| --- | --- | --- |
| FastAPI | HTTP API framework | MIT |
| Starlette | ASGI toolkit used by FastAPI | BSD-3-Clause |
| Uvicorn | ASGI server | BSD-3-Clause |
| SQLAlchemy | ORM and SQL toolkit | MIT |
| Alembic | Database migrations | MIT |
| Pydantic / pydantic-settings | Settings and validation | MIT |
| psycopg | PostgreSQL driver | LGPL-3.0-only with exceptions |
| NumPy | Numerical computing | BSD-3-Clause |
| qdrant-client | Qdrant Python client | Apache License 2.0 |

Development-only dependencies include pytest, pytest-asyncio, httpx, mypy,
ruff, and pre-commit.

## Frontend Dependencies

The frontend is a Next.js application declared in
[frontend/package.json](frontend/package.json). Main dependencies include:

| Component | Purpose | Common License |
| --- | --- | --- |
| Next.js | React application framework | MIT |
| React / React DOM | UI runtime | MIT |
| TanStack Query | Frontend data fetching/cache | MIT |
| Cytoscape.js | Graph visualization | MIT |
| React Hook Form | Form handling | MIT |
| Tailwind CSS | Styling framework | MIT |
| TypeScript | Type checking | Apache License 2.0 |

## External APIs and Services

| Service | Purpose | Notes |
| --- | --- | --- |
| OpenAIRE Graph API | Public research metadata ingestion | Use is subject to OpenAIRE API terms, attribution requirements, and availability limits. |
| Google Gemini API | Optional publication embedding generation | Requires a user-provided `GEMINI_API_KEY`; use is subject to Google API terms. |
| Qdrant | Vector storage and nearest-neighbor retrieval | Can run locally through Docker Compose or against a managed Qdrant endpoint. |

The repository does not include private API keys. Runtime secrets are expected
to be provided through environment variables or deployment-specific `.env`
files that are not committed.

## Data and Generated Artifacts

EuniGraph can ingest metadata from OpenAIRE and can persist generated graph and
embedding artifacts. These generated outputs are deployment data and are not
part of the source-code license unless explicitly published with their own
license or terms.

See [DATA_AND_API_USAGE.md](DATA_AND_API_USAGE.md) for the project data and API
usage policy.

