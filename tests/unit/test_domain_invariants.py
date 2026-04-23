import pytest

from tuesday.rag.domain.errors import InvalidInputError
from tuesday.rag.domain.models import (
    DocumentIndexResult,
    GeneratedAnswer,
    GenerationRequest,
    IndexedChunk,
    RetrievalRequest,
    RetrievedChunk,
)


def test_indexed_chunk_requires_non_empty_embedding() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        IndexedChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text="text",
            embedding=[],
            metadata={"chunk_id": "chunk-001"},
            index_name="enterprise-kb",
        )

    assert exc_info.value.details == {"field": "embedding"}


def test_retrieval_request_requires_positive_top_k() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        RetrievalRequest(
            query="refund",
            top_k=0,
            filters=None,
            index_name="enterprise-kb",
        )

    assert exc_info.value.details == {"field": "top_k"}


def test_generation_request_requires_context_source() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        GenerationRequest(
            question="refund?",
            retrieval_request=None,
            retrieved_chunks=None,
            max_context_chunks=5,
        )

    assert exc_info.value.details == {"field": "retrieval_request"}


def test_generated_answer_requires_citations_to_be_subset_of_used_chunks() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        GeneratedAnswer(
            answer="According to the current documentation...",
            citations=["chunk-002"],
            grounded=True,
            insufficient_context=False,
            used_chunks=[
                RetrievedChunk(
                    chunk_id="chunk-001",
                    document_id="doc-001",
                    text="text",
                    score=0.9,
                    metadata={"chunk_id": "chunk-001"},
                )
            ],
        )

    assert exc_info.value.details == {"field": "citations"}


def test_generated_answer_rejects_grounded_when_insufficient_context() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        GeneratedAnswer(
            answer="Not enough information.",
            citations=[],
            grounded=True,
            insufficient_context=True,
            used_chunks=[],
        )

    assert exc_info.value.details == {"field": "grounded"}


def test_document_index_result_requires_known_status() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        DocumentIndexResult(
            document_id="doc-001",
            index_name="enterprise-kb",
            chunk_count=1,
            indexed_count=1,
            status="done",
        )

    assert exc_info.value.details == {"field": "status"}
