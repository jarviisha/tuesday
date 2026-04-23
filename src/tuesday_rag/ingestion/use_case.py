from dataclasses import replace
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
        document_id = self._validate_document_id(payload.get("document_id", ""))
        index_name = self._validate_index_name(payload.get("index_name", ""))
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
        return self.index_source_document(index_name=index_name, document=document)

    def index_source_document(
        self,
        *,
        index_name: str,
        document: SourceDocument,
    ) -> DocumentIndexResult:
        document = self._normalize_document(document)
        if not document.content.strip():
            raise EmptyDocumentError("Document is empty after normalization")
        chunks = self._chunker.chunk(document)
        if not chunks:
            raise ChunkingError("Failed to create any valid chunks")
        if len(chunks) > self._config.ingestion_chunk_count_max:
            raise ChunkingError(
                "Document exceeds the maximum number of chunks for the current config"
            )
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

    def _normalize_document(self, document: SourceDocument) -> SourceDocument:
        normalized_content = document.content.strip()
        if not normalized_content:
            raise EmptyDocumentError("Document is empty after normalization")
        normalized_content = enforce_length(
            normalized_content,
            "content",
            minimum=self._config.content_length_min,
            maximum=self._config.content_length_max,
        )
        if normalized_content == document.content and document.checksum is not None:
            return document
        return replace(
            document,
            content=normalized_content,
            checksum=sha256(normalized_content.encode("utf-8")).hexdigest(),
        )

    @staticmethod
    def _validate_document_id(document_id: str) -> str:
        return enforce_length(
            require_non_blank(document_id, "document_id"),
            "document_id",
            minimum=1,
            maximum=128,
        )

    @staticmethod
    def _validate_index_name(index_name: str) -> str:
        return enforce_length(
            require_non_blank(index_name, "index_name"),
            "index_name",
            minimum=1,
            maximum=64,
        )
