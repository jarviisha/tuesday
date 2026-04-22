from hashlib import sha256

from tuesday_rag.config import RuntimeConfig
from tuesday_rag.domain.errors import ChunkingError, EmptyDocumentError
from tuesday_rag.domain.models import DocumentIndexResult, SourceDocument
from tuesday_rag.domain.ports import Chunker
from tuesday_rag.ingestion.service import IndexerService
from tuesday_rag.shared.validation import (
    enforce_length,
    require_non_blank,
    validate_metadata,
    validate_source_type,
)


class IngestionUseCase:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        chunker: Chunker,
        indexer: IndexerService,
    ) -> None:
        self._config = config
        self._chunker = chunker
        self._indexer = indexer

    def execute(self, payload: dict) -> DocumentIndexResult:
        document_id = enforce_length(
            require_non_blank(payload.get("document_id", ""), "document_id"),
            "document_id",
            minimum=1,
            maximum=128,
        )
        index_name = enforce_length(
            require_non_blank(payload.get("index_name", ""), "index_name"),
            "index_name",
            minimum=1,
            maximum=64,
        )
        content = enforce_length(
            require_non_blank(payload.get("content", ""), "content"),
            "content",
            minimum=self._config.content_length_min,
            maximum=self._config.content_length_max,
        )
        source_type = validate_source_type(payload.get("source_type", ""))
        metadata = validate_metadata(payload.get("metadata"))
        document = SourceDocument(
            document_id=document_id,
            title=payload.get("title"),
            content=content,
            source_type=source_type,
            source_uri=payload.get("source_uri"),
            language=metadata.get("language"),
            metadata=metadata,
            checksum=sha256(content.encode("utf-8")).hexdigest(),
        )
        if not document.content.strip():
            raise EmptyDocumentError("Document is empty after normalization")
        chunks = self._chunker.chunk(document)
        if not chunks:
            raise ChunkingError("Failed to create any valid chunks")
        indexed_chunks, replaced_document = self._indexer.index_chunks(
            index_name=index_name,
            document_id=document.document_id,
            chunks=chunks,
        )
        return DocumentIndexResult(
            document_id=document.document_id,
            index_name=index_name,
            chunk_count=len(chunks),
            indexed_count=len(indexed_chunks),
            status="indexed",
            errors=[],
            replaced_document=replaced_document,
        )
