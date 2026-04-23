import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import TypedDict


class RuntimeConfigOverrides(TypedDict, total=False):
    vector_store_backend: str
    vector_store_file_path: str
    pdf_startup_check_mode: str
    embedding_provider_backend: str
    generation_provider_backend: str
    openai_api_key: str
    openai_base_url: str
    openai_embedding_model: str
    openai_generation_model: str
    gemini_api_key: str
    gemini_base_url: str
    gemini_embedding_model: str
    gemini_generation_model: str
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str
    azure_openai_embedding_deployment: str
    azure_openai_generation_deployment: str
    retrieval_top_k_default: int
    retrieval_top_k_min: int
    retrieval_top_k_max: int
    generation_max_context_chunks_default: int
    generation_max_context_chunks_min: int
    generation_max_context_chunks_max: int
    embedding_timeout_ms: int
    embedding_max_retries: int
    generation_timeout_ms: int
    generation_max_retries: int
    vector_store_timeout_ms: int
    vector_store_max_retries: int
    ingestion_chunk_size_chars_default: int
    ingestion_chunk_size_chars_min: int
    ingestion_chunk_size_chars_max: int
    ingestion_chunk_overlap_chars_default: int
    ingestion_chunk_overlap_chars_min: int
    ingestion_chunk_overlap_chars_max: int
    ingestion_chunk_count_max: int
    content_length_min: int
    content_length_max: int
    query_length_min: int
    query_length_max: int
    question_length_min: int
    question_length_max: int
    insufficient_context_answer: str


