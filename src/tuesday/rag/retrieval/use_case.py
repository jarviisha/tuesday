from tuesday.rag.domain.models import RetrievalRequest, RetrievalResponse
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.runtime.config import RuntimeConfig
from tuesday.shared.validation import (
    enforce_length,
    require_non_blank,
    validate_filters,
    validate_top_k,
)


class RetrievalUseCase:
    def __init__(self, *, config: RuntimeConfig, retriever: RetrieverService) -> None:
        self._config = config
        self._retriever = retriever

    def execute(self, payload: dict) -> RetrievalResponse:
        query = enforce_length(
            require_non_blank(payload.get("query", ""), "query"),
            "query",
            minimum=self._config.query_length_min,
            maximum=self._config.query_length_max,
        )
        top_k = validate_top_k(
            payload.get("top_k", self._config.retrieval_top_k_default),
            self._config,
        )
        filters = validate_filters(payload.get("filters"))
        request = RetrievalRequest(
            query=query,
            top_k=top_k,
            filters=filters,
            index_name=require_non_blank(payload.get("index_name", ""), "index_name"),
            request_id=payload.get("request_id"),
        )
        return self._retriever.retrieve(request)
