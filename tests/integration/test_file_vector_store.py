from pathlib import Path

from tests.fixtures import REFUND_DOCUMENT

from tuesday.rag.infrastructure.chunking import CharacterChunker
from tuesday.rag.infrastructure.file_vector_store import FileBackedVectorStore
from tuesday.rag.infrastructure.providers import HashEmbeddingProvider
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.rag.retrieval.use_case import RetrievalUseCase
from tuesday.runtime.config import RuntimeConfig


def _build_use_cases(file_path: Path) -> tuple[IngestionUseCase, RetrievalUseCase]:
    config = RuntimeConfig()
    vector_store = FileBackedVectorStore(str(file_path))
    embedding_provider = HashEmbeddingProvider()
    ingestion = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(embedding_provider, vector_store),
    )
    retrieval = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
    )
    return ingestion, retrieval


def test_file_vector_store_persists_across_restart(tmp_path: Path) -> None:
    file_path = tmp_path / "vector-store.json"
    ingestion, _ = _build_use_cases(file_path)

    first_result = ingestion.execute(REFUND_DOCUMENT)

    _, retrieval_after_restart = _build_use_cases(file_path)
    result = retrieval_after_restart.execute(
        {
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        }
    )

    assert first_result.replaced_document is False
    assert result.chunks
    assert any("7 ngay" in chunk.text for chunk in result.chunks)


def test_file_vector_store_preserves_replace_document_policy(tmp_path: Path) -> None:
    file_path = tmp_path / "vector-store.json"
    ingestion, retrieval = _build_use_cases(file_path)

    first_result = ingestion.execute(REFUND_DOCUMENT)
    second_result = ingestion.execute(
        {
            **REFUND_DOCUMENT,
            "content": (
                "Khach hang co the yeu cau hoan tien trong vong 14 ngay ke tu ngay thanh toan. "
                "Yeu cau hoan tien phai duoc gui qua cong ho tro chinh thuc."
            ),
        }
    )
    result = retrieval.execute(
        {
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        }
    )

    assert first_result.replaced_document is False
    assert second_result.replaced_document is True
    assert result.chunks
    assert any("14 ngay" in chunk.text for chunk in result.chunks)
    assert all("7 ngay" not in chunk.text for chunk in result.chunks)
