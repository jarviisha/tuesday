import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tuesday.api.error_mapping import map_domain_error
from tuesday.api.middleware import request_context_middleware
from tuesday.api.observability import classify_domain_error
from tuesday.rag.api.router import create_router
from tuesday.rag.api.schemas import ErrorResponseSchema
from tuesday.rag.domain.errors import DomainError
from tuesday.runtime.container import build_runtime_from_env

logger = logging.getLogger("tuesday.api")


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = build_runtime_from_env()
        yield

    app = FastAPI(title="Tuesday", lifespan=lifespan)
    app.middleware("http")(request_context_middleware)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, error: DomainError):
        status_code, body = map_domain_error(error)
        request.state.error_code = error.error_code
        error_context = classify_domain_error(error)
        request.state.failure_group = error_context["failure_group"]
        request.state.failure_component = error_context["failure_component"]
        request.state.failure_mode = error_context["failure_mode"]
        request.state.retry_count = error_context["retry_count"]
        request.state.timeout_ms = error_context["timeout_ms"]
        logger.warning(
            "request.failed",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "use_case": getattr(request.state, "use_case", request.url.path),
                "error_code": error.error_code,
                "latency_ms": None,
                "failure_group": error_context["failure_group"],
                "failure_component": error_context["failure_component"],
                "failure_mode": error_context["failure_mode"],
                "retry_count": error_context["retry_count"],
                "timeout_ms": error_context["timeout_ms"],
            },
        )
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponseSchema(**body).model_dump(),
        )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(create_router())
    return app


app = create_app()
