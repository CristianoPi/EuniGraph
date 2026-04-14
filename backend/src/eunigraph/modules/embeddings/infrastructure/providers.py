from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from eunigraph.modules.embeddings.domain import (
    EmbeddingProvider,
    EmbeddingProviderError,
)

GEMINI_EMBEDDINGS_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
)


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
        max_retries: int,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._embed_single_text(text) for text in texts]

    def _embed_single_text(self, text: str) -> list[float]:
        endpoint = GEMINI_EMBEDDINGS_ENDPOINT_TEMPLATE.format(model=self._model_name)
        payload = json.dumps(
            {
                "model": f"models/{self._model_name}",
                "content": {
                    "parts": [
                        {
                            "text": text,
                        },
                    ],
                },
                "taskType": "RETRIEVAL_DOCUMENT",
            },
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            http_request = request.Request(
                endpoint,
                data=payload,
                headers=headers,
                method="POST",
            )
            try:
                with request.urlopen(
                    http_request,
                    timeout=self._timeout_seconds,
                ) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                values = self._extract_embedding_values(response_payload)
                if not values:
                    raise EmbeddingProviderError("Gemini returned an empty embedding vector")
                return values
            except (
                error.HTTPError,
                error.URLError,
                TimeoutError,
                ValueError,
                EmbeddingProviderError,
            ) as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
        raise EmbeddingProviderError(
            f"Gemini embedding request failed for model `{self._model_name}`: {last_error}",
        )

    def _extract_embedding_values(self, response_payload: dict[str, Any]) -> list[float]:
        if "embedding" in response_payload:
            values = response_payload["embedding"].get("values", [])
            return [float(value) for value in values]
        embeddings = response_payload.get("embeddings", [])
        if embeddings:
            values = embeddings[0].get("values", [])
            return [float(value) for value in values]
        raise EmbeddingProviderError(
            "Gemini embedding response did not contain `embedding` or `embeddings` values",
        )
