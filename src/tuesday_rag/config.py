import os
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class RuntimeConfig:
    vector_store_backend: str = "memory"
    vector_store_file_path: str = ".tuesday-rag/vector_store.json"
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
    content_length_min: int = 1
    content_length_max: int = 100000
    query_length_min: int = 1
    query_length_max: int = 2000
    question_length_min: int = 1
    question_length_max: int = 2000
    insufficient_context_answer: str = (
        "There is not enough information in the available context to answer confidently."
    )

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        values: dict[str, int | str] = {}
        for config_field in fields(cls):
            env_name = f"TUESDAY_RAG_{config_field.name.upper()}"
            raw_value = os.getenv(env_name)
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
