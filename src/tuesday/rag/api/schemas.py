from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentIndexRequest(BaseModel):
    document_id: str
    title: str | None = None
    content: str
    source_type: str
    source_uri: str | None = None
    metadata: dict[str, Any] | None = None
    index_name: str


class DocumentIndexResponse(BaseModel):
    document_id: str
    index_name: str
    chunk_count: int
    indexed_count: int
    status: str
    errors: list[str]
    replaced_document: bool


class RetrievedChunkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class RetrievalRequestSchema(BaseModel):
    query: str
    top_k: int = 5
    filters: dict[str, Any] | None = None
    index_name: str


class RetrievalResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str
    top_k: int
    index_name: str
    applied_filters: dict[str, Any]
    chunks: list[RetrievedChunkSchema]


class GenerateRetrievalRequestSchema(BaseModel):
    query: str | None = None
    top_k: int = 5
    filters: dict[str, Any] | None = None
    index_name: str | None = None


class GenerationRequestSchema(BaseModel):
    question: str
    index_name: str | None = None
    retrieval_request: GenerateRetrievalRequestSchema | None = None
    retrieved_chunks: list[RetrievedChunkSchema] | None = None
    max_context_chunks: int = 5


class GenerationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    citations: list[str]
    grounded: bool
    insufficient_context: bool
    used_chunks: list[RetrievedChunkSchema]


class ErrorResponseSchema(BaseModel):
    error_code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
