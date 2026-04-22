import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tuesday_rag.api.error_mapping import map_domain_error
from tuesday_rag.api.observability import classify_domain_error
from tuesday_rag.api.schemas import (
    DocumentIndexRequest,
    DocumentIndexResponse,
    ErrorResponseSchema,
    GenerationRequestSchema,
    GenerationResponseSchema,
    RetrievalRequestSchema,
    RetrievalResponseSchema,
)
from tuesday_rag.domain.errors import DomainError
from tuesday_rag.runtime.container import container

logger = logging.getLogger("tuesday_rag.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="Tuesday RAG Core", lifespan=lifespan)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
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
    return JSONResponse(status_code=status_code, content=ErrorResponseSchema(**body).model_dump())


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/documents/index", response_model=DocumentIndexResponse)
async def index_document(request: Request, payload: DocumentIndexRequest) -> DocumentIndexResponse:
    request.state.use_case = "documents.index"
    data = payload.model_dump()
    data["request_id"] = request.state.request_id
    result = container.ingestion_use_case.execute(data)
    return DocumentIndexResponse(**result.__dict__)


@app.post("/retrieve", response_model=RetrievalResponseSchema)
async def retrieve(request: Request, payload: RetrievalRequestSchema) -> RetrievalResponseSchema:
    request.state.use_case = "retrieve"
    data = payload.model_dump()
    data["request_id"] = request.state.request_id
    result = container.retrieval_use_case.execute(data)
    return RetrievalResponseSchema(**result.__dict__)


@app.post("/generate", response_model=GenerationResponseSchema)
async def generate(request: Request, payload: GenerationRequestSchema) -> GenerationResponseSchema:
    request.state.use_case = "generate"
    data = payload.model_dump()
    data["request_id"] = request.state.request_id
    result = container.generation_use_case.execute(data)
    return GenerationResponseSchema(**result.__dict__)
