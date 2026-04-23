class DomainError(Exception):
    error_code = "DOMAIN_ERROR"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidInputError(DomainError):
    error_code = "INVALID_INPUT"


class DocumentParseError(DomainError):
    error_code = "DOCUMENT_PARSE_ERROR"


class EmptyDocumentError(DomainError):
    error_code = "EMPTY_DOCUMENT"


class ChunkingError(DomainError):
    error_code = "CHUNKING_ERROR"


class EmbeddingError(DomainError):
    error_code = "EMBEDDING_ERROR"


class IndexWriteError(DomainError):
    error_code = "INDEX_WRITE_ERROR"


class RetrievalError(DomainError):
    error_code = "RETRIEVAL_ERROR"


class UnsupportedFilterError(DomainError):
    error_code = "UNSUPPORTED_FILTER"


class PromptBuildError(DomainError):
    error_code = "PROMPT_BUILD_ERROR"


class GenerationError(DomainError):
    error_code = "GENERATION_ERROR"


class InvalidGenerationOutputError(DomainError):
    error_code = "INVALID_GENERATION_OUTPUT"


class RetrievalRequiredIndexMissingError(DomainError):
    error_code = "RETRIEVAL_REQUIRED_INDEX_MISSING"
