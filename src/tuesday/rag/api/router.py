from fastapi import APIRouter, Request

from tuesday.rag.api.schemas import (
    DocumentIndexRequest,
    DocumentIndexResponse,
    GenerationRequestSchema,
    GenerationResponseSchema,
    RetrievalRequestSchema,
    RetrievalResponseSchema,
)


def create_router() -> APIRouter:
    router = APIRouter()

    @router.post("/documents/index", response_model=DocumentIndexResponse)
    async def index_document(
        request: Request,
        payload: DocumentIndexRequest,
    ) -> DocumentIndexResponse:
        request.state.use_case = "documents.index"
        data = payload.model_dump()
        data["request_id"] = request.state.request_id
        result = request.app.state.container.ingestion_use_case.execute(data)
        return DocumentIndexResponse(**result.__dict__)

    @router.post("/retrieve", response_model=RetrievalResponseSchema)
    async def retrieve(
        request: Request,
        payload: RetrievalRequestSchema,
    ) -> RetrievalResponseSchema:
        request.state.use_case = "retrieve"
        data = payload.model_dump()
        data["request_id"] = request.state.request_id
        result = request.app.state.container.retrieval_use_case.execute(data)
        return RetrievalResponseSchema(**result.__dict__)

    @router.post("/generate", response_model=GenerationResponseSchema)
    async def generate(
        request: Request,
        payload: GenerationRequestSchema,
    ) -> GenerationResponseSchema:
        request.state.use_case = "generate"
        data = payload.model_dump()
        data["request_id"] = request.state.request_id
        result = request.app.state.container.generation_use_case.execute(data)
        return GenerationResponseSchema(**result.__dict__)

    return router
