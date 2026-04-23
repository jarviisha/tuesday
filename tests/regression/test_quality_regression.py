import pytest
from tests.fixtures import ONBOARDING_DOCUMENT, REFUND_DOCUMENT

from tuesday.rag.evaluation.golden_cases import GENERATION_GOLDEN_CASES, RETRIEVAL_GOLDEN_CASES


@pytest.mark.anyio
async def test_regression_suite_preserves_quality_invariants(api_client) -> None:
    await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    await api_client.post("/documents/index", json=ONBOARDING_DOCUMENT)

    for case in RETRIEVAL_GOLDEN_CASES:
        response = await api_client.post(
            "/retrieve",
            json={
                "query": case.query,
                "index_name": case.index_name,
                "filters": case.filters,
            },
        )
        assert response.status_code == 200, case.case_id
        chunks = response.json()["chunks"]
        if case.expected_empty:
            assert chunks == [], case.case_id
            continue
        assert chunks, case.case_id
        returned_ids = {chunk["document_id"] for chunk in chunks}
        assert returned_ids.issuperset(case.expected_document_ids), case.case_id

    for case in GENERATION_GOLDEN_CASES:
        response = await api_client.post(
            "/generate",
            json={
                "question": case.question,
                "index_name": case.index_name,
                "retrieval_request": case.retrieval_request,
            },
        )
        assert response.status_code == 200, case.case_id
        body = response.json()
        assert body["insufficient_context"] is case.expected_insufficient_context, case.case_id
        assert body["grounded"] is case.expected_grounded, case.case_id
        if case.expected_answer_substring is not None:
            assert case.expected_answer_substring in body["answer"], case.case_id
            assert set(body["citations"]).issubset(
                {chunk["chunk_id"] for chunk in body["used_chunks"]}
            ), case.case_id
        else:
            assert body["citations"] == [], case.case_id


@pytest.mark.anyio
async def test_regression_suite_preserves_reindex_and_filter_semantics(api_client) -> None:
    first_index = await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    second_index = await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    retrieve_response = await api_client.post(
        "/retrieve",
        json={
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
            "filters": {"tags": ["refund"]},
        },
    )

    assert first_index.status_code == 200
    assert second_index.status_code == 200
    assert first_index.json()["replaced_document"] is False
    assert second_index.json()["replaced_document"] is True
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["chunks"]
