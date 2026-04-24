from tests.fixtures import ONBOARDING_DOCUMENT, REFUND_DOCUMENT

from tuesday.rag.domain.models import RetrievedChunk
from tuesday.rag.infrastructure.chunking import LlamaIndexNodeParser
from tuesday.rag.infrastructure.providers import DeterministicDenseEmbeddingProvider
from tuesday.rag.infrastructure.qdrant_vector_store import LlamaIndexQdrantAdapter
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.rag.retrieval.use_case import RetrievalUseCase
from tuesday.runtime.config import RuntimeConfig


def _build_use_cases() -> tuple[IngestionUseCase, RetrievalUseCase]:
    config = RuntimeConfig(
        vector_store_backend="qdrant",
        qdrant_location=":memory:",
        qdrant_collection_prefix="test",
        qdrant_dense_vector_size=512,
    )
    vector_store = LlamaIndexQdrantAdapter(
        location=config.qdrant_location,
        collection_prefix=config.qdrant_collection_prefix_v2,
        dense_vector_size=config.qdrant_dense_vector_size,
    )
    embedding_provider = DeterministicDenseEmbeddingProvider(
        dimension=config.qdrant_dense_vector_size
    )
    ingestion = IngestionUseCase(
        config=config,
        chunker=LlamaIndexNodeParser(
            chunk_size=config.ingestion_chunk_size_tokens_default,
            chunk_overlap=config.ingestion_chunk_overlap_tokens_default,
        ),
        indexer=IndexerService(embedding_provider, vector_store),
    )
    retrieval = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
    )
    return ingestion, retrieval


def test_retrieval_pipeline_respects_top_k() -> None:
    ingestion, retrieval = _build_use_cases()
    ingestion.execute(REFUND_DOCUMENT)
    ingestion.execute(ONBOARDING_DOCUMENT)

    result = retrieval.execute(
        {
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "top_k": 3,
            "index_name": "enterprise-kb",
        }
    )

    assert len(result.chunks) <= 3
    assert all(isinstance(chunk, RetrievedChunk) for chunk in result.chunks)
    assert result.chunks == sorted(result.chunks, key=lambda c: c.score, reverse=True)


def test_retrieval_pipeline_result_matches_retrieved_chunk_schema() -> None:
    ingestion, retrieval = _build_use_cases()
    ingestion.execute(REFUND_DOCUMENT)

    result = retrieval.execute(
        {
            "query": "hoan tien",
            "index_name": "enterprise-kb",
        }
    )

    assert result.chunks
    for chunk in result.chunks:
        assert chunk.chunk_id
        assert chunk.document_id
        assert chunk.text
        assert chunk.score > 0
        assert isinstance(chunk.metadata, dict)


def test_retrieval_pipeline_tags_filter_returns_only_matching_documents() -> None:
    ingestion, retrieval = _build_use_cases()
    ingestion.execute(REFUND_DOCUMENT)
    ingestion.execute(ONBOARDING_DOCUMENT)

    result = retrieval.execute(
        {
            "query": "chinh sach noi bo",
            "filters": {"tags": ["refund"]},
            "index_name": "enterprise-kb",
        }
    )

    assert result.chunks
    assert all(
        "refund" in chunk.metadata.get("tags", []) for chunk in result.chunks
    )
    assert all(chunk.document_id == "doc-refund-001" for chunk in result.chunks)


def test_retrieval_pipeline_tags_filter_contains_any_semantics() -> None:
    ingestion, retrieval = _build_use_cases()
    ingestion.execute(REFUND_DOCUMENT)
    ingestion.execute(ONBOARDING_DOCUMENT)

    result = retrieval.execute(
        {
            "query": "chinh sach noi bo nhan su",
            "filters": {"tags": ["refund", "hr"]},
            "index_name": "enterprise-kb",
        }
    )

    assert result.chunks
    document_ids = {chunk.document_id for chunk in result.chunks}
    assert "doc-refund-001" in document_ids or "doc-onboarding-001" in document_ids
