import pytest

from tuesday.runtime.config import RuntimeConfig


def test_runtime_config_defaults_are_valid() -> None:
    config = RuntimeConfig.from_env()
    config.validate()
    assert config.vector_store_file_path == ".tuesday/vector_store.json"
    assert config.insufficient_context_answer == (
        "Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn."
    )


def test_runtime_config_reads_env_override_within_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_RETRIEVAL_TOP_K_DEFAULT", "7")
    monkeypatch.setenv("TUESDAY_INSUFFICIENT_CONTEXT_ANSWER", "Not enough information.")
    monkeypatch.setenv("TUESDAY_VECTOR_STORE_BACKEND", "file")
    monkeypatch.setenv("TUESDAY_VECTOR_STORE_FILE_PATH", "/tmp/tuesday.json")
    monkeypatch.setenv("TUESDAY_INGESTION_CHUNK_COUNT_MAX", "250")
    monkeypatch.setenv("TUESDAY_PDF_STARTUP_CHECK_MODE", "warn")

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 7
    assert config.insufficient_context_answer == "Not enough information."
    assert config.vector_store_backend == "file"
    assert config.vector_store_file_path == "/tmp/tuesday.json"
    assert config.ingestion_chunk_count_max == 250
    assert config.pdf_startup_check_mode == "warn"


def test_runtime_config_accepts_qdrant_backend_with_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_VECTOR_STORE_BACKEND", "qdrant")
    monkeypatch.setenv("TUESDAY_QDRANT_LOCATION", ":memory:")
    monkeypatch.setenv("TUESDAY_QDRANT_COLLECTION_PREFIX", "kb")
    monkeypatch.setenv("TUESDAY_QDRANT_DENSE_VECTOR_SIZE", "256")

    config = RuntimeConfig.from_env()

    assert config.vector_store_backend == "qdrant"
    assert config.qdrant_location == ":memory:"
    assert config.qdrant_collection_prefix == "kb"
    assert config.qdrant_dense_vector_size == 256


def test_runtime_config_rejects_env_override_outside_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUESDAY_QUERY_LENGTH_MAX", "3000")

    with pytest.raises(ValueError, match="query_length_max is outside spec bounds"):
        RuntimeConfig.from_env()


def test_runtime_config_reads_values_from_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        (
            "TUESDAY_RETRIEVAL_TOP_K_DEFAULT=6\n"
            "TUESDAY_VECTOR_STORE_BACKEND=file\n"
            "TUESDAY_VECTOR_STORE_FILE_PATH=.tuesday/from-dotenv.json\n"
            "TUESDAY_INSUFFICIENT_CONTEXT_ANSWER=\"Not enough info from dotenv.\"\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 6
    assert config.vector_store_backend == "file"
    assert config.vector_store_file_path == ".tuesday/from-dotenv.json"
    assert config.insufficient_context_answer == "Not enough info from dotenv."


def test_runtime_config_prefers_os_env_over_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "TUESDAY_RETRIEVAL_TOP_K_DEFAULT=6\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TUESDAY_RETRIEVAL_TOP_K_DEFAULT", "9")

    config = RuntimeConfig.from_env()

    assert config.retrieval_top_k_default == 9


def test_runtime_config_rejects_unsupported_vector_store_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_VECTOR_STORE_BACKEND", "redis")

    with pytest.raises(ValueError, match="vector_store_backend is outside supported values"):
        RuntimeConfig.from_env()


def test_runtime_config_requires_qdrant_location_or_url_when_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_VECTOR_STORE_BACKEND", "qdrant")

    with pytest.raises(
        ValueError,
        match="qdrant_url or qdrant_location is required for the selected vector store backend",
    ):
        RuntimeConfig.from_env()


def test_runtime_config_rejects_unsupported_pdf_startup_check_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_PDF_STARTUP_CHECK_MODE", "always")

    with pytest.raises(ValueError, match="pdf_startup_check_mode is outside supported values"):
        RuntimeConfig.from_env()


def test_runtime_config_requires_openai_generation_model_when_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_GENERATION_PROVIDER_BACKEND", "openai")
    monkeypatch.setenv("TUESDAY_OPENAI_API_KEY", "test-key")

    with pytest.raises(
        ValueError,
        match="openai_generation_model is required for the selected provider backend",
    ):
        RuntimeConfig.from_env()


def test_runtime_config_rejects_chunk_count_limit_outside_spec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUESDAY_INGESTION_CHUNK_COUNT_MAX", "0")

    with pytest.raises(ValueError, match="ingestion_chunk_count_max is outside spec bounds"):
        RuntimeConfig.from_env()
