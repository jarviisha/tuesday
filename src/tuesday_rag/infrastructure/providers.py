import re
from hashlib import sha256

from tuesday_rag.domain.models import LLMGenerationResult

STOPWORDS = {
    "va",
    "và",
    "co",
    "có",
    "cho",
    "trong",
    "theo",
    "la",
    "là",
    "duoc",
    "được",
    "khong",
    "không",
    "cần",
    "gi",
    "gì",
    "bao",
    "lâu",
    "bao_lâu",
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
            answer=f"Theo ngữ cảnh hiện có, {text}",
            citations=[chunk_id.lstrip("[")],
        )
