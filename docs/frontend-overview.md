# Frontend Overview

## 1. Purpose

The frontend provides the application shell for EuniGraph:
- shared navigation
- route boundaries for the next product slices
- a clean integration layer toward the FastAPI backend
- reusable patterns for loading, error and empty states
- an administrative console for MVP operations and manual data entry

The frontend now includes the main prototype surfaces needed for demo operation: overview, dashboard, canonical browsing, graph exploration and administration.

## 2. Stack

The frontend is built with:
- Next.js with App Router
- Tailwind CSS
- TanStack Query
- Cytoscape.js for graph rendering
- React Hook Form for admin forms

These choices fit the current stage because they give the project:
- layout and route composition without custom plumbing
- a straightforward styling workflow for rapid iteration
- a standard server-state boundary for backend-driven screens

## 3. Repository Placement

The frontend lives in:
- [frontend/](../frontend/)

Main directories:
- `app/`: route tree, root layout and the backend proxy route
- `src/components/`: shared layout, UI and state components
- `src/hooks/`: TanStack Query hooks for backend-facing data
- `src/lib/`: frontend config, API client and utilities
- `src/components/graphs/`: shared graph explorer UI
- `src/lib/graphs/`: graph payload mapping and explorer-specific helpers
- `src/components/admin/`: admin console navigation, operations and manual data entry UI

## 4. Application Shell

The shell is intentionally simple but already stable:
- persistent sidebar navigation
- shared header framing the current iteration
- implemented routes for overview, dashboard, entities, graphs and admin workflows

This is enough to avoid restructuring later when richer views arrive.

## 5. Backend Integration

The frontend uses a proxy route instead of calling FastAPI directly from the browser.

Proxy route:
- [frontend/app/api/backend/[...path]/route.ts](../frontend/app/api/backend/[...path]/route.ts)

Why this choice:
- keeps the browser API base path stable
- avoids local CORS friction
- allows the actual backend origin to stay configurable on the server side

Relevant settings:
- `EUNIGRAPH_BACKEND_URL`: actual FastAPI base URL used by the proxy
- `NEXT_PUBLIC_API_BASE_URL`: frontend-visible base path, default `/api/backend`

Typical values:
- local host run: `EUNIGRAPH_BACKEND_URL=http://localhost:8000`
- Docker Compose run: `EUNIGRAPH_BACKEND_URL=http://backend:8000`

## 6. Server-State Pattern

TanStack Query is the default pattern for backend-driven screens.

Current hooks:
- backend health
- embeddings status
- coauthorship graph status
- semantic graph status
- publication preview
- admin workflow status and mutations
- manual entity creation mutations

The current implementation uses these hooks to prove:
- the shell can read the backend
- loading, error and empty states are centralized
- future pages can reuse the same pattern
- backend-triggered operations stay behind an explicit query/mutation boundary

## 7. Route Structure

Current routes:
- `/`: overview and integration status
- `/dashboard`: dashboard overview with workflow status, catalog snapshot and quick search
- `/entities`: catalog hub
- `/entities/publications`: publication browsing
- `/entities/publications/[id]`: publication detail
- `/entities/researchers`: researcher browsing
- `/entities/researchers/[id]`: researcher detail
- `/entities/organizations`: organization browsing
- `/entities/organizations/[id]`: organization detail
- `/graphs`: unified graph explorer for coauthorship and semantic layers
- `/admin`: admin console overview
- `/admin/operations`: administrative workflow controls
- `/admin/data-entry`: manual canonical entity creation

Supporting routes:
- `loading`
- `error`
- `not-found`

## 8. Dashboard and Browsing Experience

The current frontend goes beyond the initial shell foundation.

Dashboard:
- combines backend health, embeddings status and graph build status
- composes pragmatic catalog counts from existing list endpoints
- exposes a quick cross-entity search that reuses backend filters rather than inventing a new client-only search model

Entity browsing:
- publications can be filtered by title, DOI, year and OpenAIRE id
- researchers can be filtered by name, ORCID and route-linked organization scope
- organizations can be filtered by name, type and route-linked parent organization scope

Detail views:
- publication detail resolves authors, organizations and embedding metadata
- researcher detail resolves affiliation context
- organization detail resolves child organizations and primary researchers

## 9. Styling Direction

The frontend intentionally avoids a generic white-purple dashboard look.

Current direction:
- warm sand and mist background
- pine and ember accents
- soft glass-like panels
- compact but editorial typography

This gives the prototype a visual identity without locking the project into a full design system too early.

## 10. Docker and Runtime

The Compose profile `ui` is the current entry point for the full local stack:
- backend
- postgres
- qdrant
- frontend

The frontend container mounts the project workspace and receives the backend URL through environment variables.

## 11. Current Limits

The frontend foundation deliberately stops short of:
- advanced graph analytics and saved graph-view workflows
- editing workflows for existing canonical records and relation management
- authentication
- cross-entity aggregated search endpoint support
- backend-driven total counts for catalog metrics

These are deferred to later issues now that the structural groundwork and first browsing experience are in place.

## 12. Graph Experience

The graph explorer is now a real frontend surface rather than a placeholder.

The current design principle is:
- same UI pattern for both coauthorship and semantic graph layers
- different node and edge meaning depending on the selected layer

Dedicated documentation:
- [frontend-graph-explorer.md](frontend-graph-explorer.md)

## 13. Admin Console

The admin console is a dedicated frontend section for prototype operations and controlled data creation.

It is split into:
- `Operations`: seed, normalization, embeddings and graph build/status workflows
- `Manual Data Entry`: creation forms for publications, researchers and organizations

Dedicated documentation:
- [frontend-admin-console.md](frontend-admin-console.md)
