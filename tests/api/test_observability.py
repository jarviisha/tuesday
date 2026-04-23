import pytest
from tests.fixtures import REFUND_DOCUMENT


def _record_extra(record, field: str):
    return getattr(record, field, None)


@pytest.mark.anyio
async def test_request_logs_include_lifecycle_fields(
    api_client,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="tuesday.api")
    response = await api_client.post("/documents/index", json=REFUND_DOCUMENT)

    assert response.status_code == 200
    completion_records = [
        record
        for record in caplog.records
        if record.name == "tuesday.api" and record.msg == "request.completed"
    ]
    assert completion_records
    record = completion_records[-1]
    assert _record_extra(record, "request_id")
    assert _record_extra(record, "use_case") == "documents.index"
    assert _record_extra(record, "error_code") is None
    assert isinstance(_record_extra(record, "latency_ms"), int)
    assert _record_extra(record, "failure_group") is None
    assert _record_extra(record, "failure_component") is None
    assert _record_extra(record, "retry_count") == 0


@pytest.mark.anyio
async def test_failed_request_logs_include_error_code(
    api_client,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="tuesday.api")
    response = await api_client.post("/documents/index", json={**REFUND_DOCUMENT, "content": "   "})

    assert response.status_code == 400
    failure_records = [
        record
        for record in caplog.records
        if record.name == "tuesday.api" and record.msg == "request.failed"
    ]
    assert failure_records
    record = failure_records[-1]
    assert _record_extra(record, "request_id")
    assert _record_extra(record, "use_case") == "documents.index"
    assert _record_extra(record, "error_code") == "INVALID_INPUT"
    assert _record_extra(record, "failure_group") == "application"
    assert _record_extra(record, "failure_component") == "request_validation"
    assert _record_extra(record, "failure_mode") == "handled_error"
    assert _record_extra(record, "retry_count") == 0
