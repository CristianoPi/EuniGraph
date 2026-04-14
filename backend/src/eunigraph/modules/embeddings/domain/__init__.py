"""Embeddings domain contracts."""

from eunigraph.modules.embeddings.domain.providers import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderInfo,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "EmbeddingProviderInfo",
]
