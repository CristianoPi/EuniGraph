# Seed And API Notes

## OpenAIRE Beginner's Kit Path

The local dataset path is configured through:

- `OPENAIRE_BEGINNERS_KIT_PATH`

Default development value:

- `data/openaire/beginners_kit/`

Required archive files for the MVP seed:
- `publication.tar`
- `organization.tar`
- `datasource.tar`
- `project.tar`
- `relation.tar`

If the path or any required archive is missing, the seed loader returns a clear validation error before ingesting data.

## Seed Execution

CLI commands:
- `make backend-seed-openaire`
- `make backend-reset-openaire-seed`
- `make backend-seed-status`

Direct module invocation:

```bash
cd backend
uv run python -m eunigraph.modules.ingestion.application.seed_cli load
uv run python -m eunigraph.modules.ingestion.application.seed_cli load --limit-per-file 100
uv run python -m eunigraph.modules.ingestion.application.seed_cli status
uv run python -m eunigraph.modules.ingestion.application.seed_cli reset
```

Current verified behavior:
- `limit_per_file=200` completes successfully
- `limit_per_file=500` completes successfully in the current development dataset
- the CLI `status` command returns the dataclass payload correctly

Seed runtime logging now emits:
- seed start with dataset path and `limit_per_file`
- archive phase start, progress and completion
- processed record counters
- readable failure context including phase, archive and processed record count

## OpenAIRE Graph EUNICE Seed Path

The backend now also exposes a targeted seed workflow for demo-oriented datasets:

- source type: `openaire_graph_eunice`
- logical source name: `OpenAIRE Graph EUNICE Seed`
- default Graph API base URL: `https://api.openaire.eu/graph`

Relevant configuration:

- `OPENAIRE_GRAPH_API_BASE_URL`
- `OPENAIRE_GRAPH_API_TIMEOUT_SECONDS`
- `OPENAIRE_GRAPH_API_PAGE_SIZE`
- `OPENAIRE_EUNICE_SEED_MAX_PUBLICATIONS`

The workflow uses the OpenAIRE Graph API v2 and fetches only research products filtered by:

- `relCommunityId=eunice`
- `type=publication`

The current implementation intentionally stays publication-centered because the canonical model, browsing UI and graph layers are all publication-first.

## EUNICE Seed Scope

The EUNICE seed imports only data relevant to the OpenAIRE community slice for `eunice`:

- `publication` rows returned by `GET /graph/v2/researchProducts?relCommunityId=eunice&type=publication`
- `organization` rows embedded in publication metadata
- `researcher` rows derived from publication author metadata
- `publication_author`
- `publication_organization`
- `researcher_affiliation` derived through a demo-focused rule
- `external_identifier`
- provenance in `source_record`

It does not depend on the local Beginner's Kit archives.

## EUNICE Seed API Syntax

Confirmed source-of-truth syntax for the current workflow:

- all research products in the community:
  - `GET https://api.openaire.eu/graph/v2/researchProducts?relCommunityId=eunice`
- publications only:
  - `GET https://api.openaire.eu/graph/v2/researchProducts?relCommunityId=eunice&type=publication`

The implemented seed uses the publication-only variant.

OpenAIRE Graph documentation also states that `v2/researchProducts` responses contain `organizations` and `communities`, which is what the current mapping relies on.

## EUNICE Affiliation Rule

OpenAIRE Graph v2 publications expose `authors`, `organizations` and `communities`, but they still do not provide a stable per-author affiliation assignment ready to copy directly into the canonical model.

The current EUNICE seed therefore applies a deliberate demo heuristic:

- all embedded publication organizations are imported into the canonical `organization` table
- embedded organizations are deduplicated conservatively inside each publication payload, preferring stable `openorgs` records over `pending_org` variants
- if a publication ends up linked to exactly one canonical organization after that deduplication, all imported authors of that publication receive a `researcher_affiliation` to that organization
- if a publication still resolves to multiple canonical organizations, the case is treated as ambiguous and no `researcher_affiliation` is derived from that publication
- when a researcher ends up with exactly one affiliation in the loaded dataset slice, `researcher.primary_organization_id` is also aligned automatically by the existing canonical helper

This keeps the dataset useful for demo browsing and coauthorship coloring without pretending to solve full person-level affiliation resolution.

## Current Seed Scope

The seed currently reads and persists raw provenance from:
- publications
- organizations
- datasources
- projects
- relations

Canonical entities currently populated by the seed:
- `publication`
- `researcher`
- `organization`
- `publication_author`
- `publication_organization`
- `researcher_affiliation` for conservative derived cases
- `external_identifier`
- raw provenance tables

Current deliberate limit:
- `project.tar` and `datasource.tar` are preserved in `source_record` but not yet mapped to canonical tables beyond the logical `data_source` record used for ingestion provenance

