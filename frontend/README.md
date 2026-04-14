# Frontend

The frontend is now a real application workspace built with:
- Next.js App Router
- Tailwind CSS
- TanStack Query

It provides:
- the shared application shell
- the first navigable route structure
- a proxy-based integration layer toward the FastAPI backend
- reusable loading, error and empty states

## Local Run

1. Copy the frontend environment template:
   `cp frontend/.env.example frontend/.env.local`
2. Install dependencies:
   `cd frontend && npm install`
3. Start the app:
   `npm run dev`

By default the local frontend proxies backend calls to:
- `http://localhost:8000`

## Docker Run

The Docker profile `ui` starts the frontend together with the backend stack:

`docker compose --profile ui up --build`

In Docker the frontend proxy targets:
- `http://backend:8000`

## Structure

- `app/`: App Router routes, root layout and backend proxy route
- `src/components/`: shared layout, UI and state components
- `src/hooks/`: TanStack Query hooks for backend-facing server state
- `src/lib/`: config, API client and small frontend utilities

See [docs/frontend-overview.md](/Users/cristianopistorio/Code/GitHub/EuniGraph/docs/frontend-overview.md) for the technical overview.
