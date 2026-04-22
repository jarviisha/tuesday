import pytest

from tuesday_rag.config import RuntimeConfig


def test_runtime_config_defaults_are_valid() -> None:
    config = RuntimeConfig.from_env()
    config.validate()


def test_runtime_config_reads_env_override_within_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT", "7")
    monkeypatch.setenv("TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER", "Not enough information.")
    monkeypatch.setenv("TUESDAY_RAG_VECTOR_STORE_BACKEND", "file")
    monkeypatch.setenv("TUESDAY_RAG_VECTOR_STORE_FILE_PATH", "/tmp/tuesday-rag.json")

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 7
    assert config.insufficient_context_answer == "Not enough information."
    assert config.vector_store_backend == "file"
    assert config.vector_store_file_path == "/tmp/tuesday-rag.json"


def test_runtime_config_rejects_env_override_outside_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RAG_QUERY_LENGTH_MAX", "3000")

    with pytest.raises(ValueError, match="query_length_max is outside spec bounds"):
        RuntimeConfig.from_env()


def test_runtime_config_rejects_unsupported_vector_store_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_RAG_VECTOR_STORE_BACKEND", "redis")

    with pytest.raises(ValueError, match="vector_store_backend is outside supported values"):
        RuntimeConfig.from_env()