Loader robustness notes:
- raw OpenAIRE payloads remain preserved in `source_record.raw_payload`
- duplicate `source_record` identifiers inside the same ingestion run are skipped and logged instead of failing the entire seed
- conflicting external publication identifiers are skipped and logged when the same `(entity_type, identifier_type, identifier_value)` reappears for a different canonical publication in the same run
- unique-field collisions on canonical entities are handled conservatively during the seed:
  - `organization.ror_id`
  - `organization.openaire_id`
  - `researcher.orcid`
  - `publication.doi`
  - `publication.openaire_id`
  conflicting values are skipped and logged instead of aborting the run
- bounded canonical text fields are clipped conservatively when source values exceed schema column lengths
- author links are deduplicated per publication before insert
- duplicate or invalid author ranks are normalized to the next available `author_position`
- `publication.language_code` prefers compact codes such as `eng` over verbose labels such as `English`
- duplicate publication-organization relations inside the same run are skipped and logged
- `researcher_affiliation` is derived only from `relation.tar` affiliation relations that connect one publication to one organization and can be linked to a publication with exactly one canonical author
- when a researcher receives exactly one derived organization across the loaded seed slice, that organization is also assigned to `researcher.primary_organization_id`
- multi-author affiliation relations remain intentionally unresolved because the Beginner's Kit relation does not identify which author matches which organization
- `limit_per_file` is applied independently per archive, so small partial loads can produce poor cross-archive overlap and therefore under-populate relation-derived tables such as `publication_organization` and `researcher_affiliation`

## Available APIs

Main CRUD/demo endpoints:
- `GET /api/v1/publications`
- `GET /api/v1/publications/{id}`
- `POST /api/v1/publications`
- `PATCH /api/v1/publications/{id}`
- `GET /api/v1/publications/{id}/authors`
- `POST /api/v1/publications/{id}/authors`
- `GET /api/v1/publications/{id}/organizations`
- `POST /api/v1/publications/{id}/organizations`

- `GET /api/v1/researchers`
- `GET /api/v1/researchers/{id}`
- `POST /api/v1/researchers`
- `PATCH /api/v1/researchers/{id}`
- `GET /api/v1/researchers/{id}/affiliations`
- `POST /api/v1/researchers/{id}/affiliations`

- `GET /api/v1/organizations`
- `GET /api/v1/organizations/{id}`
- `POST /api/v1/organizations`
- `PATCH /api/v1/organizations/{id}`

- `GET /api/v1/source-records`
- `GET /api/v1/source-records/{id}`

