from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class EmbeddingProviderError(RuntimeError):
    """Raised when an embedding provider request fails."""


@dataclass(slots=True, frozen=True)
class EmbeddingProviderInfo:
    provider_name: str
    model_name: str


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
