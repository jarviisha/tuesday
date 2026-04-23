from __future__ import annotations

import math
import uuid
from hashlib import sha256
from typing import Any, cast

from qdrant_client import QdrantClient, models

from tuesday.rag.domain.models import IndexedChunk, RetrievedChunk


class QdrantVectorStore:
    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        location: str | None = None,
        collection_prefix: str = "tuesday",
        dense_vector_size: int = 128,
    ) -> None:
        client_kwargs: dict[str, Any] = {}
        if url:
            client_kwargs["url"] = url
        if api_key:
            client_kwargs["api_key"] = api_key
        if location:
            client_kwargs["location"] = location
        self._client = QdrantClient(**client_kwargs)
        self._collection_prefix = collection_prefix
        self._dense_vector_size = dense_vector_size

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool:
        collection_name = self._collection_name(index_name)
        vector_size = self._resolve_vector_size(collection_name, chunks)
        self._ensure_collection(collection_name, vector_size)

        document_filter = self._document_filter(document_id)
        replaced = self._client.count(
            collection_name=collection_name,
            count_filter=document_filter,
            exact=True,
        ).count > 0
        if replaced:
            self._client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=document_filter),
                wait=True,
            )

        points = [
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                vector=self._to_dense_vector(chunk.embedding, vector_size),
                payload={
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "source_type": chunk.metadata.get("source_type"),
                    "language": chunk.metadata.get("language"),
                    "tags": chunk.metadata.get("tags"),
                },
            )
            for chunk in chunks
        ]
        self._client.upsert(
            collection_name=collection_name,
            wait=True,
            points=points,
        )
        return replaced

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[RetrievedChunk]:
        collection_name = self._collection_name(index_name)
        if not self._client.collection_exists(collection_name):
            return []

        vector_size = self._collection_vector_size(collection_name)
        response = self._client.query_points(
            collection_name=collection_name,
            query=self._to_dense_vector(query_embedding, vector_size),
            query_filter=self._to_qdrant_filter(filters or {}),
            limit=top_k,
            with_payload=True,
        )
        points = self._query_result_points(response)
        results: list[RetrievedChunk] = []
        for point in points:
            score = float(point.score)
            if score <= 0:
                continue
            payload = point.payload or {}
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            results.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id", point.id)),
                    document_id=str(payload.get("document_id", metadata.get("document_id", ""))),
                    text=str(payload.get("text", "")),
                    score=score,
                    metadata=metadata,
                )
            )
        return sorted(results, key=lambda chunk: chunk.score, reverse=True)

    def reset(self) -> None:
        for collection in self._client.get_collections().collections:
            name = collection.name
            if name.startswith(f"{self._collection_prefix}__"):
                self._client.delete_collection(name)

    def _resolve_vector_size(
        self,
        collection_name: str,
        chunks: list[IndexedChunk],
    ) -> int:
        if self._client.collection_exists(collection_name):
            return self._collection_vector_size(collection_name)
        embedding_lengths = {len(chunk.embedding) for chunk in chunks}
        if len(embedding_lengths) == 1 and all(
            self._is_dense_embedding(chunk.embedding) for chunk in chunks
        ):
            return embedding_lengths.pop()
        return self._dense_vector_size

    def _ensure_collection(self, collection_name: str, vector_size: int) -> None:
        if self._client.collection_exists(collection_name):
            return
        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def _collection_vector_size(self, collection_name: str) -> int:
        info = self._client.get_collection(collection_name)
        vectors = info.config.params.vectors
        if vectors is None:
            raise RuntimeError("Qdrant collection is missing vector configuration")
        if isinstance(vectors, dict):
            return self._named_vectors_size(vectors)
        return self._vector_params_size(vectors)

    def _collection_name(self, index_name: str) -> str:
        return f"{self._collection_prefix}__{index_name}"

    @staticmethod
    def _document_filter(document_id: str) -> models.Filter:
        return QdrantVectorStore._build_filter(
            [QdrantVectorStore._match_value_condition(key="document_id", value=document_id)]
        )

    @staticmethod
    def _to_qdrant_filter(filters: dict[str, Any]) -> models.Filter | None:
        if not filters:
            return None

        conditions: list[models.Condition] = []
        for key, value in filters.items():
            if key == "tags":
                if not value:
                    continue
                conditions.append(
                    QdrantVectorStore._match_any_condition(key="tags", values=list(value))
                )
                continue
            conditions.append(QdrantVectorStore._match_value_condition(key=key, value=value))
        if not conditions:
            return None
        return QdrantVectorStore._build_filter(conditions)

    @staticmethod
    def _build_filter(conditions: list[models.Condition]) -> models.Filter:
        return models.Filter(must=conditions)

    @staticmethod
    def _query_result_points(response: Any) -> list[models.ScoredPoint]:
        if hasattr(response, "points"):
            return cast(list[models.ScoredPoint], response.points)
        return cast(list[models.ScoredPoint], response)

    @staticmethod
    def _vector_params_size(vectors: models.VectorParams) -> int:
        return int(vectors.size)

    @staticmethod
    def _named_vectors_size(vectors: dict[str, models.VectorParams]) -> int:
        first_vector = next(iter(vectors.values()))
        return int(first_vector.size)

    @staticmethod
    def _match_value_condition(*, key: str, value: Any) -> models.Condition:
        return models.FieldCondition(
            key=key,
            match=models.MatchValue(value=value),
        )

    @staticmethod
    def _match_any_condition(*, key: str, values: list[str]) -> models.Condition:
        return models.FieldCondition(
            key=key,
            match=models.MatchAny(any=values),
        )

    @staticmethod
    def _to_dense_vector(embedding: list[float], vector_size: int) -> list[float]:
        if len(embedding) == vector_size and QdrantVectorStore._is_dense_embedding(embedding):
            return embedding

        vector = [0.0] * vector_size
        for index, value in enumerate(embedding):
            digest = sha256(f"{index}:{value!r}".encode()).digest()
            bucket = int.from_bytes(digest[:4], byteorder="big") % vector_size
            vector[bucket] += 1.0

        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0:
            return vector
        return [component / norm for component in vector]

    @staticmethod
    def _is_dense_embedding(embedding: list[float]) -> bool:
        if not embedding:
            return False
        return all(math.isfinite(value) for value in embedding) and max(
            abs(value) for value in embedding
        ) <= 1.0
