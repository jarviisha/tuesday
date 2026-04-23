import pytest
from tests.fixtures import REFUND_DOCUMENT

from tuesday_rag.domain.models import LLMGenerationResult


@pytest.mark.anyio
async def test_generate_returns_400_when_internal_retrieval_index_name_missing(api_client) -> None:
    response = await api_client.post(
        "/generate",
        json={
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "retrieval_request": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "RETRIEVAL_REQUIRED_INDEX_MISSING"


@pytest.mark.anyio
async def test_retrieve_returns_400_for_unsupported_filter(api_client) -> None:
    response = await api_client.post(
        "/retrieve",
        json={
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "filters": {"foo": "bar"},
            "index_name": "enterprise-kb",
        },
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILTER"


@pytest.mark.anyio
async def test_documents_index_returns_400_for_invalid_input(api_client) -> None:
    response = await api_client.post(
        "/documents/index",
        json={**REFUND_DOCUMENT, "content": "   "},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"


@pytest.mark.anyio
async def test_retrieve_returns_502_for_embedding_error(
    api_app,
    api_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_embed_query(_: str) -> list[float]:
        raise RuntimeError("embed failed")

    monkeypatch.setattr(api_app.state.container.embedding_provider, "embed_query", fail_embed_query)
    response = await api_client.post(
        "/retrieve",
        json={
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        },
    )

    assert response.status_code == 502
    assert response.json()["error_code"] == "EMBEDDING_ERROR"


@pytest.mark.anyio
async def test_generate_returns_502_for_generation_error(
    api_app,
    api_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_generate(_: str) -> LLMGenerationResult:
        raise RuntimeError("llm failed")

    monkeypatch.setattr(api_app.state.container.llm_provider, "generate_text", fail_generate)
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    response = await api_client.post(
        "/generate",
        json={
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
            "retrieval_request": {"filters": {"tags": ["refund"]}},
        },
    )

    assert response.status_code == 502
    assert response.json()["error_code"] == "GENERATION_ERROR"
