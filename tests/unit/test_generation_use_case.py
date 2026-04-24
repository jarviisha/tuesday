import pytest
from tests.fixtures import REFUND_DOCUMENT

from tuesday.rag.domain.errors import InvalidGenerationOutputError, InvalidInputError
from tuesday.rag.domain.models import LLMGenerationResult
from tuesday.rag.generation.service import GeneratorService
from tuesday.rag.generation.use_case import GenerationUseCase
from tuesday.rag.infrastructure.providers import DeterministicLLMProvider, HashEmbeddingProvider
from tuesday.rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.runtime.config import RuntimeConfig


class CountingLLMProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_text(self, prompt: str) -> LLMGenerationResult:
        self.calls += 1
        return LLMGenerationResult(
            answer=(
                "According to the available context, khach hang co the yeu cau "
                "hoan tien trong vong 7 ngay."
            ),
            citations=["chunk-doc-refund-001-0001"],
        )


class InvalidCitationLLMProvider:
    def generate_text(self, prompt: str) -> LLMGenerationResult:
        return LLMGenerationResult(
            answer=(
                "According to the available context, khach hang co the yeu cau "
                "hoan tien trong vong 7 ngay."
            ),
            citations=["chunk-does-not-exist"],
        )


def test_generation_returns_insufficient_context_without_llm_when_chunks_empty() -> None:
    config = RuntimeConfig()
    llm_provider = CountingLLMProvider()
    use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
        generator=GeneratorService(
            llm_provider,
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    result = use_case.execute(
        {
            "question": "Chinh sach hoan tien la gi?",
            "retrieved_chunks": [],
        }
    )

    assert result.insufficient_context is True
    assert result.grounded is False
    assert result.citations == []
    assert result.answer == config.insufficient_context_answer
    assert llm_provider.calls == 0


def test_generation_uses_question_as_retrieval_query_when_query_missing() -> None:
    config = RuntimeConfig()
    vector_store = InMemoryVectorStore()
    retriever = RetrieverService(HashEmbeddingProvider(), vector_store)
    generator = GeneratorService(
        DeterministicLLMProvider(),
        insufficient_context_answer=config.insufficient_context_answer,
    )

    from tuesday.rag.infrastructure.chunking import LlamaIndexNodeParser

    ingestion = IngestionUseCase(
        config=config,
        chunker=LlamaIndexNodeParser(
            chunk_size=config.ingestion_chunk_size_tokens_default,
            chunk_overlap=config.ingestion_chunk_overlap_tokens_default,
        ),
        indexer=IndexerService(HashEmbeddingProvider(), vector_store),
    )
    ingestion.execute(REFUND_DOCUMENT)

    use_case = GenerationUseCase(
        config=config,
        retriever=retriever,
        generator=generator,
    )

    result = use_case.execute(
        {
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
            "retrieval_request": {
                "filters": {"tags": ["refund"]},
            },
        }
    )

    assert result.insufficient_context is False
    assert result.grounded is True
    assert result.citations
    assert set(result.citations).issubset({chunk.chunk_id for chunk in result.used_chunks})
    assert "7 ngay" in result.answer
    assert "Context:" not in result.answer


def test_generation_returns_insufficient_context_when_chunks_do_not_cover_question() -> None:
    config = RuntimeConfig()
    llm_provider = CountingLLMProvider()
    use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
        generator=GeneratorService(
            llm_provider,
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    result = use_case.execute(
        {
            "question": "Muc phi hoan tien la bao nhieu?",
            "retrieved_chunks": [
                {
                    "chunk_id": "chunk-doc-refund-001-0001",
                    "document_id": "doc-refund-001",
                    "text": "Khach hang co the yeu cau hoan tien trong vong 7 ngay.",
                    "metadata": {"chunk_id": "chunk-doc-refund-001-0001"},
                }
            ],
        }
    )

    assert result.insufficient_context is True
    assert result.grounded is False
    assert result.citations == []
    assert result.answer == config.insufficient_context_answer
    assert result.used_chunks
    assert llm_provider.calls == 0


def test_generation_returns_insufficient_context_when_detail_signal_is_missing() -> None:
    config = RuntimeConfig()
    llm_provider = CountingLLMProvider()
    use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
        generator=GeneratorService(
            llm_provider,
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    result = use_case.execute(
        {
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "retrieved_chunks": [
                {
                    "chunk_id": "chunk-doc-refund-001-0001",
                    "document_id": "doc-refund-001",
                    "text": "Khach hang co the yeu cau hoan tien qua cong ho tro chinh thuc.",
                    "metadata": {"chunk_id": "chunk-doc-refund-001-0001"},
                }
            ],
        }
    )

    assert result.insufficient_context is True
    assert result.grounded is False
    assert result.citations == []
    assert result.answer == config.insufficient_context_answer
    assert result.used_chunks
    assert llm_provider.calls == 0


def test_generation_rejects_missing_retrieved_chunk_fields() -> None:
    config = RuntimeConfig()
    use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
        generator=GeneratorService(
            DeterministicLLMProvider(),
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    with pytest.raises(InvalidInputError) as exc_info:
        use_case.execute(
            {
                "question": "Khach hang duoc hoan tien trong bao lau?",
                "retrieved_chunks": [{"chunk_id": "chunk-001"}],
            }
        )

    assert exc_info.value.details == {"field": "retrieved_chunks.document_id"}


def test_generation_rejects_citation_outside_used_chunks() -> None:
    config = RuntimeConfig()
    use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(HashEmbeddingProvider(), InMemoryVectorStore()),
        generator=GeneratorService(
            InvalidCitationLLMProvider(),
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    with pytest.raises(InvalidGenerationOutputError):
        use_case.execute(
            {
                "question": "Khach hang duoc hoan tien trong bao lau?",
                "retrieved_chunks": [
                    {
                        "chunk_id": "chunk-doc-refund-001-0001",
                        "document_id": "doc-refund-001",
                        "text": "Khach hang co the yeu cau hoan tien trong vong 7 ngay.",
                        "metadata": {"chunk_id": "chunk-doc-refund-001-0001"},
                    }
                ],
            }
        )
