# Embeddings Layer

## Purpose

This document describes the first semantic enrichment layer for EuniGraph.

The goal is to generate stable text embeddings for canonical publications and persist them across:
- PostgreSQL for canonical metadata
- Qdrant for vector storage

## Provider Abstraction

The embeddings module is intentionally provider-based.

Application orchestration depends on an abstract provider contract that exposes:
- provider name
- model name
- embedding generation for one or more texts
- readable provider-level errors

This keeps the rest of the application independent from a specific vendor SDK or API.

## Initial Provider

The initial concrete provider is:
- Gemini `gemini-embedding-001`

Rationale:
- text-only support is enough for the current MVP
- low friction for prototyping
- easy replacement later because the provider logic is isolated

The current implementation calls the Gemini embeddings REST API and does not leak vendor-specific details outside the provider adapter.

## Configuration

Relevant environment variables:
- `EMBEDDINGS_ENABLED`
- `EMBEDDINGS_PROVIDER`
- `EMBEDDINGS_MODEL`
- `EMBEDDINGS_VERSION`
- `EMBEDDINGS_BATCH_SIZE`
- `EMBEDDINGS_REQUEST_TIMEOUT_SECONDS`
- `EMBEDDINGS_MAX_RETRIES`
- `EMBEDDINGS_CONTENT_FIELDS`
- `GEMINI_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_PUBLICATIONS`

Important note:
- `QDRANT_API_KEY` is optional in the default local Docker setup
- if it is empty, the Qdrant client connects without authentication

## Publication Text Construction

The first version builds the embedding input from configured publication fields.

Supported fields today:
- `title`
- `authors`
- `abstract`

Default configuration:
- `EMBEDDINGS_CONTENT_FIELDS=title,authors,abstract`

Current text template:
- `Title: <value>`
- `Authors: <author 1>, <author 2>, ...`
- `Abstract: <value>`

Rules:
- fields are included in configured order
- empty fields are skipped
- author names are taken from canonical `publication_author` order, preferring `researcher.full_name`
- blocks are separated by a blank line
- the resulting text is hashed and used to avoid unnecessary regeneration

## Persistence Model

### PostgreSQL

Canonical embedding metadata is stored in `publication_embedding`.

Tracked fields include:
- `publication_id`
- `embedding_provider`
- `embedding_model`
- `embedding_version`
- `qdrant_collection`
- `qdrant_point_id`
- `content_hash`

### Qdrant

Vectors are stored in the configured publication collection.

The Qdrant payload is publication-centric and semantic. It includes:
- `publication_id`
- `title`
- `abstract` when available
- ordered `authors`
- `content_text`, which is the exact text used for the embedding
- lightweight publication metadata such as `doi`, `openaire_id`, `publication_year`, `journal_name`, `venue_name`, `publisher` when available

The point id is deterministic for:
- publication id
- provider
- model
- version

This allows safe regeneration without inventing a new identifier every time.

Provider, model, version and `content_hash` remain tracked in PostgreSQL through `publication_embedding`. They are intentionally not the main Qdrant payload for the prototype, because Qdrant should primarily expose the semantic representation of the publication.

## Regeneration Strategy

The current pipeline avoids unnecessary work when all of these match:
- same provider
- same model
- same embedding version
- same configured Qdrant collection
- same content hash

If the relevant content changes, or if the active provider/model/version changes, the embedding is regenerated.

## API Surface

Current endpoints:
- `GET /api/v1/embeddings/provider`
- `GET /api/v1/embeddings/status`
- `POST /api/v1/embeddings/build`
- `POST /api/v1/embeddings/load-all`
- `POST /api/v1/embeddings/reset`
- `POST /api/v1/publications/{id}/embedding`
- `GET /api/v1/publications/{id}/embedding`

Intended usage:
- inspect provider and runtime configuration
- build embeddings for one publication
- build embeddings for batches of publications
- force a full load of all publications into the active collection
- reset the active collection and aligned PostgreSQL metadata
- inspect metadata of the active embedding for a publication
- monitor collection and metadata counts

## Current Limitations

- no semantic search endpoint yet
- no query embeddings endpoint yet
- no local model provider yet
- no multimodal embeddings yet
- no background worker or scheduled regeneration yet
