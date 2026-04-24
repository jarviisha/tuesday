from __future__ import annotations

import json

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM

from tuesday.rag.domain.models import LLMGenerationResult

_JSON_INSTRUCTION = (
    "Return only valid JSON with schema "
    '{"answer":"string","citations":["chunk-id"]}. '
    "Do not wrap the JSON in markdown fences. "
    "Citations must contain only chunk_id values that appear in the provided context."
)


class LlamaIndexEmbeddingAdapter:
    """Domain EmbeddingProvider wrapping a LlamaIndex BaseEmbedding."""

    def __init__(self, llama_model: BaseEmbedding) -> None:
        self._llama_model = llama_model

    @property
    def llama_model(self) -> BaseEmbedding:
        return self._llama_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._llama_model.get_text_embedding_batch(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._llama_model.get_query_embedding(text)


class LlamaIndexLLMAdapter:
    """Domain LLMProvider wrapping a LlamaIndex LLM."""

    def __init__(self, llama_llm: LLM) -> None:
        self._llama_llm = llama_llm

    @property
    def llama_llm(self) -> LLM:
        return self._llama_llm

    def generate_text(self, prompt: str) -> LLMGenerationResult:
        full_prompt = f"{_JSON_INSTRUCTION}\n\n{prompt}"
        response = self._llama_llm.complete(full_prompt)
        return _parse_generation_result(response.text)


def build_openai_embedding(config) -> LlamaIndexEmbeddingAdapter:
    from llama_index.embeddings.openai import OpenAIEmbedding

    return LlamaIndexEmbeddingAdapter(
        OpenAIEmbedding(api_key=config.openai_api_key, model=config.openai_embedding_model)
    )


def build_gemini_embedding(config) -> LlamaIndexEmbeddingAdapter:
    from llama_index.embeddings.gemini import GeminiEmbedding

    return LlamaIndexEmbeddingAdapter(
        GeminiEmbedding(api_key=config.gemini_api_key, model_name=config.gemini_embedding_model)
    )


def build_azure_openai_embedding(config) -> LlamaIndexEmbeddingAdapter:
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

    return LlamaIndexEmbeddingAdapter(
        AzureOpenAIEmbedding(
            api_key=config.azure_openai_api_key,
            azure_endpoint=config.azure_openai_endpoint,
            api_version=config.azure_openai_api_version,
            azure_deployment=config.azure_openai_embedding_deployment,
        )
    )


def build_openai_llm(config) -> LlamaIndexLLMAdapter:
    from llama_index.llms.openai import OpenAI

    return LlamaIndexLLMAdapter(
        OpenAI(api_key=config.openai_api_key, model=config.openai_generation_model)
    )


def build_gemini_llm(config) -> LlamaIndexLLMAdapter:
    from llama_index.llms.gemini import Gemini

    return LlamaIndexLLMAdapter(
        Gemini(api_key=config.gemini_api_key, model=config.gemini_generation_model)
    )


def build_azure_openai_llm(config) -> LlamaIndexLLMAdapter:
    from llama_index.llms.azure_openai import AzureOpenAI

    return LlamaIndexLLMAdapter(
        AzureOpenAI(
            api_key=config.azure_openai_api_key,
            azure_endpoint=config.azure_openai_endpoint,
            api_version=config.azure_openai_api_version,
            azure_deployment=config.azure_openai_generation_deployment,
        )
    )


def _parse_generation_result(raw_content: str) -> LLMGenerationResult:
    payload = _extract_json_object(raw_content)
    answer = payload.get("answer")
    citations = payload.get("citations", [])
    if not isinstance(answer, str):
        raise RuntimeError("provider generation output is invalid")
    if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
        raise RuntimeError("provider generation output is invalid")
    return LLMGenerationResult(answer=answer.strip(), citations=citations)


def _extract_json_object(raw_content: str) -> dict:
    stripped = raw_content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end < start:
            raise RuntimeError("provider generation output is invalid") from None
        payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise RuntimeError("provider generation output is invalid")
    return payload
