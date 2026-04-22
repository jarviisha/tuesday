import httpx
import pytest
from tests.fixtures import NO_MATCH_QUERY, ONBOARDING_DOCUMENT, REFUND_DOCUMENT

from tuesday_rag.api.app import app


@pytest.mark.anyio
async def test_documents_index_contract_supports_reindex() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        first_response = await client.post("/documents/index", json=REFUND_DOCUMENT)
        second_response = await client.post("/documents/index", json=REFUND_DOCUMENT)

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "indexed"
    assert first_response.json()["replaced_document"] is False
    assert second_response.status_code == 200
    assert second_response.json()["replaced_document"] is True
    assert "x-request-id" in second_response.headers
    assert "x-latency-ms" in second_response.headers


@pytest.mark.anyio
async def test_documents_index_rejects_blank_content() -> None:
    transport = httpx.ASGITransport(app=app)
    payload = {**REFUND_DOCUMENT, "content": "   "}
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/documents/index", json=payload)

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"


@pytest.mark.anyio
async def test_retrieve_contract_applies_tags_contains_any() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/documents/index", json=REFUND_DOCUMENT)
        await client.post("/documents/index", json=ONBOARDING_DOCUMENT)
        response = await client.post(
            "/retrieve",
            json={
                "query": "Khach hang duoc hoan tien trong bao lau?",
                "top_k": 3,
                "filters": {"language": "vi", "tags": ["refund"]},
                "index_name": "enterprise-kb",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["applied_filters"] == {"language": "vi", "tags": ["refund"]}
    assert body["chunks"]
    assert any(chunk["document_id"] == "doc-refund-001" for chunk in body["chunks"])


@pytest.mark.anyio
async def test_retrieve_contract_returns_empty_chunks_when_no_match() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/documents/index", json=REFUND_DOCUMENT)
        response = await client.post(
            "/retrieve",
            json={"query": NO_MATCH_QUERY, "index_name": "enterprise-kb"},
        )

    assert response.status_code == 200
    assert response.json()["chunks"] == []


@pytest.mark.anyio
async def test_retrieve_contract_rejects_unknown_filter() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/retrieve",
            json={
                "query": "How long do customers have to request a refund?",
                "filters": {"foo": "bar"},
                "index_name": "enterprise-kb",
            },
        )

    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILTER"


@pytest.mark.anyio
async def test_generate_contract_uses_retrieved_chunks() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/documents/index", json=REFUND_DOCUMENT)
        retrieve_response = await client.post(
            "/retrieve",
            json={
                "query": "Khach hang duoc hoan tien trong bao lau?",
                "index_name": "enterprise-kb",
            },
        )
        response = await client.post(
            "/generate",
            json={
                "question": "Khach hang duoc hoan tien trong bao lau?",
                "retrieved_chunks": retrieve_response.json()["chunks"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_context"] is False
    assert body["grounded"] is True
    assert body["citations"]
    assert set(body["citations"]).issubset({chunk["chunk_id"] for chunk in body["used_chunks"]})
    assert "7 ngay" in body["answer"]
    assert "Context:" not in body["answer"]


@pytest.mark.anyio
async def test_generate_contract_performs_internal_retrieval() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/documents/index", json=REFUND_DOCUMENT)
        response = await client.post(
            "/generate",
            json={
                "question": "Khach hang duoc hoan tien trong bao lau?",
                "index_name": "enterprise-kb",
                "retrieval_request": {
                    "filters": {"tags": ["refund"]},
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_context"] is False
    assert body["grounded"] is True
    assert body["citations"]
    assert "7 ngay" in body["answer"]
    assert "Context:" not in body["answer"]


@pytest.mark.anyio
async def test_generate_contract_returns_insufficient_context() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/documents/index", json=REFUND_DOCUMENT)
        response = await client.post(
            "/generate",
            json={
                "question": NO_MATCH_QUERY,
                "index_name": "enterprise-kb",
                "retrieval_request": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_context"] is True
    assert body["grounded"] is False
    assert body["citations"] == []
