from tests.fixtures import REFUND_DOCUMENT

from tuesday.rag.generation.service import GeneratorService
from tuesday.rag.generation.use_case import GenerationUseCase
from tuesday.rag.infrastructure.chunking import LlamaIndexNodeParser
from tuesday.rag.infrastructure.providers import (
    DeterministicDenseEmbeddingProvider,
    DeterministicLLMProvider,
)
from tuesday.rag.infrastructure.qdrant_vector_store import LlamaIndexQdrantAdapter
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.rag.retrieval.use_case import RetrievalUseCase
from tuesday.runtime.config import RuntimeConfig


def test_qdrant_smoke_index_retrieve_generate_flow() -> None:
    config = RuntimeConfig(
        vector_store_backend="qdrant",
        qdrant_location=":memory:",
        qdrant_collection_prefix="smoke",
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
    chunker = LlamaIndexNodeParser(
        chunk_size=config.ingestion_chunk_size_tokens_default,
        chunk_overlap=config.ingestion_chunk_overlap_tokens_default,
    )
    retriever = RetrieverService(embedding_provider, vector_store)
    generator = GeneratorService(
        DeterministicLLMProvider(),
        insufficient_context_answer=config.insufficient_context_answer,
    )
    ingestion = IngestionUseCase(
        config=config,
        chunker=chunker,
        indexer=IndexerService(embedding_provider, vector_store),
    )
    generation = GenerationUseCase(
        config=config,
        retriever=retriever,
        generator=generator,
    )
    retrieval = RetrievalUseCase(
        config=config,
        retriever=retriever,
    )

    index_result = ingestion.execute(REFUND_DOCUMENT)
    retrieval_result = retrieval.execute(
        {
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        }
    )
    generation_result = generation.execute(
        {
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "retrieval_request": {
                "filters": {"tags": ["refund"]},
                "index_name": "enterprise-kb",
            },
        }
    )

    assert index_result.status == "indexed"
    assert retrieval_result.chunks
    assert retrieval_result.applied_filters == {}
    assert generation_result.grounded is True
    assert generation_result.insufficient_context is False
    assert generation_result.citations
    assert generation_result.used_chunks
