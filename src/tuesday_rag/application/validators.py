from tuesday_rag.config import RuntimeConfig
from tuesday_rag.domain.errors import InvalidInputError, UnsupportedFilterError

ALLOWED_SOURCE_TYPES = {"text", "pdf", "html"}
ALLOWED_FILTERS = {"document_id", "source_type", "language", "tags"}


def require_non_blank(value: str, field_name: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise InvalidInputError(f"{field_name} không được để trống", details={"field": field_name})
    return trimmed


def enforce_length(value: str, field_name: str, *, minimum: int, maximum: int) -> str:
    if not (minimum <= len(value) <= maximum):
        raise InvalidInputError(
            f"{field_name} phải có độ dài trong khoảng {minimum}..{maximum}",
            details={"field": field_name},
        )
    return value


def validate_source_type(source_type: str) -> str:
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise InvalidInputError("source_type không hợp lệ", details={"field": "source_type"})
    return source_type


def validate_metadata(metadata: dict | None) -> dict:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise InvalidInputError("metadata phải là object hợp lệ", details={"field": "metadata"})

    language = metadata.get("language")
    if language is not None:
        if not isinstance(language, str) or not language.strip():
            raise InvalidInputError(
                "metadata.language không hợp lệ",
                details={"field": "metadata.language"},
            )

    tags = metadata.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not tags:
            raise InvalidInputError(
                "metadata.tags phải là danh sách string không rỗng",
                details={"field": "metadata.tags"},
            )
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise InvalidInputError(
                "metadata.tags phải là danh sách string không rỗng",
                details={"field": "metadata.tags"},
            )

    return metadata


def validate_filters(filters: dict | None) -> dict:
    if not filters:
        return {}
    if not isinstance(filters, dict):
        raise InvalidInputError("filters phải là object hợp lệ", details={"field": "filters"})
    unknown_keys = [key for key in filters if key not in ALLOWED_FILTERS]
    if unknown_keys:
        raise UnsupportedFilterError(
            "filter không được hỗ trợ",
            details={"unsupported_filters": unknown_keys},
        )
    if "tags" in filters:
        tags = filters["tags"]
        if not isinstance(tags, list) or not tags:
            raise InvalidInputError(
                "filters.tags phải là danh sách string không rỗng",
                details={"field": "filters.tags"},
            )
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise InvalidInputError(
                "filters.tags phải là danh sách string không rỗng",
                details={"field": "filters.tags"},
            )
    for key in ("document_id", "source_type", "language"):
        if key in filters and (not isinstance(filters[key], str) or not filters[key].strip()):
            raise InvalidInputError(
                f"filters.{key} không hợp lệ",
                details={"field": f"filters.{key}"},
            )
    return filters


def validate_top_k(top_k: int, config: RuntimeConfig) -> int:
    if not (config.retrieval_top_k_min <= top_k <= config.retrieval_top_k_max):
        raise InvalidInputError(
            "top_k không hợp lệ",
            details={"field": "top_k"},
        )
    return top_k


def validate_max_context_chunks(value: int, config: RuntimeConfig) -> int:
    if not (
        config.generation_max_context_chunks_min
        <= value
        <= config.generation_max_context_chunks_max
    ):
        raise InvalidInputError(
            "max_context_chunks không hợp lệ",
            details={"field": "max_context_chunks"},
        )
    return value
