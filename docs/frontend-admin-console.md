# Frontend Admin Console

## 1. Purpose

The admin console is the frontend surface for operating the EuniGraph prototype without relying on Swagger or manual API calls for every demo action.

It is intentionally separated from public browsing surfaces:
- browsing and graph exploration remain focused on reading canonical data
- admin operations trigger backend workflows and mutate system state
- manual data entry creates controlled canonical records through existing backend APIs

The console does not introduce new backend logic. It consumes the APIs already exposed by the FastAPI modular monolith.

## 2. Routes

The admin area currently exposes:
- `/admin`: overview and entry point
- `/admin/operations`: administrative workflow controls
- `/admin/data-entry`: manual creation forms for canonical entities

The root application navigation links to `/admin`, while the admin area has its own internal navigation between operations and manual data entry.

## 3. Frontend Structure

Main files:
- [frontend/app/admin/page.tsx](../frontend/app/admin/page.tsx)
- [frontend/app/admin/layout.tsx](../frontend/app/admin/layout.tsx)
- [frontend/app/admin/operations/page.tsx](../frontend/app/admin/operations/page.tsx)
- [frontend/app/admin/data-entry/page.tsx](../frontend/app/admin/data-entry/page.tsx)
- [frontend/src/components/admin/admin-nav.tsx](../frontend/src/components/admin/admin-nav.tsx)
- [frontend/src/components/admin/operations-console.tsx](../frontend/src/components/admin/operations-console.tsx)
- [frontend/src/components/admin/manual-data-entry.tsx](../frontend/src/components/admin/manual-data-entry.tsx)
- [frontend/src/hooks/use-admin.ts](../frontend/src/hooks/use-admin.ts)
- [frontend/src/lib/api/admin.ts](../frontend/src/lib/api/admin.ts)

The implementation follows the existing frontend conventions:
- Next.js App Router for route composition
- TanStack Query for backend status queries and mutations
- React Hook Form for operational forms and manual data entry forms
- existing shared UI components for panels, loading states and error states
- the existing `/api/backend` proxy route for FastAPI calls

## 4. Operations Area

The operations view groups backend-triggered workflows that change system state or materialized artifacts.

Supported operations:
- inspect OpenAIRE Beginner's Kit seed status
- load OpenAIRE seed data, optionally with `limit_per_file`
- reset OpenAIRE seed data with explicit destructive-action confirmation
- inspect normalization status
- run normalization with optional notes
- inspect latest normalization findings
- inspect embeddings provider and status
- build selected publication embeddings
- load all publication embeddings
- reset the active embeddings collection with explicit destructive-action confirmation
- inspect coauthorship graph status
- build/rebuild the coauthorship graph
- inspect semantic graph status
- build/rebuild the semantic graph with backend-supported parameters

After successful mutations, the frontend invalidates related TanStack Query caches so dashboard, catalog, embeddings and graph status surfaces can refresh from backend state.

## 5. Manual Data Entry Area

The manual data entry view creates the three primary canonical entity types required by the MVP:
- publications
- researchers
- organizations

Each form calls the existing canonical API endpoint:
- `POST /api/v1/publications`
- `POST /api/v1/researchers`
- `POST /api/v1/organizations`

The backend remains responsible for:
- validation
- canonical normalization fields
- integrity constraints
- manual provenance through `manual_api_entry`

After creation, the UI shows success feedback and links to the corresponding public detail view.

## 6. Backend APIs Used

Admin and workflow APIs:
- `GET /api/v1/admin/seeds/openaire-beginners-kit/status`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/load`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/reset`
- `GET /api/v1/admin/normalization/status`
- `POST /api/v1/admin/normalization/run`
- `GET /api/v1/admin/normalization/findings`
- `GET /api/v1/embeddings/provider`
- `GET /api/v1/embeddings/status`
- `POST /api/v1/embeddings/build`
- `POST /api/v1/embeddings/load-all`
- `POST /api/v1/embeddings/reset`
- `GET /api/v1/coauthorship-graph/status`
- `POST /api/v1/coauthorship-graph/build`
- `GET /api/v1/semantic-graph/status`
- `POST /api/v1/semantic-graph/build`

Manual entity APIs:
- `POST /api/v1/publications`
- `POST /api/v1/researchers`
- `POST /api/v1/organizations`

The console deliberately does not call relation-creation APIs yet, although the backend already exposes endpoints for publication authors, researcher affiliations and publication organizations.

## 7. Feedback Model

The admin console handles:
- loading states for status queries and pending mutations
- success states after completed mutations
- FastAPI error responses through the existing `ApiError` detail handling
- explicit warnings and confirmation checkboxes for destructive reset operations

The current backend executes these workflows synchronously. The frontend therefore reports completion when the backend response returns; it does not implement realtime orchestration or background progress tracking.

## 8. Current MVP Limits

Current limits are intentional for this issue:
- no authentication or role-based authorization
- no audit-trail frontend beyond backend provenance behavior
- no advanced editing of existing entities
- no relation management UI for authorships, affiliations or publication-organization links
- no realtime job progress or background polling orchestration
- no human-in-the-loop review UI for normalization findings

These can be added later without changing the current route split between operations and manual data entry.
