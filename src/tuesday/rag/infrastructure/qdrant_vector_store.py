from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient

from tuesday.rag.domain.models import IndexedChunk, RetrievedChunk
from tuesday.rag.infrastructure.llamaindex_qdrant_bridge import LlamaIndexQdrantBridge


class QdrantVectorStore:
    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        location: str | None = None,
        collection_prefix: str = "tuesday",
        dense_vector_size: int = 512,
    ) -> None:
        client_kwargs: dict[str, Any] = {}
        if url:
            client_kwargs["url"] = url
        if api_key:
            client_kwargs["api_key"] = api_key
        if location:
            client_kwargs["location"] = location
        self._client = QdrantClient(**client_kwargs)
        self._bridge = LlamaIndexQdrantBridge(
            client=self._client,
            collection_prefix=collection_prefix,
            dense_vector_size=dense_vector_size,
        )

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool:
        return self._bridge.replace_document(
            index_name=index_name,
            document_id=document_id,
            chunks=chunks,
        )

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[RetrievedChunk]:
        result = self._bridge.query(
            index_name=index_name,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters or {},
        )
        results: list[RetrievedChunk] = []
        nodes = result.nodes or []
        similarities = result.similarities or []
        ids = result.ids or []
        for index, node in enumerate(nodes):
            score = similarities[index] if index < len(similarities) else 0.0
            if score <= 0:
                continue
            metadata = dict(node.metadata)
            chunk_id = ids[index] if index < len(ids) else node.node_id
            results.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    document_id=str(metadata.get("document_id", "")),
                    text=node.text,
                    score=score,
                    metadata=metadata,
                )
            )
        return sorted(results, key=lambda chunk: chunk.score, reverse=True)

    def reset(self) -> None:
        self._bridge.reset()
