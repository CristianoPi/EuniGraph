# Semantic Similarity Graph Pipeline

## Purpose

This document describes how EuniGraph builds, persists and serves the semantic similarity graph.

The goal is to transform publication embeddings already stored in Qdrant into a materialized publication-publication graph that can be reused by APIs and the frontend graph explorer without rebuilding on every request.

## Data Sources

The semantic graph is built from:
- Qdrant as the source of vector nearest neighbors
- PostgreSQL as the canonical source of publication metadata
- `publication_embedding` as the explicit bridge between canonical publications and Qdrant points

Nodes are canonical `publication` entities.

Edges are derived from nearest-neighbor retrieval over the Qdrant publication collection.

## Build Strategy

The MVP uses:
- an undirected graph
- no self-loops
- no duplicate edges
- `top_k + score_threshold` pruning
- score-based edge weights
- optional `mutual_knn`

The default behavior is:
- `top_k = 5`
- `score_threshold = 0.75`
- `edge_symmetry_policy = max_score_union`
- `mutual_knn = false`

### Edge Construction

For each publication with an active embedding:
1. query nearest neighbors from Qdrant
2. discard self-matches
3. keep up to `top_k` valid neighbors after filtering
4. drop neighbors below the configured threshold
5. convert directional nearest-neighbor links into one undirected edge per publication pair

Current edge fields include:
- `source`
- `target`
- `weight`
- `similarity_score`
- `rank`
- `mutual_match`
- `source_rank`
- `target_rank`
- `source_score`
- `target_score`

With `edge_symmetry_policy = max_score_union`, one-sided matches are allowed and the undirected edge keeps the best score observed across directions.

With `mutual_knn = true` or `edge_symmetry_policy = mutual_only`, only reciprocal nearest-neighbor matches are kept.

## Build Parameters

The build API exposes these parameters:
- `top_k`
- `score_threshold`
- `edge_symmetry_policy`
- `mutual_knn`
- `include_isolated_nodes`
- optional `publication_type`
- optional `language_code`
- optional `year_from`
- optional `year_to`

The resolved build metadata also records:
- Qdrant collection
- Qdrant distance metric
- embedding provider
- embedding model
- embedding version
- weight strategy

## Materialization and Storage

The semantic graph is materialized exactly once per build and stored on disk.

Default storage path:
- `data/graphs/semantic/`

Each build writes:
- `semantic_graph.gt`
- `semantic_graph.json`
- `semantic_graph.svg`

The backend Docker setup already mounts `data/graphs/` as persistent writable storage.

## Build Tracking

Each build is tracked in PostgreSQL through `semantic_graph_build`.

Tracked metadata includes:
- build status
- start and completion timestamps
- resolved build parameters
- source snapshot
- artifact paths
- node and edge counts
- component and community counts
- graph version hash
- last error if the build failed

Only the latest successful active build is used by retrieval endpoints.

## Retrieval Model

Retrieval APIs never rebuild the graph live.

They read the persisted JSON artifact of the latest successful build and expose:
- the full graph
- filtered subgraphs
- graph-level metrics
- node-level metrics
- a static SVG visualization

## Available Endpoints

- `POST /api/v1/semantic-graph/build`
- `GET /api/v1/semantic-graph/status`
- `GET /api/v1/semantic-graph`
- `GET /api/v1/semantic-graph/subgraph`
- `GET /api/v1/semantic-graph/metrics`
- `GET /api/v1/semantic-graph/nodes/{publication_id}`
- `GET /api/v1/semantic-graph/visualization`

## Current Limitations

- no automatic rebuild after embedding refreshes
- no query-time semantic search endpoint yet
- no cross-modal similarity graph
- score semantics depend on the Qdrant collection distance currently configured
- organization filters operate on already materialized publication-organization links, not on a dedicated semantic index
