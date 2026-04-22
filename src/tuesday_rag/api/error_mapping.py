from fastapi import status

from tuesday_rag.domain.errors import DomainError

ERROR_STATUS_MAPPING = {
    "INVALID_INPUT": status.HTTP_400_BAD_REQUEST,
    "UNSUPPORTED_FILTER": status.HTTP_400_BAD_REQUEST,
    "DOCUMENT_PARSE_ERROR": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "EMPTY_DOCUMENT": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "CHUNKING_ERROR": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "EMBEDDING_ERROR": status.HTTP_502_BAD_GATEWAY,
    "INDEX_WRITE_ERROR": status.HTTP_502_BAD_GATEWAY,
    "RETRIEVAL_ERROR": status.HTTP_502_BAD_GATEWAY,
    "RETRIEVAL_REQUIRED_INDEX_MISSING": status.HTTP_400_BAD_REQUEST,
    "PROMPT_BUILD_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "GENERATION_ERROR": status.HTTP_502_BAD_GATEWAY,
    "INVALID_GENERATION_OUTPUT": status.HTTP_502_BAD_GATEWAY,
}


def map_domain_error(error: DomainError) -> tuple[int, dict]:
    return ERROR_STATUS_MAPPING.get(error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR), {
        "error_code": error.error_code,
        "message": error.message,
        "details": error.details,
    }
