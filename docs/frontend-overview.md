# Frontend Overview

## 1. Purpose

The frontend provides the application shell for EuniGraph:
- shared navigation
- route boundaries for the next product slices
- a clean integration layer toward the FastAPI backend
- reusable patterns for loading, error and empty states

This first iteration does not attempt to deliver the final dashboard or graph explorer. Its role is to create a stable, documented foundation for the UI work that follows.

## 2. Stack

The frontend is built with:
- Next.js with App Router
- Tailwind CSS
- TanStack Query

These choices fit the current stage because they give the project:
- layout and route composition without custom plumbing
- a straightforward styling workflow for rapid iteration
- a standard server-state boundary for backend-driven screens

## 3. Repository Placement

The frontend lives in:
- [frontend/](/Users/cristianopistorio/Code/GitHub/EuniGraph/frontend)

Main directories:
- `app/`: route tree, root layout and the backend proxy route
- `src/components/`: shared layout, UI and state components
- `src/hooks/`: TanStack Query hooks for backend-facing data
- `src/lib/`: frontend config, API client and utilities

## 4. Application Shell

The shell is intentionally simple but already stable:
- persistent sidebar navigation
- shared header framing the current iteration
- route placeholders for overview, dashboard, entities and graphs

This is enough to avoid restructuring later when richer views arrive.

## 5. Backend Integration

The frontend uses a proxy route instead of calling FastAPI directly from the browser.

Proxy route:
- [frontend/app/api/backend/[...path]/route.ts](/Users/cristianopistorio/Code/GitHub/EuniGraph/frontend/app/api/backend/[...path]/route.ts)

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

The current implementation uses these hooks to prove:
- the shell can read the backend
- loading, error and empty states are centralized
- future pages can reuse the same pattern

## 7. Route Structure

Current routes:
- `/`: overview and integration status
- `/dashboard`: workflow-oriented placeholder
- `/entities`: canonical catalog placeholder with publication preview
- `/graphs`: graph-oriented placeholder

Supporting routes:
- `loading`
- `error`
- `not-found`

## 8. Styling Direction

The frontend intentionally avoids a generic white-purple dashboard look.

Current direction:
- warm sand and mist background
- pine and ember accents
- soft glass-like panels
- compact but editorial typography

This gives the prototype a visual identity without locking the project into a full design system too early.

## 9. Docker and Runtime

The Compose profile `ui` is the current entry point for the full local stack:
- backend
- postgres
- qdrant
- frontend

The frontend container mounts the project workspace and receives the backend URL through environment variables.

## 10. Current Limits

The frontend foundation deliberately stops short of:
- full dashboard composition
- graph visualization
- advanced entity browsing
- editing workflows
- authentication

These are deferred to later issues now that the structural groundwork is in place.
