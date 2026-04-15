# Frontend Graph Explorer

## 1. Purpose

The graph explorer is the first interactive visualization surface of EuniGraph.

It exposes two backend graph layers through one shared frontend pattern:
- coauthorship graph
- semantic similarity graph

The goal is to make the difference between the two graphs semantic, not structural. The user changes layer, but stays inside the same exploration experience.

## 2. Route

The unified explorer currently lives at:
- [frontend/app/graphs/page.tsx](../frontend/app/graphs/page.tsx)

Frontend URL:
- `/graphs`

## 3. Stack and Rendering

The graph experience uses:
- Next.js App Router for route composition
- TanStack Query for backend retrieval and caching
- Cytoscape.js for interactive graph rendering

The frontend does not rebuild graphs. It only consumes the materialized graph payloads already produced by the backend.

## 4. Shared Interaction Pattern

Both graph layers share the same UI structure:
- layer switcher
- filter and focus controls
- canvas area
- loading, error and empty states
- detail panel for selected node or edge
- view reset and selection centering

Shared interactions:
- zoom by wheel or trackpad
- pan by dragging the background
- node selection
- edge selection
- focus on selected node neighborhood
- reset of filters and viewport

## 5. Backend APIs Used

### Coauthorship
- `GET /api/v1/coauthorship-graph/status`
- `GET /api/v1/coauthorship-graph`
- `GET /api/v1/coauthorship-graph/subgraph`
- `GET /api/v1/coauthorship-graph/metrics`
- `GET /api/v1/coauthorship-graph/nodes/{researcher_id}`

### Semantic
- `GET /api/v1/semantic-graph/status`
- `GET /api/v1/semantic-graph`
- `GET /api/v1/semantic-graph/subgraph`
- `GET /api/v1/semantic-graph/metrics`
- `GET /api/v1/semantic-graph/nodes/{publication_id}`

## 6. Filter Model

The explorer only exposes filters already supported by the backend.

### Coauthorship filters
- `researcher_id`
- `organization_id`
- `max_nodes`
- `min_edge_weight`
- `community_id`

### Semantic filters
- `publication_id`
- `organization_id`
- `publication_year`
- `max_nodes`
- `min_edge_weight`
- `community_id`

When no filter is active, the explorer loads the full persisted graph payload.

When a filter is active, the explorer loads a backend subgraph instead of pruning locally.

## 7. Detail Panels

### Coauthorship node detail
- researcher identity
- degree, strength and betweenness
- organization context
- component and community ids
- quick link to the researcher detail route

### Semantic node detail
- publication identity
- year, DOI, venue and metrics
- author list
- quick link to the publication detail route

### Edge detail
- coauthorship: collaboration weight and collaboration years
- semantic: similarity score, weight, rank and mutual match information

## 8. Internal Frontend Structure

Main files:
- [frontend/src/components/graphs/unified-graph-explorer.tsx](../frontend/src/components/graphs/unified-graph-explorer.tsx)
- [frontend/src/components/graphs/graph-controls.tsx](../frontend/src/components/graphs/graph-controls.tsx)
- [frontend/src/components/graphs/graph-detail-panel.tsx](../frontend/src/components/graphs/graph-detail-panel.tsx)
- [frontend/src/components/graphs/graph-canvas.tsx](../frontend/src/components/graphs/graph-canvas.tsx)
- [frontend/src/hooks/use-graphs.ts](../frontend/src/hooks/use-graphs.ts)
- [frontend/src/lib/api/graphs.ts](../frontend/src/lib/api/graphs.ts)
- [frontend/src/lib/graphs/mappers.ts](../frontend/src/lib/graphs/mappers.ts)

## 9. Difference Between the Two Layers

The UX is shared, but the node and edge semantics differ:

### Coauthorship graph
- nodes are researchers
- edges represent shared publications
- edge weight is collaboration intensity

### Semantic graph
- nodes are publications
- edges represent semantic similarity from Qdrant nearest neighbors
- edge weight is similarity-driven

## 10. Current MVP Limits

- no advanced graph analytics UI yet
- no dynamic styling controls or saved graph views
- no hover tooltips beyond selection-driven detail panels
- no client-side graph editing
- no background refresh or realtime synchronization

The explorer is intentionally focused on reliable retrieval and readable exploration of the materialized backend graphs.
