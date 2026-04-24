from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any, cast

from qdrant_client import QdrantClient, models

from tuesday.rag.domain.models import IndexedChunk

try:
    from llama_index.core.schema import TextNode
    from llama_index.core.vector_stores.types import (
        FilterCondition,
        FilterOperator,
        MetadataFilter,
        MetadataFilters,
        VectorStoreQuery,
        VectorStoreQueryResult,
    )
except Exception:
    class FilterCondition(str, Enum):
        AND = "and"
        OR = "or"
        NOT = "not"

    class FilterOperator(str, Enum):
        EQ = "=="
        ANY = "any"

    @dataclass(frozen=True)
    class MetadataFilter:
        key: str
        value: int | float | str | list[str] | list[float] | list[int] | None
        operator: FilterOperator = FilterOperator.EQ

    @dataclass(frozen=True)
    class MetadataFilters:
        filters: list[MetadataFilter | "MetadataFilters"]
        condition: FilterCondition | None = FilterCondition.AND

    @dataclass(frozen=True)
    class VectorStoreQuery:
        query_embedding: list[float] | None = None
        similarity_top_k: int = 1
        filters: MetadataFilters | None = None

    @dataclass(frozen=True)
    class VectorStoreQueryResult:
        nodes: list["TextNode"] | None = None
        similarities: list[float] | None = None
        ids: list[str] | None = None

    @dataclass
    class TextNode:
        id_: str
        text: str = ""
        metadata: dict[str, Any] = field(default_factory=dict)
        embedding: list[float] | None = None

        @property
        def node_id(self) -> str:
            return self.id_


