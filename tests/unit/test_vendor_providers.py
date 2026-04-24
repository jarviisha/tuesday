from unittest.mock import MagicMock

import pytest

from tuesday.rag.infrastructure.providers_vendor import (
    LlamaIndexEmbeddingAdapter,
    LlamaIndexLLMAdapter,
    _extract_json_object,
    _parse_generation_result,
)

# ── LlamaIndexEmbeddingAdapter ────────────────────────────────────────────────


def test_embedding_adapter_embed_texts_delegates_to_llama_model() -> None:
    llama_model = MagicMock()
    llama_model.get_text_embedding_batch.return_value = [[1.0, 2.0], [3.0, 4.0]]
    adapter = LlamaIndexEmbeddingAdapter(llama_model)

    result = adapter.embed_texts(["alpha", "beta"])

    assert result == [[1.0, 2.0], [3.0, 4.0]]
    llama_model.get_text_embedding_batch.assert_called_once_with(["alpha", "beta"])


def test_embedding_adapter_embed_query_delegates_to_llama_model() -> None:
    llama_model = MagicMock()
    llama_model.get_query_embedding.return_value = [0.1, 0.2]
    adapter = LlamaIndexEmbeddingAdapter(llama_model)

    result = adapter.embed_query("refund policy")

    assert result == [0.1, 0.2]
    llama_model.get_query_embedding.assert_called_once_with("refund policy")


def test_embedding_adapter_exposes_llama_model_property() -> None:
    llama_model = MagicMock()
    adapter = LlamaIndexEmbeddingAdapter(llama_model)

    assert adapter.llama_model is llama_model


def test_embedding_adapter_propagates_llama_errors() -> None:
    llama_model = MagicMock()
    llama_model.get_text_embedding_batch.side_effect = RuntimeError("API failure")
    adapter = LlamaIndexEmbeddingAdapter(llama_model)

    with pytest.raises(RuntimeError, match="API failure"):
        adapter.embed_texts(["text"])


# ── LlamaIndexLLMAdapter ──────────────────────────────────────────────────────


def test_llm_adapter_generate_text_calls_complete_with_json_instruction() -> None:
    llama_llm = MagicMock()
    llama_llm.complete.return_value = MagicMock(
        text='{"answer":"Use the portal","citations":["chunk-1"]}'
    )
    adapter = LlamaIndexLLMAdapter(llama_llm)

    result = adapter.generate_text("some prompt")

    assert result.answer == "Use the portal"
    assert result.citations == ["chunk-1"]
    called_prompt = llama_llm.complete.call_args[0][0]
    assert "json" in called_prompt.lower() or "JSON" in called_prompt
    assert "some prompt" in called_prompt


def test_llm_adapter_exposes_llama_llm_property() -> None:
    llama_llm = MagicMock()
    adapter = LlamaIndexLLMAdapter(llama_llm)

    assert adapter.llama_llm is llama_llm


def test_llm_adapter_propagates_llama_errors() -> None:
    llama_llm = MagicMock()
    llama_llm.complete.side_effect = RuntimeError("LLM unavailable")
    adapter = LlamaIndexLLMAdapter(llama_llm)

    with pytest.raises(RuntimeError, match="LLM unavailable"):
        adapter.generate_text("prompt")


def test_llm_adapter_empty_citations_is_valid() -> None:
    llama_llm = MagicMock()
    llama_llm.complete.return_value = MagicMock(
        text='{"answer":"No sources needed","citations":[]}'
    )
    adapter = LlamaIndexLLMAdapter(llama_llm)

    result = adapter.generate_text("prompt")

    assert result.answer == "No sources needed"
    assert result.citations == []


# ── JSON parsing helpers ──────────────────────────────────────────────────────


def test_parse_generation_result_parses_valid_json() -> None:
    result = _parse_generation_result('{"answer":"ok","citations":["c-1"]}')

    assert result.answer == "ok"
    assert result.citations == ["c-1"]


def test_parse_generation_result_strips_markdown_fences() -> None:
    raw = "```json\n{\"answer\":\"ok\",\"citations\":[]}\n```"
    result = _parse_generation_result(raw)

    assert result.answer == "ok"


def test_parse_generation_result_raises_for_missing_answer() -> None:
    with pytest.raises(RuntimeError, match="invalid"):
        _parse_generation_result('{"citations":[]}')


def test_extract_json_object_extracts_embedded_json() -> None:
    raw = 'Some preamble text {"answer":"x","citations":[]} trailing text'
    result = _extract_json_object(raw)

    assert result["answer"] == "x"


def test_extract_json_object_raises_for_no_braces() -> None:
    with pytest.raises(RuntimeError, match="invalid"):
        _extract_json_object("no json here at all")
