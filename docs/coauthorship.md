# Coauthorship Graph Pipeline

## Purpose

This document describes how EuniGraph builds, persists and serves the coauthorship graph.

The graph is a materialized projection of canonical relational data. It is not rebuilt during retrieval APIs.

## Source Data

The current build reads from canonical PostgreSQL tables:
- `researcher`
- `publication`
- `publication_author`

Node derivation:
- one node per canonical `researcher` that appears in `publication_author`
- optional isolated nodes for researchers with only solo-authored publications

Edge derivation:
- one undirected edge between two researchers when they co-author at least one publication
- edge `weight` equals the number of shared publications
- edge metadata also tracks:
  - `shared_publication_count`
  - `first_collaboration_year`
  - `last_collaboration_year`
  - `shared_publication_ids`

## Build Strategy

The build is an explicit pipeline step exposed by:
- `POST /api/v1/coauthorship-graph/build`

The current MVP executes synchronously and performs these steps:
1. read canonical authorship data from PostgreSQL
2. aggregate researcher pairs into weighted coauthorship edges
3. build a `graph-tool` graph in memory
4. compute node metrics and graph partitions
5. serialize graph artifacts to persistent storage
6. persist build metadata in PostgreSQL
7. mark the successful build as the active one

If a build fails:
- the build is persisted with `status=failed`
- the previous successful active build remains available for retrieval

## Metrics

Current node metrics:
- `degree`
- `strength` as weighted degree
- `betweenness`
- `component_id`
- `community_id` when blockmodel community detection succeeds

Current graph-level summary:
- node count
- edge count
- connected component count
- community count
- graph version hash

Community detection is intentionally best-effort in the MVP. If `graph-tool` blockmodel inference fails for a specific build, the graph still completes without `community_id`.

## Persistence

### Build metadata

Each build is tracked in PostgreSQL through `coauthorship_graph_build`.

Tracked fields include:
- graph type
- build status
- timestamps
- build parameters
- node and edge counts
- component and community counts
- graph version hash
- artifact paths
- data snapshot metadata
- active flag
- error message for failed builds

### Artifact storage

The default storage path is configured through:
- `EUNIGRAPH_COAUTHORSHIP_GRAPH_STORAGE_PATH`

Default value:
- `data/graphs/coauthorship/`

Each build stores its own directory containing:
- `coauthorship.gt`
- `coauthorship.json`
- `coauthorship.svg`

The backend Docker setup mounts `data/graphs/` as writable persistent storage.

## Retrieval APIs

The current API surface is:
- `POST /api/v1/coauthorship-graph/build`
- `GET /api/v1/coauthorship-graph/status`
- `GET /api/v1/coauthorship-graph`
- `GET /api/v1/coauthorship-graph/subgraph`
- `GET /api/v1/coauthorship-graph/metrics`
- `GET /api/v1/coauthorship-graph/nodes/{researcher_id}`
- `GET /api/v1/coauthorship-graph/visualization`

Retrieval behavior:
- `GET /coauthorship-graph` returns the persisted JSON payload of the active build
- `GET /coauthorship-graph/subgraph` filters the persisted payload, not the relational source data
- `GET /coauthorship-graph/metrics` returns graph summary plus top nodes by key metrics
- `GET /coauthorship-graph/nodes/{researcher_id}` returns one materialized node plus incident edges and neighbors
- `GET /coauthorship-graph/visualization` serves the persisted static SVG artifact

## Versioning and Snapshot

Each build stores:
- a stable graph hash derived from node identities, organization context and weighted edges
- a lightweight data snapshot with counts and latest update timestamps from source tables

This is intended for traceability and for later decisions about rebuild cadence.

## Current Limitations

- builds are explicit and synchronous; there is no background job orchestration yet
- retrieval uses the materialized JSON payload, not direct reopening of the `.gt` file
- edge metadata currently focuses on shared publications and collaboration years
- organization context is limited to the researcher's primary organization
- no incremental update strategy is implemented yet
- no dedicated manual review workflow exists for graph anomalies or author disambiguation effects
