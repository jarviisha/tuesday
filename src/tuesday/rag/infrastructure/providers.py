from __future__ import annotations

import re
from hashlib import sha256
from math import sqrt
from typing import Any

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import (
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)

from tuesday.rag.domain.models import LLMGenerationResult

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


class HashEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._to_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._to_embedding(text)

    @staticmethod
    def _to_embedding(text: str) -> list[float]:
        tokens = [
            token
            for token in re.findall(r"\w+", text.lower())
            if token not in STOPWORDS and len(token) > 1
        ]
        if not tokens:
            return []
        return [
            float(int.from_bytes(sha256(token.encode("utf-8")).digest()[:8], byteorder="big"))
            for token in sorted(set(tokens))
        ]


def _dense_vector(text: str, dimension: int) -> list[float]:
    tokens = [
        token
        for token in re.findall(r"\w+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]
    if not tokens:
        return [0.0] * dimension

    vector = [0.0] * dimension
    for token in sorted(set(tokens)):
        digest = sha256(token.encode()).digest()
        bucket = int.from_bytes(digest[:4], byteorder="big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = sqrt(sum(c * c for c in vector))
    if norm == 0:
        return vector
    return [c / norm for c in vector]


class DeterministicDenseEmbeddingProvider(BaseEmbedding):
    """Demo embedding provider — deterministic dense vectors, no API calls.

    Implements both the domain EmbeddingProvider protocol (embed_texts/embed_query)
    and LlamaIndex's BaseEmbedding interface so it can be set as Settings.embed_model.
    """

    dimension: int = 512

    def __init__(self, *, dimension: int = 512, **kwargs: Any) -> None:
        super().__init__(model_name="deterministic-dense", **{"dimension": dimension, **kwargs})

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_dense_vector(text, self.dimension) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return _dense_vector(text, self.dimension)

    # --- LlamaIndex BaseEmbedding abstract methods ---

    def _get_text_embedding(self, text: str) -> list[float]:
        return _dense_vector(text, self.dimension)

    def _get_query_embedding(self, query: str) -> list[float]:
        return _dense_vector(query, self.dimension)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)


def _parse_demo_llm_prompt(prompt: str) -> LLMGenerationResult:
    context_lines = [
        line for line in prompt.splitlines() if line.startswith("[") and "] " in line
    ]
    if not context_lines:
        return LLMGenerationResult(answer="", citations=[])
    first_line = context_lines[0]
    chunk_id, _, text = first_line.partition("] ")
    return LLMGenerationResult(
        answer=f"According to the available context, {text}",
        citations=[chunk_id.lstrip("[")],
    )


class DeterministicLLMProvider(CustomLLM):
    """Demo LLM provider — returns deterministic answer from prompt context, no API calls.

    Implements both the domain LLMProvider protocol (generate_text)
    and LlamaIndex's CustomLLM interface so it can be set as Settings.llm.
    """

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name="deterministic-llm")

    def generate_text(self, prompt: str) -> LLMGenerationResult:
        return _parse_demo_llm_prompt(prompt)

    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        result = _parse_demo_llm_prompt(prompt)
        return CompletionResponse(text=result.answer)

    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        result = _parse_demo_llm_prompt(prompt)

        def gen() -> CompletionResponseGen:
            yield CompletionResponse(text=result.answer, delta=result.answer)

        return gen()

    async def acomplete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        return self.complete(prompt, **kwargs)
