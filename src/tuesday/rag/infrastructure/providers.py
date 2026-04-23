import re
from hashlib import sha256
from math import sqrt

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


class DeterministicLLMProvider:
    def generate_text(self, prompt: str) -> LLMGenerationResult:
        context_lines = [
            line
            for line in prompt.splitlines()
            if line.startswith("[") and "] " in line
        ]
        if not context_lines:
            return LLMGenerationResult(answer="", citations=[])
        first_line = context_lines[0]
        chunk_id, _, text = first_line.partition("] ")
        return LLMGenerationResult(
            answer=f"According to the available context, {text}",
            citations=[chunk_id.lstrip("[")],
        )


class DeterministicDenseEmbeddingProvider:
    def __init__(self, *, dimension: int = 512) -> None:
        self._dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._to_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._to_embedding(text)

    def _to_embedding(self, text: str) -> list[float]:
        tokens = [
            token
            for token in re.findall(r"\w+", text.lower())
            if token not in STOPWORDS and len(token) > 1
        ]
        if not tokens:
            return []

        vector = [0.0] * self._dimension
        for token in sorted(set(tokens)):
            digest = sha256(token.encode()).digest()
            bucket = int.from_bytes(digest[:4], byteorder="big") % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = sqrt(sum(component * component for component in vector))
        if norm == 0:
            return vector
        return [component / norm for component in vector]
