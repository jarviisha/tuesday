from tuesday.rag.domain.errors import InvalidInputError, RetrievalRequiredIndexMissingError
from tuesday.rag.domain.models import (
    GeneratedAnswer,
    GenerationRequest,
    RetrievalRequest,
    RetrievedChunk,
)
from tuesday.rag.generation.service import GeneratorService
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.runtime.config import RuntimeConfig
from tuesday.shared.validation import (
    enforce_length,
    require_non_blank,
    validate_filters,
    validate_max_context_chunks,
    validate_top_k,
)


class GenerationUseCase:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        retriever: RetrieverService,
        generator: GeneratorService,
    ) -> None:
        self._config = config
        self._retriever = retriever
        self._generator = generator

    def execute(self, payload: dict) -> GeneratedAnswer:
        question = enforce_length(
            require_non_blank(payload.get("question", ""), "question"),
            "question",
            minimum=self._config.question_length_min,
            maximum=self._config.question_length_max,
        )
        raw_retrieved_chunks = payload.get("retrieved_chunks")
        retrieval_request_payload = payload.get("retrieval_request")
        if raw_retrieved_chunks is None and retrieval_request_payload is None:
            raise InvalidInputError(
                "Either retrieval_request or retrieved_chunks is required",
                details={"field": "retrieval_request"},
            )

        retrieved_chunks = None
        retrieval_request = None
        if raw_retrieved_chunks is not None:
            retrieved_chunks = [self._to_retrieved_chunk(item) for item in raw_retrieved_chunks]
        elif retrieval_request_payload is not None:
            index_name = retrieval_request_payload.get("index_name") or payload.get("index_name")
            if not index_name:
                raise RetrievalRequiredIndexMissingError(
                    "index_name is required for internal retrieval",
                )
            retrieval_request = RetrievalRequest(
                query=retrieval_request_payload.get("query") or question,
                top_k=validate_top_k(
                    retrieval_request_payload.get(
                        "top_k",
                        self._config.retrieval_top_k_default,
                    ),
                    self._config,
                ),
                filters=validate_filters(retrieval_request_payload.get("filters")),
                index_name=index_name,
                request_id=payload.get("request_id"),
            )
            retrieved_chunks = self._retriever.retrieve(retrieval_request).chunks

        generation_request = GenerationRequest(
            question=question,
            retrieval_request=retrieval_request,
            retrieved_chunks=retrieved_chunks,
            max_context_chunks=validate_max_context_chunks(
                payload.get(
                    "max_context_chunks",
                    self._config.generation_max_context_chunks_default,
                ),
                self._config,
            ),
            request_id=payload.get("request_id"),
        )
        return self._generator.generate(generation_request)

    @staticmethod
    def _to_retrieved_chunk(payload: dict) -> RetrievedChunk:
        for field in ("chunk_id", "document_id", "text", "metadata"):
            if field not in payload:
                raise InvalidInputError(
                    f"retrieved_chunks.{field} is required",
                    details={"field": f"retrieved_chunks.{field}"},
                )
        return RetrievedChunk(
            chunk_id=payload["chunk_id"],
            document_id=payload["document_id"],
            text=payload["text"],
            score=payload.get("score", 0.0),
            metadata=payload["metadata"],
        )
