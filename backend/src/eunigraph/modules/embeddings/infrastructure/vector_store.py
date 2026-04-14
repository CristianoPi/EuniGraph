from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient, models


class QdrantPublicationEmbeddingStore:
    def __init__(self, client: QdrantClient) -> None:
        self.client = client

    def ensure_collection(self, *, collection_name: str, vector_size: int) -> None:
        if self.client.collection_exists(collection_name):
            return
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_publication_embedding(
        self,
        *,
        collection_name: str,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        self.ensure_collection(
            collection_name=collection_name,
            vector_size=len(vector),
        )
        self.client.upsert(
            collection_name=collection_name,
            wait=True,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                ),
            ],
        )

    def get_collection_status(self, collection_name: str) -> dict[str, Any]:
        if not self.client.collection_exists(collection_name):
            return {
                "exists": False,
                "points_count": 0,
                "status": None,
            }
        collection_info = self.client.get_collection(collection_name)
        return {
            "exists": True,
            "points_count": int(getattr(collection_info, "points_count", 0) or 0),
            "status": getattr(collection_info, "status", None),
        }

    def delete_collection(self, collection_name: str) -> bool:
        if not self.client.collection_exists(collection_name):
            return False
        self.client.delete_collection(collection_name=collection_name)
        return True
