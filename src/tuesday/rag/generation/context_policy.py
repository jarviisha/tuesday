import re

from tuesday.rag.domain.models import RetrievedChunk

GENERATION_STOPWORDS = {
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
    "lao",
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

DETAIL_SEEKING_PATTERNS = (
    "bao lau",
    "bao nhieu",
    "khi nao",
    "luc nao",
    "muc phi",
    "gia bao nhieu",
)

DETAIL_SIGNAL_TOKENS = {
    "gio",
    "ngay",
    "nam",
    "phut",
    "thang",
    "tuan",
}

MIN_CONTEXT_OVERLAP_RATIO = 0.6


def has_sufficient_context(question: str, used_chunks: list[RetrievedChunk]) -> bool:
    if not used_chunks:
        return False

    question_tokens = _meaningful_tokens(question)
    if not question_tokens:
        return True

    context_text = " ".join(chunk.text for chunk in used_chunks)
    context_tokens = _meaningful_tokens(context_text)
    overlap_tokens = question_tokens.intersection(context_tokens)
    minimum_overlap_tokens = 1 if len(question_tokens) == 1 else 2

    if len(overlap_tokens) < minimum_overlap_tokens:
        return False

    overlap_ratio = len(overlap_tokens) / len(question_tokens)
    if overlap_ratio < MIN_CONTEXT_OVERLAP_RATIO:
        return False

    if _is_detail_seeking_question(question) and not _has_detail_signal(context_text):
        return False

    return True


def _is_detail_seeking_question(question: str) -> bool:
    normalized_question = question.lower()
    return any(pattern in normalized_question for pattern in DETAIL_SEEKING_PATTERNS)


def _has_detail_signal(context_text: str) -> bool:
    lower_text = context_text.lower()
    if re.search(r"\d", lower_text):
        return True
    context_tokens = _meaningful_tokens(context_text)
    return any(token in DETAIL_SIGNAL_TOKENS for token in context_tokens)


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", text.lower())
        if len(token) > 1 and token not in GENERATION_STOPWORDS
    }
