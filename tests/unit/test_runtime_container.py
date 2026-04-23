import logging

import pytest

from tuesday.rag.infrastructure.providers import DeterministicDenseEmbeddingProvider
from tuesday.rag.infrastructure.qdrant_vector_store import QdrantVectorStore
from tuesday.runtime.config import RuntimeConfig
from tuesday.runtime.container import build_container


def test_build_container_warns_when_pdftotext_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="tuesday.runtime")
    monkeypatch.setattr(
        "tuesday.rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: False),
    )

    container = build_container(RuntimeConfig(pdf_startup_check_mode="warn"))

    assert container.config.pdf_startup_check_mode == "warn"
    assert any(record.msg == "runtime.startup_check_failed" for record in caplog.records)


def test_build_container_fails_strict_when_pdftotext_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tuesday.rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: False),
    )

    with pytest.raises(RuntimeError, match="pdftotext is not available on PATH"):
        build_container(RuntimeConfig(pdf_startup_check_mode="strict"))


def test_build_container_allows_strict_when_pdftotext_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tuesday.rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: True),
    )

    container = build_container(RuntimeConfig(pdf_startup_check_mode="strict"))

    assert container.config.pdf_startup_check_mode == "strict"


def test_build_container_uses_qdrant_and_dense_demo_embedding_for_qdrant_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tuesday.rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: True),
    )
    config = RuntimeConfig(
        vector_store_backend="qdrant",
        qdrant_location=":memory:",
        qdrant_collection_prefix="runtime-test",
        qdrant_dense_vector_size=512,
        embedding_provider_backend="demo",
    )

    container = build_container(config)

    assert isinstance(container.vector_store._store, QdrantVectorStore)
    assert isinstance(container.embedding_provider._provider, DeterministicDenseEmbeddingProvider)
