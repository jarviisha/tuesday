from __future__ import annotations

import hashlib
import uuid

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core.vector_stores.types import (
    FilterCondition,
    FilterOperator,
    VectorStoreQuery,
    VectorStoreQueryMode,
)
from llama_index.vector_stores.qdrant import QdrantVectorStore as LlamaIndexQdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from tuesday.rag.domain.errors import IndexWriteError, RetrievalError
from tuesday.rag.domain.models import IndexedChunk, RetrievedChunk


class LlamaIndexQdrantAdapter:
    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        location: str | None = None,
        collection_prefix: str = "tuesday_v2",
        dense_vector_size: int = 512,
    ) -> None:
        client_kwargs: dict = {}
        if url:
            client_kwargs["url"] = url
        if api_key:
            client_kwargs["api_key"] = api_key
        if location:
            client_kwargs["location"] = location
        self._client = QdrantClient(**client_kwargs)
        self._prefix = collection_prefix
        self._vector_size = dense_vector_size
        self._stores: dict[str, LlamaIndexQdrantVectorStore] = {}

    def _collection_name(self, index_name: str) -> str:
        return f"{self._prefix}__{index_name}"

    def _get_or_create_store(self, index_name: str) -> LlamaIndexQdrantVectorStore:
        if index_name not in self._stores:
            self._stores[index_name] = LlamaIndexQdrantVectorStore(
                client=self._client,
                collection_name=self._collection_name(index_name),
            )
        return self._stores[index_name]

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool:
        try:
            qdrant_store = self._get_or_create_store(index_name)
            collection_name = self._collection_name(index_name)

            replaced = False
            if self._client.collection_exists(collection_name):
                scroll_result, _ = self._client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="document_id", match=MatchValue(value=document_id)
                            )
                        ]
                    ),
                    limit=1,
                    with_payload=False,
                    with_vectors=False,
                )
                replaced = bool(scroll_result)
                if replaced:
                    qdrant_store.delete(document_id)

            nodes = [_chunk_to_node(chunk) for chunk in chunks]
            qdrant_store.add(nodes)
            return replaced
        except Exception as exc:
            raise IndexWriteError(f"Qdrant replace_document failed: {exc}") from exc

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[RetrievedChunk]:
        try:
            if not self._client.collection_exists(self._collection_name(index_name)):
                return []

            qdrant_store = self._get_or_create_store(index_name)
            llama_filters = _build_metadata_filters(filters)

            query_obj = VectorStoreQuery(
                query_embedding=query_embedding,
                similarity_top_k=top_k,
                filters=llama_filters,
                mode=VectorStoreQueryMode.DEFAULT,
            )
            result = qdrant_store.query(query_obj)

            retrieved: list[RetrievedChunk] = []
            nodes = result.nodes or []
            similarities = result.similarities or []
            for i, node in enumerate(nodes):
                score = similarities[i] if i < len(similarities) else 0.0
                if score <= 0:
                    continue
                metadata = dict(node.metadata)
                retrieved.append(
                    RetrievedChunk(
                        chunk_id=str(metadata.get("chunk_id", node.node_id)),
                        document_id=str(metadata.get("document_id", "")),
                        text=node.get_content(),
                        score=score,
                        metadata=metadata,
                    )
                )
            return sorted(retrieved, key=lambda c: c.score, reverse=True)
        except Exception as exc:
            raise RetrievalError(f"Qdrant query failed: {exc}") from exc

    def reset(self) -> None:
        for index_name in list(self._stores.keys()):
            collection_name = self._collection_name(index_name)
            try:
                if self._client.collection_exists(collection_name):
                    self._client.delete_collection(collection_name)
            except Exception:
                pass
        self._stores.clear()


def _chunk_id_to_qdrant_uuid(chunk_id: str) -> str:
    """Convert a chunk_id string to a deterministic UUID for Qdrant point IDs."""
    return str(uuid.UUID(bytes=hashlib.md5(chunk_id.encode()).digest()))


def _chunk_to_node(chunk: IndexedChunk) -> TextNode:
    node = TextNode(
        id_=_chunk_id_to_qdrant_uuid(chunk.chunk_id),
        text=chunk.text,
        embedding=chunk.embedding,
        metadata={**chunk.metadata, "document_id": chunk.document_id, "chunk_id": chunk.chunk_id},
    )
    node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=chunk.document_id)
    return node


def _build_metadata_filters(filters: dict | None) -> MetadataFilters | None:
    if not filters:
        return None

    leaf_filters: list[MetadataFilter] = []
    has_tags = "tags" in filters

    for key, value in filters.items():
        if key == "tags" and isinstance(value, list):
            for tag in value:
                leaf_filters.append(
                    MetadataFilter(key="tags", value=tag, operator=FilterOperator.EQ)
                )
        elif isinstance(value, (str, int, float, bool)):
            leaf_filters.append(
                MetadataFilter(key=key, value=value, operator=FilterOperator.EQ)
            )

    if not leaf_filters:
        return None

    # For a tags-only filter, use OR (contains-any, DL-003).
    # For any other combination, use AND.
    condition = FilterCondition.OR if has_tags and len(filters) == 1 else FilterCondition.AND
    return MetadataFilters(filters=leaf_filters, condition=condition)
