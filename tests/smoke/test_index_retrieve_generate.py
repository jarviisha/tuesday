import pytest
from tests.fixtures import REFUND_DOCUMENT


@pytest.mark.anyio
async def test_smoke_index_retrieve_generate_flow(api_client) -> None:
    index_response = await api_client.post("/documents/index", json=REFUND_DOCUMENT)
    retrieve_response = await api_client.post(
        "/retrieve",
        json={
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        },
    )
    generate_response = await api_client.post(
        "/generate",
        json={
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "retrieval_request": {
                "filters": {"tags": ["refund"]},
                "index_name": "enterprise-kb",
            },
        },
    )

    assert index_response.status_code == 200
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["chunks"]
    assert generate_response.status_code == 200
    assert generate_response.json()["grounded"] is True
    assert generate_response.json()["insufficient_context"] is False
    assert generate_response.json()["citations"]
