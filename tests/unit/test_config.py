import pytest

from tuesday_rag.config import RuntimeConfig


def test_runtime_config_defaults_are_valid() -> None:
    config = RuntimeConfig.from_env()
    config.validate()
    assert config.insufficient_context_answer == (
        "Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn."
    )


def test_runtime_config_reads_env_override_within_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT", "7")
    monkeypatch.setenv("TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER", "Not enough information.")
    monkeypatch.setenv("TUESDAY_RAG_VECTOR_STORE_BACKEND", "file")
    monkeypatch.setenv("TUESDAY_RAG_VECTOR_STORE_FILE_PATH", "/tmp/tuesday-rag.json")
    monkeypatch.setenv("TUESDAY_RAG_INGESTION_CHUNK_COUNT_MAX", "250")
    monkeypatch.setenv("TUESDAY_RAG_PDF_STARTUP_CHECK_MODE", "warn")

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 7
    assert config.insufficient_context_answer == "Not enough information."
    assert config.vector_store_backend == "file"
    assert config.vector_store_file_path == "/tmp/tuesday-rag.json"
    assert config.ingestion_chunk_count_max == 250
    assert config.pdf_startup_check_mode == "warn"


def test_runtime_config_rejects_env_override_outside_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RAG_QUERY_LENGTH_MAX", "3000")

    with pytest.raises(ValueError, match="query_length_max is outside spec bounds"):
        RuntimeConfig.from_env()


def test_runtime_config_reads_values_from_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        (
            "TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT=6\n"
            "TUESDAY_RAG_VECTOR_STORE_BACKEND=file\n"
            "TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/from-dotenv.json\n"
            "TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER=\"Not enough info from dotenv.\"\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 6
    assert config.vector_store_backend == "file"
    assert config.vector_store_file_path == ".tuesday-rag/from-dotenv.json"
    assert config.insufficient_context_answer == "Not enough info from dotenv."


def test_runtime_config_prefers_os_env_over_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT=6\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT", "9")

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 9


def test_runtime_config_rejects_unsupported_vector_store_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_RAG_VECTOR_STORE_BACKEND", "redis")

    with pytest.raises(ValueError, match="vector_store_backend is outside supported values"):
        RuntimeConfig.from_env()


def test_runtime_config_rejects_unsupported_pdf_startup_check_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_RAG_PDF_STARTUP_CHECK_MODE", "always")

    with pytest.raises(ValueError, match="pdf_startup_check_mode is outside supported values"):
        RuntimeConfig.from_env()


def test_runtime_config_requires_openai_generation_model_when_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_RAG_GENERATION_PROVIDER_BACKEND", "openai")
    monkeypatch.setenv("TUESDAY_RAG_OPENAI_API_KEY", "test-key")

    with pytest.raises(
        ValueError,
        match="openai_generation_model is required for the selected provider backend",
    ):
        RuntimeConfig.from_env()


def test_runtime_config_rejects_chunk_count_limit_outside_spec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_RAG_INGESTION_CHUNK_COUNT_MAX", "0")

    with pytest.raises(ValueError, match="ingestion_chunk_count_max is outside spec bounds"):
        RuntimeConfig.from_env()
