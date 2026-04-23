import json
import os
from dataclasses import asdict
from tempfile import NamedTemporaryFile

from tuesday.rag.domain.models import IndexedChunk, RetrievedChunk


class FileBackedVectorStore:
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._storage: dict[str, dict[str, list[IndexedChunk]]] = {}
        self._load()

    def reset(self) -> None:
        self._storage.clear()
        self._persist()

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
        self._persist()
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

    def _load(self) -> None:
        if not os.path.exists(self._file_path):
            return
        with open(self._file_path, encoding="utf-8") as file:
            raw_storage = json.load(file)
        self._storage = {
            index_name: {
                document_id: [IndexedChunk(**chunk) for chunk in chunks]
                for document_id, chunks in by_document.items()
            }
            for index_name, by_document in raw_storage.items()
        }

    def _persist(self) -> None:
        directory = os.path.dirname(self._file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        payload = {
            index_name: {
                document_id: [asdict(chunk) for chunk in chunks]
                for document_id, chunks in by_document.items()
            }
            for index_name, by_document in self._storage.items()
        }
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory or ".",
            delete=False,
        ) as tmp_file:
            json.dump(payload, tmp_file, ensure_ascii=True)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_name = tmp_file.name
        os.replace(tmp_name, self._file_path)

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
