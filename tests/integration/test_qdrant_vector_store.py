from tests.fixtures import NO_MATCH_QUERY, ONBOARDING_DOCUMENT, REFUND_DOCUMENT

from tuesday.rag.infrastructure.chunking import CharacterChunker
from tuesday.rag.infrastructure.providers import DeterministicDenseEmbeddingProvider
from tuesday.rag.infrastructure.qdrant_vector_store import QdrantVectorStore
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
    vector_store = QdrantVectorStore(
        location=config.qdrant_location,
        collection_prefix=config.qdrant_collection_prefix,
        dense_vector_size=config.qdrant_dense_vector_size,
    )
    embedding_provider = DeterministicDenseEmbeddingProvider(
        dimension=config.qdrant_dense_vector_size
    )
    ingestion = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(embedding_provider, vector_store),
    )
    retrieval = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
    )
    return ingestion, retrieval


def test_qdrant_vector_store_replace_document_within_index_name() -> None:
    ingestion, retrieval = _build_use_cases()

    first_result = ingestion.execute(REFUND_DOCUMENT)
    second_result = ingestion.execute(
        {
            **REFUND_DOCUMENT,
            "content": (
                "Khach hang co the yeu cau hoan tien trong vong 14 ngay ke tu ngay thanh toan. "
                "Yeu cau hoan tien phai duoc gui qua cong ho tro chinh thuc."
            ),
        }
    )
    result = retrieval.execute(
        {
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        }
    )

    assert first_result.replaced_document is False
    assert second_result.replaced_document is True
    assert result.chunks
    assert any("14 ngay" in chunk.text for chunk in result.chunks)
    assert all("7 ngay" not in chunk.text for chunk in result.chunks)


def test_qdrant_vector_store_supports_tags_contains_any_and_top_k_sorted() -> None:
    ingestion, retrieval = _build_use_cases()
    ingestion.execute(REFUND_DOCUMENT)
    ingestion.execute(ONBOARDING_DOCUMENT)

    result = retrieval.execute(
        {
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "top_k": 1,
            "filters": {"tags": ["refund", "missing-tag"]},
            "index_name": "enterprise-kb",
        }
    )

    assert len(result.chunks) == 1
    assert result.chunks[0].document_id == "doc-refund-001"
    assert result.chunks == sorted(result.chunks, key=lambda chunk: chunk.score, reverse=True)


def test_qdrant_vector_store_returns_empty_list_for_no_match_query() -> None:
    ingestion, retrieval = _build_use_cases()
    ingestion.execute(REFUND_DOCUMENT)

    result = retrieval.execute(
        {
            "query": NO_MATCH_QUERY,
            "index_name": "enterprise-kb",
        }
    )

    assert result.chunks == []