class LlamaIndexQdrantBridge:
    def __init__(
        self,
        *,
        client: QdrantClient,
        collection_prefix: str,
        dense_vector_size: int,
    ) -> None:
        self._client = client
        self._collection_prefix = collection_prefix
        self._dense_vector_size = dense_vector_size

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool:
        collection_name = self.collection_name(index_name)
        nodes = [self._to_text_node(chunk) for chunk in chunks]
        vector_size = self._resolve_vector_size(collection_name, nodes)
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

        points = [self._to_point(node=node, vector_size=vector_size) for node in nodes]
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
        filters: dict[str, Any] | None,
    ) -> VectorStoreQueryResult:
        collection_name = self.collection_name(index_name)
        if not self._client.collection_exists(collection_name):
            return VectorStoreQueryResult(nodes=[], similarities=[], ids=[])

        vector_size = self._collection_vector_size(collection_name)
        query = VectorStoreQuery(
            query_embedding=self.to_dense_vector(query_embedding, vector_size),
            similarity_top_k=top_k,
            filters=self._to_metadata_filters(filters or {}),
        )
        response = self._client.query_points(
            collection_name=collection_name,
            query=query.query_embedding,
            query_filter=self._to_qdrant_filter(query.filters),
            limit=query.similarity_top_k,
            with_payload=True,
        )
        return self._to_query_result(response)

    def collection_name(self, index_name: str) -> str:
        return f"{self._collection_prefix}__{index_name}"

    def collection_exists(self, index_name: str) -> bool:
        return self._client.collection_exists(self.collection_name(index_name))

    def reset(self) -> None:
        for collection in self._client.get_collections().collections:
            name = collection.name
            if name.startswith(f"{self._collection_prefix}__"):
                self._client.delete_collection(name)

    def _resolve_vector_size(
        self,
        collection_name: str,
        nodes: list[TextNode],
    ) -> int:
        if self._client.collection_exists(collection_name):
            return self._collection_vector_size(collection_name)
        embedding_lengths = {len(node.embedding or []) for node in nodes}
        if len(embedding_lengths) == 1 and all(
            self._is_dense_embedding(node.embedding or []) for node in nodes
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

    def _to_point(self, *, node: TextNode, vector_size: int) -> models.PointStruct:
        metadata = dict(node.metadata)
        return models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, node.node_id)),
            vector=self.to_dense_vector(node.embedding or [], vector_size),
            payload={
                "document_id": str(metadata.get("document_id", "")),
                "chunk_id": metadata.get("chunk_id", node.node_id),
                "text": node.text,
                "metadata": metadata,
                "source_type": metadata.get("source_type"),
                "language": metadata.get("language"),
                "tags": metadata.get("tags"),
            },
        )

    @staticmethod
    def _to_text_node(chunk: IndexedChunk) -> TextNode:
        metadata = dict(chunk.metadata)
        metadata.setdefault("document_id", chunk.document_id)
        metadata.setdefault("chunk_id", chunk.chunk_id)
        return TextNode(
            id_=chunk.chunk_id,
            text=chunk.text,
            metadata=metadata,
            embedding=chunk.embedding,
        )

    @staticmethod
    def _to_metadata_filters(filters: dict[str, Any]) -> MetadataFilters | None:
        if not filters:
            return None

        resolved_filters: list[MetadataFilter] = []
        for key, value in filters.items():
            if key == "tags":
                if not value:
                    continue
                resolved_filters.append(
                    MetadataFilter(key="tags", value=list(value), operator=FilterOperator.ANY)
                )
                continue
            resolved_filters.append(MetadataFilter(key=key, value=value, operator=FilterOperator.EQ))
        if not resolved_filters:
            return None
        return MetadataFilters(filters=resolved_filters, condition=FilterCondition.AND)

    @staticmethod
    def _to_qdrant_filter(filters: MetadataFilters | None) -> models.Filter | None:
        if filters is None:
            return None

        conditions: list[models.Condition] = []
        for metadata_filter in filters.filters:
            if isinstance(metadata_filter, MetadataFilters):
                nested = LlamaIndexQdrantBridge._to_qdrant_filter(metadata_filter)
                if nested is not None:
                    conditions.append(nested)
                continue
            conditions.append(LlamaIndexQdrantBridge._to_qdrant_condition(metadata_filter))
        if not conditions:
            return None

        if filters.condition == FilterCondition.OR:
            return models.Filter(should=conditions)
        if filters.condition == FilterCondition.NOT:
            return models.Filter(must_not=conditions)
        return models.Filter(must=conditions)

    @staticmethod
    def _to_qdrant_condition(metadata_filter: MetadataFilter) -> models.Condition:
        if metadata_filter.operator == FilterOperator.ANY:
            values = metadata_filter.value
            if not isinstance(values, list):
                values = [cast(str, metadata_filter.value)]
            return models.FieldCondition(
                key=metadata_filter.key,
                match=models.MatchAny(any=list(values)),
            )
        return models.FieldCondition(
            key=metadata_filter.key,
            match=models.MatchValue(value=metadata_filter.value),
        )

    @staticmethod
    def _to_query_result(response: Any) -> VectorStoreQueryResult:
        points = LlamaIndexQdrantBridge._query_result_points(response)
        nodes: list[TextNode] = []
        similarities: list[float] = []
        ids: list[str] = []
        for point in points:
            score = float(point.score)
            if score <= 0:
                continue
            payload = point.payload or {}
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            metadata = dict(metadata)
            metadata.setdefault("document_id", payload.get("document_id", ""))
            metadata.setdefault("chunk_id", payload.get("chunk_id", point.id))
            if "source_type" in payload:
                metadata.setdefault("source_type", payload.get("source_type"))
            if "language" in payload:
                metadata.setdefault("language", payload.get("language"))
            if "tags" in payload:
                metadata.setdefault("tags", payload.get("tags"))
            chunk_id = str(payload.get("chunk_id", point.id))
            nodes.append(
                TextNode(
                    id_=chunk_id,
                    text=str(payload.get("text", "")),
                    metadata=metadata,
                )
            )
            similarities.append(score)
            ids.append(chunk_id)
        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

    @staticmethod
    def _document_filter(document_id: str) -> models.Filter:
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                )
            ]
        )

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
    def to_dense_vector(embedding: list[float], vector_size: int) -> list[float]:
        if len(embedding) == vector_size and LlamaIndexQdrantBridge._is_dense_embedding(embedding):
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
