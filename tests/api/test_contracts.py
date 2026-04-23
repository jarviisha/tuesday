import pytest
from tests.fixtures import NO_MATCH_QUERY, ONBOARDING_DOCUMENT, REFUND_DOCUMENT


@pytest.mark.anyio
async def test_documents_index_contract_supports_reindex(api_client) -> None:
    first_response = await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    second_response = await api_client.post("/documents/index", json=REFUND_DOCUMENT)

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "indexed"
    assert first_response.json()["replaced_document"] is False
    assert second_response.status_code == 200
    assert second_response.json()["replaced_document"] is True
    assert "x-request-id" in second_response.headers
    assert "x-latency-ms" in second_response.headers


@pytest.mark.anyio
async def test_documents_index_rejects_blank_content(api_client) -> None:
    payload = {**REFUND_DOCUMENT, "content": "   "}
    response = await api_client.post("/documents/index", json=payload)

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"


@pytest.mark.anyio
async def test_retrieve_contract_applies_tags_contains_any(api_client) -> None:
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    await api_client.post("/documents/index", json=ONBOARDING_DOCUMENT)
    response = await api_client.post(
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
async def test_retrieve_contract_returns_empty_chunks_when_no_match(api_client) -> None:
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    response = await api_client.post(
        "/retrieve",
        json={"query": NO_MATCH_QUERY, "index_name": "enterprise-kb"},
    )

    assert response.status_code == 200
    assert response.json()["chunks"] == []


@pytest.mark.anyio
async def test_retrieve_contract_rejects_unknown_filter(api_client) -> None:
    response = await api_client.post(
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
async def test_generate_contract_uses_retrieved_chunks(api_client) -> None:
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    retrieve_response = await api_client.post(
        "/retrieve",
        json={
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        },
    )
    response = await api_client.post(
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
async def test_generate_contract_performs_internal_retrieval(api_client) -> None:
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    response = await api_client.post(
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
async def test_generate_contract_returns_insufficient_context(api_client) -> None:
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    response = await api_client.post(
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
    assert body["answer"] == "Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn."


@pytest.mark.anyio
async def test_generate_contract_returns_insufficient_context_for_related_but_incomplete_chunks(
    api_client,
) -> None:
    response = await api_client.post(
        "/generate",
        json={
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "retrieved_chunks": [
                {
                    "chunk_id": "chunk-doc-refund-001-0001",
                    "document_id": "doc-refund-001",
                    "text": "Khach hang co the yeu cau hoan tien qua cong ho tro chinh thuc.",
                    "score": 0.91,
                    "metadata": {
                        "chunk_id": "chunk-doc-refund-001-0001",
                        "document_id": "doc-refund-001",
                        "source_type": "text",
                    },
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_context"] is True
    assert body["grounded"] is False
    assert body["citations"] == []
    assert body["used_chunks"]
