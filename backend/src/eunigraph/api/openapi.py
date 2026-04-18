from __future__ import annotations

from eunigraph.api.schemas.common import ApiErrorResponse, ValidationErrorResponse

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Lightweight runtime checks for the backend service.",
    },
    {
        "name": "publications",
        "description": "Canonical publication entities and publication-linked relations.",
    },
    {
        "name": "researchers",
        "description": "Canonical researcher entities and affiliation management.",
    },
    {
        "name": "organizations",
        "description": "Canonical organizations, including universities and departments.",
    },
    {
        "name": "source-records",
        "description": "Raw provenance records and source payload inspection endpoints.",
    },
    {
        "name": "embeddings",
        "description": (
            "Publication embedding generation, collection management "
            "and metadata retrieval."
        ),
    },
    {
        "name": "coauthorship",
        "description": "Materialized coauthorship graph build, retrieval and analytics.",
    },
    {
        "name": "semantic-graph",
        "description": "Materialized semantic similarity graph build, retrieval and analytics.",
    },
    {
        "name": "normalization",
        "description": "Normalization runs and deduplication findings.",
    },
    {
        "name": "admin",
        "description": "Administrative development endpoints for seed and internal workflows.",
    },
]

COMMON_ERROR_RESPONSES = {
    400: {
        "model": ApiErrorResponse,
        "description": "The request is syntactically valid but violates application rules.",
    },
    409: {
        "model": ApiErrorResponse,
        "description": "The request conflicts with the current application or persistence state.",
    },
    404: {
        "model": ApiErrorResponse,
        "description": "The requested resource or materialized artifact was not found.",
    },
    422: {
        "model": ValidationErrorResponse,
        "description": "The request payload or query parameters failed validation.",
    },
    503: {
        "model": ApiErrorResponse,
        "description": (
            "The feature is temporarily unavailable in the current "
            "runtime configuration."
        ),
    },
}


def build_openapi_description() -> str:
    return (
        "EuniGraph exposes canonical research entities, provenance data, graph pipelines, "
        "and semantic enrichment workflows through a modular FastAPI backend.\n\n"
        "Documentation entry points:\n"
        "- Swagger UI: `/docs`\n"
        "- ReDoc: `/redoc`\n"
        "- OpenAPI JSON: `/openapi.json`\n\n"
        "Key API families:\n"
        "- canonical entities: publications, researchers, organizations\n"
        "- provenance and ingestion support: source-records, seed admin endpoints\n"
        "- data quality workflows: normalization\n"
        "- graph pipelines: coauthorship and semantic similarity\n"
        "- vector workflows: embeddings and Qdrant integration"
    )
