import pytest

from tuesday_rag.config import RuntimeConfig


def test_runtime_config_defaults_are_valid() -> None:
    config = RuntimeConfig.from_env()
    config.validate()


def test_runtime_config_reads_env_override_within_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT", "7")
    monkeypatch.setenv("TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER", "Không đủ dữ liệu.")

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 7
    assert config.insufficient_context_answer == "Không đủ dữ liệu."


def test_runtime_config_rejects_env_override_outside_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RAG_QUERY_LENGTH_MAX", "3000")

    with pytest.raises(ValueError, match="query_length_max ngoài biên spec"):
        RuntimeConfig.from_env()
