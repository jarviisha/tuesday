from tuesday.rag.domain.models import IndexedChunk, RetrievedChunk


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._storage: dict[str, dict[str, list[IndexedChunk]]] = {}

    def reset(self) -> None:
        self._storage.clear()

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool:
        by_index = self._storage.setdefault(index_name, {})
        replaced = document_id in by_index
        by_index[document_id] = chunks
        return replaced

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[RetrievedChunk]:
        results: list[RetrievedChunk] = []
        for chunks in self._storage.get(index_name, {}).values():
            for chunk in chunks:
                if not self._matches_filters(chunk.metadata, filters or {}):
                    continue
                score = self._cosine_like(query_embedding, chunk.embedding)
                if score <= 0:
                    continue
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        score=score,
                        metadata=chunk.metadata,
                    )
                )
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]

    @staticmethod
    def _matches_filters(metadata: dict, filters: dict) -> bool:
        for key, expected in filters.items():
            actual = metadata.get(key)
            if key == "tags":
                actual_tags = set(actual or [])
                expected_tags = set(expected or [])
                if not actual_tags.intersection(expected_tags):
                    return False
                continue
            if actual != expected:
                return False
        return True

    @staticmethod
    def _cosine_like(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        left_set = set(left)
        right_set = set(right)
        intersection_size = len(left_set.intersection(right_set))
        if intersection_size == 0:
            return 0.0
        return intersection_size / ((len(left_set) * len(right_set)) ** 0.5)