@dataclass(frozen=True)
class RuntimeConfig:
    vector_store_backend: str = "memory"
    vector_store_file_path: str = ".tuesday-rag/vector_store.json"
    pdf_startup_check_mode: str = "off"
    embedding_provider_backend: str = "demo"
    generation_provider_backend: str = "demo"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_embedding_model: str | None = None
    openai_generation_model: str | None = None
    gemini_api_key: str | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_embedding_model: str | None = None
    gemini_generation_model: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_embedding_deployment: str | None = None
    azure_openai_generation_deployment: str | None = None
    retrieval_top_k_default: int = 5
    retrieval_top_k_min: int = 1
    retrieval_top_k_max: int = 20
    generation_max_context_chunks_default: int = 5
    generation_max_context_chunks_min: int = 1
    generation_max_context_chunks_max: int = 10
    embedding_timeout_ms: int = 1000
    embedding_max_retries: int = 0
    generation_timeout_ms: int = 1000
    generation_max_retries: int = 0
    vector_store_timeout_ms: int = 1000
    vector_store_max_retries: int = 0
    ingestion_chunk_size_chars_default: int = 1000
    ingestion_chunk_size_chars_min: int = 300
    ingestion_chunk_size_chars_max: int = 2000
    ingestion_chunk_overlap_chars_default: int = 150
    ingestion_chunk_overlap_chars_min: int = 0
    ingestion_chunk_overlap_chars_max: int = 300
    ingestion_chunk_count_max: int = 200
    content_length_min: int = 1
    content_length_max: int = 100000
    query_length_min: int = 1
    query_length_max: int = 2000
    question_length_min: int = 1
    question_length_max: int = 2000
    insufficient_context_answer: str = (
        "Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn."
    )

    @classmethod
    def from_env(cls, *, env_file_path: str | None = None) -> "RuntimeConfig":
        values: RuntimeConfigOverrides = {}
        dotenv_values = _read_dotenv(env_file_path or ".env")
        for config_field in fields(cls):
            env_name = f"TUESDAY_RAG_{config_field.name.upper()}"
            raw_value = os.getenv(env_name, dotenv_values.get(env_name))
            if raw_value is None:
                continue
            if config_field.type is int:
                values[config_field.name] = int(raw_value)
            else:
                values[config_field.name] = raw_value
        config = cls(**values)
        config.validate()
        return config

    def validate(self) -> None:
        integer_bounds = [
            (
                "retrieval_top_k_default",
                self.retrieval_top_k_default,
                self.retrieval_top_k_min,
                self.retrieval_top_k_max,
            ),
            (
                "generation_max_context_chunks_default",
                self.generation_max_context_chunks_default,
                self.generation_max_context_chunks_min,
                self.generation_max_context_chunks_max,
            ),
            (
                "ingestion_chunk_size_chars_default",
                self.ingestion_chunk_size_chars_default,
                self.ingestion_chunk_size_chars_min,
                self.ingestion_chunk_size_chars_max,
            ),
            (
                "ingestion_chunk_overlap_chars_default",
                self.ingestion_chunk_overlap_chars_default,
                self.ingestion_chunk_overlap_chars_min,
                self.ingestion_chunk_overlap_chars_max,
            ),
            (
                "ingestion_chunk_count_max",
                self.ingestion_chunk_count_max,
                1,
                5000,
            ),
            (
                "embedding_timeout_ms",
                self.embedding_timeout_ms,
                1,
                60000,
            ),
            (
                "embedding_max_retries",
                self.embedding_max_retries,
                0,
                5,
            ),
            (
                "generation_timeout_ms",
                self.generation_timeout_ms,
                1,
                60000,
            ),
            (
                "generation_max_retries",
                self.generation_max_retries,
                0,
                5,
            ),
            (
                "vector_store_timeout_ms",
                self.vector_store_timeout_ms,
                1,
                60000,
            ),
            (
                "vector_store_max_retries",
                self.vector_store_max_retries,
                0,
                5,
            ),
            (
                "content_length_max",
                self.content_length_max,
                self.content_length_min,
                100000,
            ),
            (
                "query_length_max",
                self.query_length_max,
                self.query_length_min,
                2000,
            ),
            (
                "question_length_max",
                self.question_length_max,
                self.question_length_min,
                2000,
            ),
        ]
        for field_name, value, minimum, maximum in integer_bounds:
            if not (minimum <= value <= maximum):
                raise ValueError(f"{field_name} is outside spec bounds")
        if self.vector_store_backend not in {"memory", "file"}:
            raise ValueError("vector_store_backend is outside supported values")
        if self.pdf_startup_check_mode not in {"off", "warn", "strict"}:
            raise ValueError("pdf_startup_check_mode is outside supported values")
        if self.embedding_provider_backend not in {"demo", "openai", "gemini", "azure_openai"}:
            raise ValueError("embedding_provider_backend is outside supported values")
        if self.generation_provider_backend not in {"demo", "openai", "gemini", "azure_openai"}:
            raise ValueError("generation_provider_backend is outside supported values")
        self._validate_provider_settings()
        if self.retrieval_top_k_min > self.retrieval_top_k_max:
            raise ValueError("retrieval_top_k bounds are invalid")
        if (
            self.generation_max_context_chunks_min
            > self.generation_max_context_chunks_max
        ):
            raise ValueError("generation_max_context_chunks bounds are invalid")
        if not (
            self.ingestion_chunk_size_chars_min
            <= self.ingestion_chunk_size_chars_default
            <= self.ingestion_chunk_size_chars_max
        ):
            raise ValueError("ingestion_chunk_size_chars_default is outside spec bounds")
        if not (
            self.ingestion_chunk_overlap_chars_min
            <= self.ingestion_chunk_overlap_chars_default
            <= self.ingestion_chunk_overlap_chars_max
        ):
            raise ValueError("ingestion_chunk_overlap_chars_default is outside spec bounds")
        if (
            self.ingestion_chunk_overlap_chars_default
            >= self.ingestion_chunk_size_chars_default
        ):
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.content_length_min > self.content_length_max:
            raise ValueError("content_length bounds are invalid")
        if self.query_length_min > self.query_length_max:
            raise ValueError("query_length bounds are invalid")
        if self.question_length_min > self.question_length_max:
            raise ValueError("question_length bounds are invalid")

    def _validate_provider_settings(self) -> None:
        if self.embedding_provider_backend == "openai":
            _require_config(self.openai_api_key, "openai_api_key")
            _require_config(self.openai_embedding_model, "openai_embedding_model")
        if self.generation_provider_backend == "openai":
            _require_config(self.openai_api_key, "openai_api_key")
            _require_config(self.openai_generation_model, "openai_generation_model")
        if self.embedding_provider_backend == "gemini":
            _require_config(self.gemini_api_key, "gemini_api_key")
            _require_config(self.gemini_embedding_model, "gemini_embedding_model")
        if self.generation_provider_backend == "gemini":
            _require_config(self.gemini_api_key, "gemini_api_key")
            _require_config(self.gemini_generation_model, "gemini_generation_model")
        if self.embedding_provider_backend == "azure_openai":
            _require_config(self.azure_openai_api_key, "azure_openai_api_key")
            _require_config(self.azure_openai_endpoint, "azure_openai_endpoint")
            _require_config(
                self.azure_openai_embedding_deployment,
                "azure_openai_embedding_deployment",
            )
        if self.generation_provider_backend == "azure_openai":
            _require_config(self.azure_openai_api_key, "azure_openai_api_key")
            _require_config(self.azure_openai_endpoint, "azure_openai_endpoint")
            _require_config(
                self.azure_openai_generation_deployment,
                "azure_openai_generation_deployment",
            )


def _require_config(value: str | None, field_name: str) -> None:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} is required for the selected provider backend")


def _read_dotenv(env_file_path: str) -> dict[str, str]:
    path = Path(env_file_path)
    if not path.exists() or not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values
