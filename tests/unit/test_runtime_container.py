import logging

import pytest

from tuesday_rag.config import RuntimeConfig
from tuesday_rag.runtime.container import build_container


def test_build_container_warns_when_pdftotext_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="tuesday_rag.runtime")
    monkeypatch.setattr(
        "tuesday_rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: False),
    )

    container = build_container(RuntimeConfig(pdf_startup_check_mode="warn"))

    assert container.config.pdf_startup_check_mode == "warn"
    assert any(record.msg == "runtime.startup_check_failed" for record in caplog.records)


def test_build_container_fails_strict_when_pdftotext_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tuesday_rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: False),
    )

    with pytest.raises(RuntimeError, match="pdftotext is not available on PATH"):
        build_container(RuntimeConfig(pdf_startup_check_mode="strict"))


def test_build_container_allows_strict_when_pdftotext_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tuesday_rag.infrastructure.file_document_parser.LocalFileDocumentParser.has_pdftotext",
        staticmethod(lambda: True),
    )

    container = build_container(RuntimeConfig(pdf_startup_check_mode="strict"))

    assert container.config.pdf_startup_check_mode == "strict"
