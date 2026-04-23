from tuesday.rag.domain.errors import DomainError
from tuesday.rag.infrastructure.resilience import IntegrationTimeoutError, RetryExhaustedError

APPLICATION_ERROR_CODES = {
    "INVALID_INPUT",
    "UNSUPPORTED_FILTER",
    "DOCUMENT_PARSE_ERROR",
    "EMPTY_DOCUMENT",
    "CHUNKING_ERROR",
    "RETRIEVAL_REQUIRED_INDEX_MISSING",
    "PROMPT_BUILD_ERROR",
    "INVALID_GENERATION_OUTPUT",
}

PROVIDER_ERROR_CODES = {
    "EMBEDDING_ERROR",
    "GENERATION_ERROR",
}

STORAGE_ERROR_CODES = {
    "INDEX_WRITE_ERROR",
    "RETRIEVAL_ERROR",
}


def classify_error_code(error_code: str | None) -> str:
    if error_code in PROVIDER_ERROR_CODES:
        return "provider"
    if error_code in STORAGE_ERROR_CODES:
        return "storage"
    if error_code in APPLICATION_ERROR_CODES:
        return "application"
    return "unknown"


def classify_domain_error(error: DomainError) -> dict[str, int | str | None]:
    failure_group = classify_error_code(error.error_code)
    failure_component = "request_validation"
    if failure_group == "storage":
        failure_component = "vector_store"

    retry_count = 0
    timeout_ms = None
    failure_mode = "handled_error"
    current_error = error.__cause__
    while current_error is not None:
        if isinstance(current_error, RetryExhaustedError):
            failure_component = current_error.component
            retry_count = max(current_error.attempts - 1, 0)
            failure_mode = "retry_exhausted"
        if isinstance(current_error, IntegrationTimeoutError):
            failure_component = current_error.component
            timeout_ms = current_error.timeout_ms
            failure_mode = "timeout"
        current_error = current_error.__cause__

    if failure_component == "request_validation" and error.error_code == "GENERATION_ERROR":
        failure_component = "generation_provider"
    if failure_component == "request_validation" and error.error_code == "EMBEDDING_ERROR":
        failure_component = "embedding_provider"
    if (
        failure_component == "request_validation"
        and error.error_code == "RETRIEVAL_REQUIRED_INDEX_MISSING"
    ):
        failure_component = "generation_request"

    return {
        "failure_group": failure_group,
        "failure_component": failure_component,
        "failure_mode": failure_mode,
        "retry_count": retry_count,
        "timeout_ms": timeout_ms,
    }
