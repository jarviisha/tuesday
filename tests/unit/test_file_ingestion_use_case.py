from pathlib import Path

import pytest

from tuesday_rag.config import RuntimeConfig
from tuesday_rag.domain.errors import EmptyDocumentError, InvalidInputError
from tuesday_rag.infrastructure.chunking import CharacterChunker
from tuesday_rag.infrastructure.file_document_parser import LocalFileDocumentParser
from tuesday_rag.infrastructure.providers import HashEmbeddingProvider
from tuesday_rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday_rag.ingestion.file_use_case import FileIngestionUseCase
from tuesday_rag.ingestion.service import IndexerService
from tuesday_rag.ingestion.use_case import IngestionUseCase


def _build_file_ingestion_use_case() -> FileIngestionUseCase:
    config = RuntimeConfig()
    ingestion_use_case = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(HashEmbeddingProvider(), InMemoryVectorStore()),
    )
    return FileIngestionUseCase(
        config=config,
        parser=LocalFileDocumentParser(),
        ingestion_use_case=ingestion_use_case,
    )


def test_file_ingestion_indexes_supported_file(tmp_path: Path) -> None:
    file_path = tmp_path / "refund.md"
    file_path.write_text("Refunds are available within 7 days.", encoding="utf-8")

    result = _build_file_ingestion_use_case().execute(
        {
            "path": str(file_path),
            "document_id": "doc-refund-file",
            "index_name": "enterprise-kb",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )

    assert result.status == "indexed"
    assert result.replaced_document is False
    assert result.indexed_count == result.chunk_count


def test_file_ingestion_raises_empty_document_for_blank_file(tmp_path: Path) -> None:
    file_path = tmp_path / "blank.txt"
    file_path.write_text("   \n\t", encoding="utf-8")

    with pytest.raises(EmptyDocumentError):
        _build_file_ingestion_use_case().execute(
            {
                "path": str(file_path),
                "document_id": "doc-blank-file",
                "index_name": "enterprise-kb",
            }
        )


def test_file_ingestion_rejects_unsupported_extension(tmp_path: Path) -> None:
    file_path = tmp_path / "refund.docx"
    file_path.write_text("Refunds are available within 7 days.", encoding="utf-8")

    with pytest.raises(InvalidInputError) as exc_info:
        _build_file_ingestion_use_case().execute(
            {
                "path": str(file_path),
                "document_id": "doc-refund-file",
                "index_name": "enterprise-kb",
            }
        )

    assert exc_info.value.details == {"field": "path"}


def test_file_ingestion_preserves_reindex_semantics(tmp_path: Path) -> None:
    file_path = tmp_path / "refund.txt"
    file_path.write_text("Refunds are available within 7 days.", encoding="utf-8")
    use_case = _build_file_ingestion_use_case()

    first_result = use_case.execute(
        {
            "path": str(file_path),
            "document_id": "doc-refund-file",
            "index_name": "enterprise-kb",
        }
    )
    second_result = use_case.execute(
        {
            "path": str(file_path),
            "document_id": "doc-refund-file",
            "index_name": "enterprise-kb",
        }
    )

    assert first_result.replaced_document is False
    assert second_result.replaced_document is True
