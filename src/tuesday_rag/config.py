import os
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class RuntimeConfig:
    retrieval_top_k_default: int = 5
    retrieval_top_k_min: int = 1
    retrieval_top_k_max: int = 20
    generation_max_context_chunks_default: int = 5
    generation_max_context_chunks_min: int = 1
    generation_max_context_chunks_max: int = 10
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
        "Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn."
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
                raise ValueError(f"{field_name} ngoài biên spec")
        if self.retrieval_top_k_min > self.retrieval_top_k_max:
            raise ValueError("biên retrieval_top_k không hợp lệ")
        if (
            self.generation_max_context_chunks_min
            > self.generation_max_context_chunks_max
        ):
            raise ValueError("biên generation_max_context_chunks không hợp lệ")
        if not (
            self.ingestion_chunk_size_chars_min
            <= self.ingestion_chunk_size_chars_default
            <= self.ingestion_chunk_size_chars_max
        ):
            raise ValueError("ingestion_chunk_size_chars_default ngoài biên spec")
        if not (
            self.ingestion_chunk_overlap_chars_min
            <= self.ingestion_chunk_overlap_chars_default
            <= self.ingestion_chunk_overlap_chars_max
        ):
            raise ValueError("ingestion_chunk_overlap_chars_default ngoài biên spec")
        if (
            self.ingestion_chunk_overlap_chars_default
            >= self.ingestion_chunk_size_chars_default
        ):
            raise ValueError("chunk_overlap phải nhỏ hơn chunk_size")
        if self.content_length_min > self.content_length_max:
            raise ValueError("biên content_length không hợp lệ")
        if self.query_length_min > self.query_length_max:
            raise ValueError("biên query_length không hợp lệ")
        if self.question_length_min > self.question_length_max:
            raise ValueError("biên question_length không hợp lệ")
