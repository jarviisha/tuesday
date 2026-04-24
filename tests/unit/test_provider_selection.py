import pytest

from tuesday.rag.infrastructure.providers import DeterministicLLMProvider, HashEmbeddingProvider
from tuesday.rag.infrastructure.providers_vendor import (
    LlamaIndexEmbeddingAdapter,
    LlamaIndexLLMAdapter,
)
from tuesday.runtime.config import RuntimeConfig
from tuesday.runtime.container import build_container


def test_build_container_uses_demo_providers_by_default() -> None:
    container = build_container(RuntimeConfig())

    assert isinstance(container.embedding_provider._provider, HashEmbeddingProvider)
    assert isinstance(container.llm_provider._provider, DeterministicLLMProvider)


def test_build_container_selects_openai_providers() -> None:
    container = build_container(
        RuntimeConfig(
            embedding_provider_backend="openai",
            generation_provider_backend="openai",
            openai_api_key="test-key",
            openai_embedding_model="text-embedding-3-small",
            openai_generation_model="gpt-4o-mini",
        )
    )

    assert isinstance(container.embedding_provider._provider, LlamaIndexEmbeddingAdapter)
    assert isinstance(container.llm_provider._provider, LlamaIndexLLMAdapter)


def test_build_container_selects_gemini_providers(monkeypatch: pytest.MonkeyPatch) -> None:

    from tuesday.rag.infrastructure.providers import DeterministicDenseEmbeddingProvider
    from tuesday.rag.infrastructure.providers import DeterministicLLMProvider as _DemoLLM

    monkeypatch.setattr(
        "tuesday.rag.infrastructure.providers_vendor.build_gemini_embedding",
        lambda config: LlamaIndexEmbeddingAdapter(DeterministicDenseEmbeddingProvider(dimension=8)),
    )
    monkeypatch.setattr(
        "tuesday.rag.infrastructure.providers_vendor.build_gemini_llm",
        lambda config: LlamaIndexLLMAdapter(_DemoLLM()),
    )
    container = build_container(
        RuntimeConfig(
            embedding_provider_backend="gemini",
            generation_provider_backend="gemini",
            gemini_api_key="test-key",
            gemini_embedding_model="gemini-embedding-001",
            gemini_generation_model="gemini-2.5-flash",
        )
    )

    assert isinstance(container.embedding_provider._provider, LlamaIndexEmbeddingAdapter)
    assert isinstance(container.llm_provider._provider, LlamaIndexLLMAdapter)


def test_build_container_selects_azure_openai_providers() -> None:
    container = build_container(
        RuntimeConfig(
            embedding_provider_backend="azure_openai",
            generation_provider_backend="azure_openai",
            azure_openai_api_key="test-key",
            azure_openai_endpoint="https://example.openai.azure.com",
            azure_openai_embedding_deployment="text-embedding-3-small",
            azure_openai_generation_deployment="gpt-4o-mini",
        )
    )

    assert isinstance(container.embedding_provider._provider, LlamaIndexEmbeddingAdapter)
    assert isinstance(container.llm_provider._provider, LlamaIndexLLMAdapter)


def test_runtime_config_requires_provider_specific_openai_fields() -> None:
    with pytest.raises(
        ValueError,
        match="openai_api_key is required for the selected provider backend",
    ):
        RuntimeConfig(embedding_provider_backend="openai").validate()
