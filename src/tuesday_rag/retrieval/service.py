from tuesday_rag.domain.errors import EmbeddingError, RetrievalError
from tuesday_rag.domain.models import RetrievalRequest, RetrievalResponse
from tuesday_rag.domain.ports import EmbeddingProvider, VectorStore


class RetrieverService:
    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        try:
            query_embedding = self._embedding_provider.embed_query(request.query)
        except Exception as exc:
            raise EmbeddingError("Failed to generate an embedding for the query") from exc
        try:
            chunks = self._vector_store.query(
                index_name=request.index_name,
                query_embedding=query_embedding,
                top_k=request.top_k,
                filters=request.filters,
            )
        except Exception as exc:
            raise RetrievalError("Failed to retrieve data from the vector store") from exc
        chunks = sorted(chunks, key=lambda chunk: chunk.score, reverse=True)
        return RetrievalResponse(
            query=request.query,
            top_k=request.top_k,
            chunks=chunks,
            applied_filters=request.filters or {},
            index_name=request.index_name,
        )
