from typing import Protocol

from tuesday_rag.domain.models import (
    Chunk,
    IndexedChunk,
    LLMGenerationResult,
    RetrievedChunk,
    SourceDocument,
)


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class LLMProvider(Protocol):
    def generate_text(self, prompt: str) -> LLMGenerationResult: ...


class VectorStore(Protocol):
    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool: ...

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[RetrievedChunk]: ...


class DocumentParser(Protocol):
    def parse(self, raw_input: dict) -> SourceDocument: ...


class Chunker(Protocol):
    def chunk(self, document: SourceDocument) -> list[Chunk]: ...
