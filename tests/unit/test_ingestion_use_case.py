import pytest
from tests.fixtures import ONBOARDING_DOCUMENT, REFUND_DOCUMENT

from tuesday_rag.config import RuntimeConfig
from tuesday_rag.domain.errors import (
    ChunkingError,
    EmbeddingError,
    IndexWriteError,
    InvalidInputError,
)
from tuesday_rag.domain.models import Chunk, IndexedChunk, SourceDocument
from tuesday_rag.infrastructure.chunking import CharacterChunker
from tuesday_rag.infrastructure.providers import HashEmbeddingProvider
from tuesday_rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday_rag.ingestion.service import IndexerService
from tuesday_rag.ingestion.use_case import IngestionUseCase


class EmptyChunker:
    def chunk(self, document: SourceDocument) -> list[Chunk]:
        return []


class OneChunker:
    def chunk(self, document: SourceDocument) -> list[Chunk]:
        return [
            Chunk(
                chunk_id="chunk-001",
                document_id=document.document_id,
                text=document.content,
                sequence_no=1,
                token_count=None,
                char_start=0,
                char_end=len(document.content),
                metadata={"chunk_id": "chunk-001", "document_id": document.document_id},
            )
        ]


class FailingEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embedding failed")

    def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("query embedding failed")


class FailingVectorStore:
    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[IndexedChunk],
    ) -> bool:
        raise RuntimeError("index write failed")

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list:
        return []


def test_ingestion_returns_replaced_document_false_on_first_index() -> None:
    config = RuntimeConfig()
    chunker = CharacterChunker(
        chunk_size=config.ingestion_chunk_size_chars_default,
        chunk_overlap=config.ingestion_chunk_overlap_chars_default,
    )
    vector_store = InMemoryVectorStore()
    use_case = IngestionUseCase(
        config=config,
        chunker=chunker,
        indexer=IndexerService(HashEmbeddingProvider(), vector_store),
    )

    result = use_case.execute(
        {
            **REFUND_DOCUMENT,
            "content": "Test content " * 100,
        }
    )

    assert result.status == "indexed"
    assert result.replaced_document is False
    assert result.indexed_count > 0


def test_ingestion_returns_replaced_document_true_on_reindex() -> None:
    config = RuntimeConfig()
    chunker = CharacterChunker(
        chunk_size=config.ingestion_chunk_size_chars_default,
        chunk_overlap=config.ingestion_chunk_overlap_chars_default,
    )
    vector_store = InMemoryVectorStore()
    use_case = IngestionUseCase(
        config=config,
        chunker=chunker,
        indexer=IndexerService(HashEmbeddingProvider(), vector_store),
    )

    first_result = use_case.execute(REFUND_DOCUMENT)
    second_result = use_case.execute(REFUND_DOCUMENT)

    assert first_result.replaced_document is False
    assert second_result.replaced_document is True
    assert second_result.indexed_count == second_result.chunk_count


def test_ingestion_creates_multiple_chunks_for_long_document() -> None:
    config = RuntimeConfig()
    chunker = CharacterChunker(
        chunk_size=config.ingestion_chunk_size_chars_default,
        chunk_overlap=config.ingestion_chunk_overlap_chars_default,
    )
    vector_store = InMemoryVectorStore()
    use_case = IngestionUseCase(
        config=config,
        chunker=chunker,
        indexer=IndexerService(HashEmbeddingProvider(), vector_store),
    )

    result = use_case.execute(ONBOARDING_DOCUMENT)

    assert result.chunk_count > 1
    assert result.indexed_count == result.chunk_count


def test_ingestion_rejects_invalid_metadata_tags() -> None:
    config = RuntimeConfig()
    use_case = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(HashEmbeddingProvider(), InMemoryVectorStore()),
    )

    with pytest.raises(InvalidInputError) as exc_info:
        use_case.execute(
            {
                **REFUND_DOCUMENT,
                "metadata": {"language": "vi", "tags": ["refund", ""]},
            }
        )

    assert exc_info.value.error_code == "INVALID_INPUT"
    assert exc_info.value.details == {"field": "metadata.tags"}


def test_ingestion_raises_chunking_error_when_chunker_returns_empty() -> None:
    config = RuntimeConfig()
    use_case = IngestionUseCase(
        config=config,
        chunker=EmptyChunker(),
        indexer=IndexerService(HashEmbeddingProvider(), InMemoryVectorStore()),
    )

    with pytest.raises(ChunkingError):
        use_case.execute(REFUND_DOCUMENT)


def test_ingestion_raises_embedding_error_from_provider() -> None:
    config = RuntimeConfig()
    use_case = IngestionUseCase(
        config=config,
        chunker=OneChunker(),
        indexer=IndexerService(FailingEmbeddingProvider(), InMemoryVectorStore()),
    )

    with pytest.raises(EmbeddingError):
        use_case.execute(REFUND_DOCUMENT)


def test_ingestion_raises_index_write_error_from_vector_store() -> None:
    config = RuntimeConfig()
    use_case = IngestionUseCase(
        config=config,
        chunker=OneChunker(),
        indexer=IndexerService(HashEmbeddingProvider(), FailingVectorStore()),
    )

    with pytest.raises(IndexWriteError):
        use_case.execute(REFUND_DOCUMENT)
