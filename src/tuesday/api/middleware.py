import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger("tuesday.api")


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started_at = time.perf_counter()
    request.state.request_id = request_id
    request.state.error_code = None
    request.state.failure_group = None
    request.state.failure_component = None
    request.state.failure_mode = None
    request.state.retry_count = 0
    request.state.timeout_ms = None
    response = await call_next(request)
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    response.headers["x-request-id"] = request_id
    response.headers["x-latency-ms"] = str(latency_ms)
    logger.info(
        "request.completed",
        extra={
            "request_id": request_id,
            "use_case": getattr(request.state, "use_case", request.url.path),
            "error_code": getattr(request.state, "error_code", None),
            "latency_ms": latency_ms,
            "failure_group": getattr(request.state, "failure_group", None),
            "failure_component": getattr(request.state, "failure_component", None),
            "failure_mode": getattr(request.state, "failure_mode", None),
            "retry_count": getattr(request.state, "retry_count", 0),
            "timeout_ms": getattr(request.state, "timeout_ms", None),
        },
    )
    return response
