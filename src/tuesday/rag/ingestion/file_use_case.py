from tuesday.rag.domain.models import DocumentIndexResult
from tuesday.rag.domain.ports import DocumentParser
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.runtime.config import RuntimeConfig
from tuesday.shared.validation import enforce_length, require_non_blank, validate_metadata


class FileIngestionUseCase:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        parser: DocumentParser,
        ingestion_use_case: IngestionUseCase,
    ) -> None:
        self._config = config
        self._parser = parser
        self._ingestion_use_case = ingestion_use_case

    def execute(self, payload: dict) -> DocumentIndexResult:
        path = require_non_blank(payload.get("path", ""), "path")
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
        title = payload.get("title")
        if isinstance(title, str):
            title = title.strip() or None
        metadata = validate_metadata(payload.get("metadata"))

        document = self._parser.parse(
            {
                "path": path,
                "document_id": document_id,
                "index_name": index_name,
                "title": title,
                "metadata": metadata,
            }
        )
        return self._ingestion_use_case.index_source_document(
            index_name=index_name,
            document=document,
        )
