# Data and API Usage

This document describes how EuniGraph uses external data sources, APIs, secrets,
and personal-data-like research metadata.

## Data Sources

EuniGraph is designed to work with research metadata from public or authorized
sources. The main supported source is the OpenAIRE Graph API, specifically the
EUNICE community slice used by the prototype ingestion workflow.

The repository contains source code and documentation. It is not intended to
store private datasets, API secrets, or production database dumps.

## OpenAIRE Metadata

The OpenAIRE ingestion workflow imports research metadata such as:

- publication titles, abstracts, years, DOIs, and source identifiers
- author and researcher names
- organization names and affiliations when available
- provenance metadata needed to trace imported records back to their source

OpenAIRE metadata must be used in accordance with OpenAIRE's applicable terms,
documentation, attribution guidance, and API usage limits. EuniGraph preserves
source identifiers and provenance fields so that downstream users can inspect
where imported records came from.

## Gemini API and Embeddings

EuniGraph can optionally use Google Gemini to generate publication embeddings.
Embeddings are vector representations derived from publication content such as
title, authors, and abstract. They are used for semantic workflows, including
similarity graph generation and vector retrieval through Qdrant.

Gemini usage requires a deployment-specific API key:

```env
GEMINI_API_KEY=...
```

If `GEMINI_API_KEY` is not configured, EuniGraph keeps the backend available and
disables embedding-generation functionality. Core catalog, ingestion, manual
data management, and coauthorship workflows can still run without Gemini.

Users enabling Gemini are responsible for ensuring that submitted text and API
usage comply with Google API terms and any applicable institutional policies.

## Qdrant Vector Storage

Qdrant stores generated vectors and lightweight publication payloads used for
semantic retrieval. Qdrant may run locally through Docker Compose or through a
managed service.

If a managed Qdrant instance is used, credentials must be configured outside the
repository, for example through:

```env
QDRANT_URL=...
QDRANT_API_KEY=...
```

## Personal Data and Research Metadata

EuniGraph may process names of researchers, publication authors, and affiliation
metadata. This information is usually derived from public research metadata
sources, but deployments should still treat it as personal-data-like information
when required by local policy or law.

Recommended operational practices:

- ingest only data that the deployment is allowed to process
- keep source provenance for imported records
- avoid committing production exports, database dumps, API keys, or raw private
  datasets to the repository
- use the admin/manual APIs for controlled corrections and enrichment
- review applicable GDPR or institutional obligations before publishing a
  production dataset

## Generated Graph Artifacts

Coauthorship and semantic graph builds generate artifacts under configured data
paths, such as:

```env
EUNIGRAPH_COAUTHORSHIP_GRAPH_STORAGE_PATH=...
EUNIGRAPH_SEMANTIC_GRAPH_STORAGE_PATH=...
```

These files are generated deployment artifacts. Their reuse depends on the
license and terms of the data from which they were created.

## Secrets

The repository must not contain real secrets. Use `.env` files or deployment
secret managers for values such as:

- `GEMINI_API_KEY`
- `QDRANT_API_KEY`
- database passwords used outside local development

The committed `.env.example` is a template and intentionally does not include
real credentials.

