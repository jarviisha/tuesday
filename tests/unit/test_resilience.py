import time

import pytest

from tuesday.rag.infrastructure.resilience import (
    ResilientEmbeddingProvider,
    ResilientLLMProvider,
    ResilientVectorStore,
    RetryableDependencyError,
    RetryExhaustedError,
)


class SlowEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        time.sleep(0.02)
        return [[1.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        time.sleep(0.02)
        return [1.0]


class FlakyEmbeddingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls == 1:
            raise RetryableDependencyError("temporary embed failure")
        return [[1.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        self.calls += 1
        if self.calls == 1:
            raise RetryableDependencyError("temporary embed failure")
        return [1.0]


class SlowGenerationProvider:
    def generate_text(self, prompt: str):
        time.sleep(0.02)
        return type("Result", (), {"answer": "ok", "citations": ["chunk-001"]})()


class SlowVectorStore:
    def replace_document(self, *, index_name: str, document_id: str, chunks: list) -> bool:
        time.sleep(0.02)
        return False

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list:
        time.sleep(0.02)
        return []


def test_resilient_embedding_provider_retries_transient_error() -> None:
    provider = ResilientEmbeddingProvider(
        FlakyEmbeddingProvider(),
        timeout_ms=100,
        max_retries=1,
    )

    result = provider.embed_query("refund")

    assert result == [1.0]


def test_resilient_embedding_provider_raises_after_timeout() -> None:
    provider = ResilientEmbeddingProvider(
        SlowEmbeddingProvider(),
        timeout_ms=1,
        max_retries=0,
    )

    with pytest.raises(RetryExhaustedError):
        provider.embed_query("refund")


def test_resilient_llm_provider_raises_after_timeout() -> None:
    provider = ResilientLLMProvider(
        SlowGenerationProvider(),
        timeout_ms=1,
        max_retries=0,
    )

    with pytest.raises(RetryExhaustedError):
        provider.generate_text("prompt")


def test_resilient_vector_store_raises_after_timeout() -> None:
    store = ResilientVectorStore(
        SlowVectorStore(),
        timeout_ms=1,
        max_retries=0,
    )

    with pytest.raises(RetryExhaustedError):
        store.query(
            index_name="enterprise-kb",
            query_embedding=[1.0],
            top_k=1,
            filters=None,
        )
