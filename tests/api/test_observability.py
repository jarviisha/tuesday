import httpx
import pytest
from tests.fixtures import REFUND_DOCUMENT

from tuesday_rag.api.app import app


@pytest.mark.anyio
async def test_request_logs_include_lifecycle_fields(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO", logger="tuesday_rag.api")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/documents/index", json=REFUND_DOCUMENT)

    assert response.status_code == 200
    completion_records = [
        record
        for record in caplog.records
        if record.name == "tuesday_rag.api" and record.msg == "request.completed"
    ]
    assert completion_records
    record = completion_records[-1]
    assert record.request_id
    assert record.use_case == "documents.index"
    assert record.error_code is None
    assert isinstance(record.latency_ms, int)
    assert record.failure_group is None
    assert record.failure_component is None
    assert record.retry_count == 0


@pytest.mark.anyio
async def test_failed_request_logs_include_error_code(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO", logger="tuesday_rag.api")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/documents/index", json={**REFUND_DOCUMENT, "content": "   "})

    assert response.status_code == 400
    failure_records = [
        record
        for record in caplog.records
        if record.name == "tuesday_rag.api" and record.msg == "request.failed"
    ]
    assert failure_records
    record = failure_records[-1]
    assert record.request_id
    assert record.use_case == "documents.index"
    assert record.error_code == "INVALID_INPUT"
    assert record.failure_group == "application"
    assert record.failure_component == "request_validation"
    assert record.failure_mode == "handled_error"
    assert record.retry_count == 0