Development seed/admin endpoints:
- `GET /api/v1/admin/seeds/openaire-beginners-kit/status`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/load`
- `POST /api/v1/admin/seeds/openaire-beginners-kit/reset`
- `GET /api/v1/admin/seeds/openaire-graph-eunice/status`
- `POST /api/v1/admin/seeds/openaire-graph-eunice/load`
- `POST /api/v1/admin/normalization/run`
- `GET /api/v1/admin/normalization/status`
- `GET /api/v1/admin/normalization/findings`

Coauthorship graph endpoints:
- `POST /api/v1/coauthorship-graph/build`
- `GET /api/v1/coauthorship-graph/status`
- `GET /api/v1/coauthorship-graph`
- `GET /api/v1/coauthorship-graph/subgraph`
- `GET /api/v1/coauthorship-graph/metrics`
- `GET /api/v1/coauthorship-graph/nodes/{researcher_id}`
- `GET /api/v1/coauthorship-graph/visualization`

Semantic graph endpoints:
- `POST /api/v1/semantic-graph/build`
- `GET /api/v1/semantic-graph/status`
- `GET /api/v1/semantic-graph`
- `GET /api/v1/semantic-graph/subgraph`
- `GET /api/v1/semantic-graph/metrics`
- `GET /api/v1/semantic-graph/nodes/{publication_id}`
- `GET /api/v1/semantic-graph/visualization`

Embeddings endpoints:
- `GET /api/v1/embeddings/provider`
- `GET /api/v1/embeddings/status`
- `POST /api/v1/embeddings/build`
- `POST /api/v1/embeddings/load-all`
- `POST /api/v1/embeddings/reset`
- `POST /api/v1/publications/{id}/embedding`
- `GET /api/v1/publications/{id}/embedding`

## Manual Canonical Entity Management

The main domain endpoints are also the manual entity management APIs for the MVP.

Supported manual writes:
- create and patch `publication`
- create and patch `researcher`
- create and patch `organization`
- create `publication_author`
- create `researcher_affiliation`
- create `publication_organization`

Manual writes are validated at the API boundary with pragmatic checks such as:
- `publication_year` must stay in the supported canonical range
- `author_position` must be greater than or equal to 1
- `country_code` is normalized to ISO-like uppercase two-letter form
- empty identifiers such as DOI, OpenAIRE id, ORCID are normalized away
- affiliation date ranges reject `end_date < start_date`

Integrity and collision errors are returned as readable `400` responses instead of surfacing raw database failures.

## Manual Provenance

Manual API writes are tracked through the existing provenance layer.

Implementation choices:
- logical `data_source.source_type = manual_api_entry`
- one short `ingestion_run` per manual write operation
- one `source_record` per create/update request

The `source_record.raw_payload` stores:
- action type such as `create` or `update`
- canonical entity type
- canonical entity id
- original API payload

Direct linkage behavior:
- `publication` updates `canonical_source_record_id`
- `publication_author`, `researcher_affiliation`, and `publication_organization` store `source_record_id`
- `researcher` and `organization` provenance is recoverable via `source_record.raw_payload.canonical_entity_id`

This keeps manual data distinguishable from:
- OpenAIRE Beginner's Kit seed data
- future automated ingestion pipelines
- future development-only bootstrap data

Useful provenance filters on `GET /api/v1/source-records`:
- `source_type`
- `canonical_entity_id`
- `entity_type`
- `source_identifier`
- `data_source_id`
- `ingestion_run_id`

This makes it possible to inspect, for example:
- only manual API provenance with `source_type=manual_api_entry`
- all provenance rows linked to one canonical entity with `canonical_entity_id=<uuid>`

## Seed Failure Semantics

The OpenAIRE seed loader should no longer fail with an opaque generic `500` for the known ingestion-path issues addressed in the MVP.

Current behavior:
- `400` for dataset path or archive validation problems, and for archive/parsing failures
- `409` for database persistence conflicts or schema-bound data issues encountered during ingestion
- `503` for resource exhaustion such as `MemoryError`

For the EUNICE Graph seed specifically:

- `400` is used for invalid target keys, unresolved configured organizations, or invalid year ranges
- `409` is used for canonical persistence conflicts
- `503` is used for OpenAIRE Graph API transport or response-shape failures

Readable seed failures include:
- failure category
- execution stage
- archive name when available
- processed record count when available
- `limit_per_file` when set

Failed ingestion runs are also persisted with `status=failed`, `completed_at`, and contextual notes so the last run status remains inspectable after rollback.

## Coauthorship Materialization

The coauthorship graph is materialized from canonical PostgreSQL data and then served from persisted artifacts.

Input tables:
- `researcher`
- `publication`
- `publication_author`

Persisted outputs:
- a `graph-tool` binary graph file
- a JSON payload used by retrieval APIs
- a static SVG visualization
- build metadata in `coauthorship_graph_build`

Default artifact path:
- `EUNIGRAPH_COAUTHORSHIP_GRAPH_STORAGE_PATH`
- default value: `data/graphs/coauthorship/`

Retrieval endpoints always use the latest successful active build. A failed rebuild does not force the API to reconstruct the graph live.

## Semantic Graph Materialization

The semantic graph is materialized from publication embeddings already stored in Qdrant and then served from persisted artifacts.

Current characteristics:
- nodes derive from canonical `publication`
- edges derive from Qdrant nearest neighbors
- graph type is undirected
- weights use the Qdrant similarity score
- self-loops are discarded
- duplicate edges are collapsed into one undirected relation

Artifacts persisted for each build:
- a `graph-tool` binary graph file
- a JSON payload used by retrieval APIs
- a static SVG visualization
- build metadata in `semantic_graph_build`

Default storage path:
- `data/graphs/semantic/`

Build parameters exposed by the API include:
- `top_k`
- `score_threshold`
- `edge_symmetry_policy`
- `mutual_knn`
- `include_isolated_nodes`
- optional `publication_type`
- optional `language_code`
- optional `year_from`
- optional `year_to`

## Embeddings Layer

The embeddings layer uses a provider abstraction so the application orchestration does not depend directly on Gemini or any other vendor.

Initial provider:
- Gemini `gemini-embedding-001`

Configured content fields:
- `EMBEDDINGS_CONTENT_FIELDS`
- default value: `title,authors,abstract`

Current publication text construction:
- `Title: <publication.title>`
- `Authors: <publication authors in canonical order>`
- `Abstract: <publication.abstract>`

Only configured non-empty fields are included, in the configured order, separated by blank lines.

Storage split:
- Qdrant stores the semantic publication payload and vector
- PostgreSQL stores canonical metadata in `publication_embedding`

Tracked metadata includes:
- publication id
- embedding provider
- embedding model
- embedding version
- Qdrant collection
- Qdrant point id
- content hash

The Qdrant payload is intentionally publication-centric. It includes the semantic text used for embedding plus lightweight publication fields such as title, authors and abstract, instead of exposing provider/model/version as the main payload.

`QDRANT_API_KEY` is optional for local Docker development. The client only sends it when configured.

## Current Limitations

- no automatic download of the Beginner's Kit
- no canonical `project` API yet
- no canonical `datasource` entity API for OpenAIRE datasource records yet
- relation-to-affiliation mapping remains intentionally conservative:
  - `publication_organization` is materialized directly from result-organization relations
  - `researcher_affiliation` is derived only for unambiguous solo-author publication cases
- manual provenance for `researcher` and `organization` is stored in `source_record` but those entities do not yet have a direct foreign key to the latest provenance row
- coauthorship graph rebuilds are explicit API operations; there is no automatic rebuild trigger yet
- subgraph filtering currently uses materialized node metadata and edge weights, not dynamic graph recomputation
- embeddings generation currently targets publications only
- the first provider implementation is Gemini-only, even though the orchestration is provider-based
- the current APIs expose generation and metadata retrieval, not semantic search endpoints yet
