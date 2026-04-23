import re

from tuesday.rag.domain.models import RetrievedChunk

RETRIEVAL_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "bao",
    "cho",
    "co",
    "cua",
    "do",
    "duoc",
    "for",
    "from",
    "gi",
    "how",
    "in",
    "is",
    "khi",
    "la",
    "lau",
    "nhieu",
    "o",
    "of",
    "the",
    "to",
    "trong",
    "ve",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def rerank_chunks(query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    query_tokens = _meaningful_tokens(query)
    if not query_tokens:
        return sorted(chunks, key=lambda chunk: chunk.score, reverse=True)

    ranked_chunks = [
        (
            chunk,
            overlap_count,
            overlap_count / len(query_tokens),
        )
        for chunk in chunks
        for overlap_count in [len(query_tokens.intersection(_meaningful_tokens(chunk.text)))]
    ]

    if any(overlap_count > 0 for _, overlap_count, _ in ranked_chunks):
        ranked_chunks = [
            item for item in ranked_chunks if item[1] > 0
        ]

    ranked_chunks.sort(
        key=lambda item: (item[1], item[2], item[0].score),
        reverse=True,
    )
    return [chunk for chunk, _, _ in ranked_chunks]


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", text.lower())
        if len(token) > 1 and token not in RETRIEVAL_STOPWORDS
    }
