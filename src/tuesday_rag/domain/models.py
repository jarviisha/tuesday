from dataclasses import dataclass, field
from typing import Any

from tuesday_rag.domain.errors import InvalidInputError

Metadata = dict[str, Any]


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    title: str | None
    content: str
    source_type: str
    source_uri: str | None
    language: str | None
    metadata: Metadata
    checksum: str | None = None


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    sequence_no: int
    token_count: int | None
    char_start: int | None
    char_end: int | None
    metadata: Metadata


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: str
    document_id: str
    text: str
    embedding: list[float]
    metadata: Metadata
    index_name: str

    def __post_init__(self) -> None:
        if not self.embedding:
            raise InvalidInputError("embedding không được rỗng", details={"field": "embedding"})


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: Metadata


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    top_k: int
    filters: Metadata | None
    index_name: str
    request_id: str | None = None

    def __post_init__(self) -> None:
        if self.top_k <= 0:
            raise InvalidInputError("top_k không hợp lệ", details={"field": "top_k"})


@dataclass(frozen=True)
class RetrievalResponse:
    query: str
    top_k: int
    chunks: list[RetrievedChunk]
    applied_filters: Metadata
    index_name: str


@dataclass(frozen=True)
class GenerationRequest:
    question: str
    retrieval_request: RetrievalRequest | None
    retrieved_chunks: list[RetrievedChunk] | None
    max_context_chunks: int | None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if self.retrieval_request is None and self.retrieved_chunks is None:
            raise InvalidInputError(
                "Phải có retrieval_request hoặc retrieved_chunks",
                details={"field": "retrieval_request"},
            )


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    citations: list[str]
    grounded: bool
    insufficient_context: bool
    used_chunks: list[RetrievedChunk]

    def __post_init__(self) -> None:
        valid_chunk_ids = {chunk.chunk_id for chunk in self.used_chunks}
        if any(citation not in valid_chunk_ids for citation in self.citations):
            raise InvalidInputError("citation không hợp lệ", details={"field": "citations"})
        if self.insufficient_context and self.grounded:
            raise InvalidInputError(
                "insufficient_context không được đi cùng grounded=true",
                details={"field": "grounded"},
            )
        if not self.used_chunks and self.citations:
            raise InvalidInputError(
                "citations phải rỗng khi used_chunks rỗng",
                details={"field": "citations"},
            )


@dataclass(frozen=True)
class LLMGenerationResult:
    answer: str
    citations: list[str]


@dataclass(frozen=True)
class DocumentIndexResult:
    document_id: str
    index_name: str
    chunk_count: int
    indexed_count: int
    status: str
    errors: list[str] = field(default_factory=list)
    replaced_document: bool = False

    def __post_init__(self) -> None:
        if self.status not in {"indexed", "partial", "failed"}:
            raise InvalidInputError("status không hợp lệ", details={"field": "status"})
