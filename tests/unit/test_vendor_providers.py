import pytest

from tuesday.rag.infrastructure.providers_vendor import (
    AzureOpenAIEmbeddingProvider,
    AzureOpenAILLMProvider,
    GeminiEmbeddingProvider,
    GeminiLLMProvider,
    OpenAIEmbeddingProvider,
    OpenAILLMProvider,
)


def test_openai_embedding_provider_uses_embeddings_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_post_json(
        *,
        url: str,
        headers: dict[str, str],
        payload: dict,
        timeout_seconds: float = 30.0,
    ):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        return {"data": [{"embedding": [1.0, 2.0]}, {"embedding": [3.0, 4.0]}]}

    monkeypatch.setattr("tuesday.rag.infrastructure.providers_vendor.post_json", fake_post_json)
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="text-embedding-3-small",
    )

    result = provider.embed_texts(["alpha", "beta"])

    assert result == [[1.0, 2.0], [3.0, 4.0]]
    assert captured["url"] == "https://api.openai.com/v1/embeddings"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "text-embedding-3-small"


def test_openai_llm_provider_parses_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post_json(
        *,
        url: str,
        headers: dict[str, str],
        payload: dict,
        timeout_seconds: float = 30.0,
    ):
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"answer":"According to policy","citations":["chunk-1"]}'
                    }
                }
            ]
        }

    monkeypatch.setattr("tuesday.rag.infrastructure.providers_vendor.post_json", fake_post_json)
    provider = OpenAILLMProvider(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
    )

    result = provider.generate_text("prompt")

    assert result.answer == "According to policy"
    assert result.citations == ["chunk-1"]


def test_gemini_embedding_provider_uses_embed_content(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_post_json(
        *,
        url: str,
        headers: dict[str, str],
        payload: dict,
        timeout_seconds: float = 30.0,
    ):
        captured["url"] = url
        captured["payload"] = payload
        return {"embedding": {"values": [0.1, 0.2]}}

    monkeypatch.setattr("tuesday.rag.infrastructure.providers_vendor.post_json", fake_post_json)
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        model="gemini-embedding-001",
    )

    result = provider.embed_query("refund policy")

    assert result == [0.1, 0.2]
    assert captured["url"].endswith("/models/gemini-embedding-001:embedContent?key=test-key")
    assert captured["payload"]["taskType"] == "RETRIEVAL_QUERY"


def test_gemini_llm_provider_parses_text_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post_json(
        *,
        url: str,
        headers: dict[str, str],
        payload: dict,
        timeout_seconds: float = 30.0,
    ):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"answer":"Refund in 7 days","citations":["chunk-abc"]}'
                            }
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr("tuesday.rag.infrastructure.providers_vendor.post_json", fake_post_json)
    provider = GeminiLLMProvider(
        api_key="test-key",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        model="gemini-2.5-flash",
    )

    result = provider.generate_text("prompt")

    assert result.answer == "Refund in 7 days"
    assert result.citations == ["chunk-abc"]


def test_azure_openai_embedding_provider_uses_deployment_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_post_json(
        *,
        url: str,
        headers: dict[str, str],
        payload: dict,
        timeout_seconds: float = 30.0,
    ):
        captured["url"] = url
        captured["headers"] = headers
        return {"data": [{"embedding": [9.0, 8.0]}]}

    monkeypatch.setattr("tuesday.rag.infrastructure.providers_vendor.post_json", fake_post_json)
    provider = AzureOpenAIEmbeddingProvider(
        api_key="test-key",
        endpoint="https://example.openai.azure.com",
        api_version="2024-10-21",
        deployment="embedding-deploy",
    )

    result = provider.embed_query("refund")

    assert result == [9.0, 8.0]
    assert "embedding-deploy/embeddings?api-version=2024-10-21" in captured["url"]
    assert captured["headers"]["api-key"] == "test-key"


def test_azure_openai_llm_provider_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post_json(
        *,
        url: str,
        headers: dict[str, str],
        payload: dict,
        timeout_seconds: float = 30.0,
    ):
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"answer":"Use support portal","citations":["chunk-1"]}'
                    }
                }
            ]
        }

    monkeypatch.setattr("tuesday.rag.infrastructure.providers_vendor.post_json", fake_post_json)
    provider = AzureOpenAILLMProvider(
        api_key="test-key",
        endpoint="https://example.openai.azure.com",
        api_version="2024-10-21",
        deployment="chat-deploy",
    )

    result = provider.generate_text("prompt")

    assert result.answer == "Use support portal"
    assert result.citations == ["chunk-1"]
