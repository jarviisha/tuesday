import re

from tuesday_rag.domain.errors import (
    GenerationError,
    InvalidGenerationOutputError,
    PromptBuildError,
)
from tuesday_rag.domain.models import GeneratedAnswer, GenerationRequest
from tuesday_rag.domain.ports import LLMProvider
from tuesday_rag.generation.prompt_builder import build_grounded_prompt

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


class GeneratorService:
    def __init__(self, llm_provider: LLMProvider, insufficient_context_answer: str) -> None:
        self._llm_provider = llm_provider
        self._insufficient_context_answer = insufficient_context_answer

    def generate(self, request: GenerationRequest) -> GeneratedAnswer:
        retrieved_chunks = request.retrieved_chunks or []
        max_context_chunks = request.max_context_chunks or len(retrieved_chunks)
        used_chunks = list(retrieved_chunks[:max_context_chunks])
        if not used_chunks:
            return GeneratedAnswer(
                answer=self._insufficient_context_answer,
                citations=[],
                grounded=False,
                insufficient_context=True,
                used_chunks=[],
            )
        if not self._has_sufficient_context(request.question, used_chunks):
            return GeneratedAnswer(
                answer=self._insufficient_context_answer,
                citations=[],
                grounded=False,
                insufficient_context=True,
                used_chunks=used_chunks,
            )

        try:
            prompt = build_grounded_prompt(request.question, used_chunks)
        except Exception as exc:
            raise PromptBuildError("Failed to build a valid prompt") from exc
        try:
            generation_result = self._llm_provider.generate_text(prompt)
        except Exception as exc:
            raise GenerationError("Failed to generate an answer from the LLM provider") from exc
        answer = generation_result.answer.strip()
        if not answer:
            raise InvalidGenerationOutputError("answer is invalid")
        valid_chunk_ids = {chunk.chunk_id for chunk in used_chunks}
        citations = generation_result.citations
        if not all(citation in valid_chunk_ids for citation in citations):
            raise InvalidGenerationOutputError("citation is invalid")
        return GeneratedAnswer(
            answer=answer,
            citations=citations,
            grounded=True,
            insufficient_context=False,
            used_chunks=used_chunks,
        )

    @staticmethod
    def _has_sufficient_context(question: str, used_chunks: list) -> bool:
        question_tokens = GeneratorService._meaningful_tokens(question)
        if not question_tokens:
            return bool(used_chunks)
        context_tokens = GeneratorService._meaningful_tokens(
            " ".join(chunk.text for chunk in used_chunks)
        )
        covered_tokens = question_tokens.intersection(context_tokens)
        return (len(covered_tokens) / len(question_tokens)) >= 0.6

    @staticmethod
    def _meaningful_tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"\w+", text.lower())
            if len(token) > 1 and token not in GENERATION_STOPWORDS
        }
