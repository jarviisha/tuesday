from tuesday_rag.domain.errors import EmbeddingError, IndexWriteError
from tuesday_rag.domain.models import Chunk, IndexedChunk
from tuesday_rag.domain.ports import EmbeddingProvider, VectorStore


class IndexerService:
    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def index_chunks(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[Chunk],
    ) -> tuple[list[IndexedChunk], bool]:
        try:
            embeddings = self._embedding_provider.embed_texts([chunk.text for chunk in chunks])
        except Exception as exc:
            raise EmbeddingError("Không thể sinh embedding cho tài liệu") from exc
        indexed_chunks = [
            IndexedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                embedding=embedding,
                metadata=chunk.metadata,
                index_name=index_name,
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        try:
            replaced_document = self._vector_store.replace_document(
                index_name=index_name,
                document_id=document_id,
                chunks=indexed_chunks,
            )
        except Exception as exc:
            raise IndexWriteError("Không thể ghi dữ liệu vào vector store") from exc
        return indexed_chunks, replaced_document
