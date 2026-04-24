import pytest
from tests.fixtures import NO_MATCH_QUERY, REFUND_DOCUMENT

from tuesday.rag.domain.errors import InvalidInputError, UnsupportedFilterError
from tuesday.rag.infrastructure.chunking import LlamaIndexNodeParser
from tuesday.rag.infrastructure.providers import HashEmbeddingProvider
from tuesday.rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.rag.retrieval.use_case import RetrievalUseCase
from tuesday.runtime.config import RuntimeConfig


def test_retrieval_tags_filter_uses_contains_any() -> None:
    config = RuntimeConfig()
    vector_store = InMemoryVectorStore()
    embedding_provider = HashEmbeddingProvider()
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

    ingestion.execute(
        {
            "document_id": "doc-001",
            "content": "Noi dung hoan tien " * 80,
            "source_type": "text",
            "metadata": {"language": "vi", "tags": ["policy", "refund"]},
            "index_name": "enterprise-kb",
        }
    )

    result = retrieval.execute(
        {
            "query": "hoan tien",
            "filters": {"tags": ["refund"]},
            "index_name": "enterprise-kb",
        }
    )

    assert result.chunks


def test_retrieval_returns_empty_list_when_query_has_no_match() -> None:
    config = RuntimeConfig()
    vector_store = InMemoryVectorStore()
    embedding_provider = HashEmbeddingProvider()
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
    ingestion.execute(REFUND_DOCUMENT)

    result = retrieval.execute(
        {
            "query": NO_MATCH_QUERY,
            "index_name": "enterprise-kb",
        }
    )

    assert result.chunks == []


def test_retrieval_rejects_unknown_filter_key() -> None:
    config = RuntimeConfig()
    use_case = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
    )

    with pytest.raises(UnsupportedFilterError):
        use_case.execute(
            {
                "query": "hoan tien",
                "filters": {"foo": "bar"},
                "index_name": "enterprise-kb",
            }
        )


def test_retrieval_rejects_invalid_tags_filter_shape() -> None:
    config = RuntimeConfig()
    use_case = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
    )

    with pytest.raises(InvalidInputError) as exc_info:
        use_case.execute(
            {
                "query": "hoan tien",
                "filters": {"tags": []},
                "index_name": "enterprise-kb",
            }
        )

    assert exc_info.value.details == {"field": "filters.tags"}
