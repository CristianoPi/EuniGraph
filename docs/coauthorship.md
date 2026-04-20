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
- each node carries:
  - the researcher's `primary_organization_id` and `primary_organization_name`
  - an EUNICE attribution payload:
    - `university_code`
    - `university_name`
    - `is_eunice_university`

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

## EUNICE University Attribution

The coauthorship payload still exposes:
- `primary_organization_id`
- `primary_organization_name`

In addition, the build now derives a governed EUNICE university attribution for each node when possible:
- `university_code`
- `university_name`
- `is_eunice_university`

Attribution rule:
1. try to resolve the researcher's `primary_organization`
2. if needed, walk `organization.parent_organization_id` to collapse departments and child organizations to a supported university
3. if `primary_organization` is not attributable, inspect `researcher_affiliation`
4. if affiliations resolve to exactly one EUNICE university, use it
5. if affiliations resolve to multiple EUNICE universities or no governed university, leave the node unattributed

This logic is intentionally governed and closed:
- only known EUNICE universities are mapped
- non-EUNICE organizations do not receive arbitrary institutional colors
- ambiguous cases fall back to a neutral visual state

Frontend rendering precedence is slightly more permissive for readability:
- if `university_code` is available, use the institutional EUNICE palette
- otherwise, if `primary_organization_id` exists, use the deterministic organization fallback color already used by the MVP explorer
- only nodes with no university attribution and no organization context stay neutral gray

## Institutional Palette

The governed palette currently used for coauthorship nodes is:
- `karlstad` -> `#F4E600`
- `vaasa` -> `#F5C439`
- `btu` -> `#A6C60D`
- `poznan-tech` -> `#00618E`
- `unict` -> `#007DCB`
- `peloponnese` -> `#A51317`
- `cantabria` -> `#438D96`
- `viseu` -> `#010101`
- `umons` -> `#B60038`
- `uphf` -> `#46B6C6`

The same university code is also reused by the persisted SVG artifact colorization so API payloads, interactive frontend rendering and static graph artifacts stay aligned.

## Current Limitations

- builds are explicit and synchronous; there is no background job orchestration yet
- retrieval uses the materialized JSON payload, not direct reopening of the `.gt` file
- edge metadata currently focuses on shared publications and collaboration years
- attribution still depends on canonical `primary_organization` and `researcher_affiliation` quality
- multi-university affiliation cases remain intentionally unresolved
- no incremental update strategy is implemented yet
- no dedicated manual review workflow exists for graph anomalies or author disambiguation effects
