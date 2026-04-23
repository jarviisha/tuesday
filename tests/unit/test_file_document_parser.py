import shutil
import subprocess
from pathlib import Path

import pytest

from tuesday_rag.domain.errors import DocumentParseError, InvalidInputError
from tuesday_rag.infrastructure.file_document_parser import LocalFileDocumentParser


@pytest.mark.parametrize("extension", [".txt", ".md"])
def test_file_document_parser_supports_text_and_markdown_files(
    tmp_path: Path,
    extension: str,
) -> None:
    file_path = tmp_path / f"refund{extension}"
    file_path.write_text("Refunds are available within 7 days.", encoding="utf-8")

    document = LocalFileDocumentParser().parse(
        {
            "path": str(file_path),
            "document_id": "doc-refund-file",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )

    assert document.document_id == "doc-refund-file"
    assert document.title == "refund"
    assert document.content == "Refunds are available within 7 days."
    assert document.source_type == "text"
    assert document.source_uri == file_path.resolve().as_uri()
    assert document.language == "en"
    assert document.metadata == {"language": "en", "tags": ["refund"]}


def test_file_document_parser_supports_html_and_extracts_title_and_text(tmp_path: Path) -> None:
    file_path = tmp_path / "refund.html"
    file_path.write_text(
        (
            "<html><head><title>Refund policy</title><style>.hidden{display:none;}</style></head>"
            "<body><h1>Refund policy</h1><p>Customers can request a refund within 7 days.</p>"
            "<script>window.alert('ignore');</script></body></html>"
        ),
        encoding="utf-8",
    )

    document = LocalFileDocumentParser().parse(
        {
            "path": str(file_path),
            "document_id": "doc-refund-file",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )

    assert document.document_id == "doc-refund-file"
    assert document.title == "Refund policy"
    assert document.source_type == "html"
    assert document.source_uri == file_path.resolve().as_uri()
    assert "Customers can request a refund within 7 days." in document.content
    assert "window.alert" not in document.content
    assert "display:none" not in document.content


def test_file_document_parser_supports_pdf(tmp_path: Path) -> None:
    if shutil.which("ps2pdf") is None or shutil.which("pdftotext") is None:
        pytest.skip("pdf tools are not available")

    pdf_path = _build_simple_pdf(
        tmp_path,
        "refund-policy.pdf",
        [
            "Customers can request a refund within 7 days.",
            "Refund policy",
        ],
    )

    document = LocalFileDocumentParser().parse(
        {
            "path": str(pdf_path),
            "document_id": "doc-refund-pdf",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )

    assert document.document_id == "doc-refund-pdf"
    assert document.title == "refund-policy"
    assert document.source_type == "pdf"
    assert document.source_uri == pdf_path.resolve().as_uri()
    assert "Customers can request a refund within 7 days." in document.content


def test_file_document_parser_rejects_unsupported_extension(tmp_path: Path) -> None:
    file_path = tmp_path / "refund.docx"
    file_path.write_text("unsupported", encoding="utf-8")

    with pytest.raises(InvalidInputError) as exc_info:
        LocalFileDocumentParser().parse(
            {
                "path": str(file_path),
                "document_id": "doc-refund-file",
            }
        )

    assert exc_info.value.details == {"field": "path"}


def test_file_document_parser_rejects_missing_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.md"

    with pytest.raises(InvalidInputError) as exc_info:
        LocalFileDocumentParser().parse(
            {
                "path": str(missing_path),
                "document_id": "doc-refund-file",
            }
        )

    assert exc_info.value.details == {"field": "path"}


def test_file_document_parser_rejects_directory_path(tmp_path: Path) -> None:
    directory_path = tmp_path / "docs"
    directory_path.mkdir()

    with pytest.raises(InvalidInputError) as exc_info:
        LocalFileDocumentParser().parse(
            {
                "path": str(directory_path),
                "document_id": "doc-refund-file",
            }
        )

    assert exc_info.value.details == {"field": "path"}


def test_file_document_parser_raises_parse_error_for_invalid_utf8(tmp_path: Path) -> None:
    file_path = tmp_path / "broken.txt"
    file_path.write_bytes(b"\xff\xfe\x00\x00")

    with pytest.raises(DocumentParseError):
        LocalFileDocumentParser().parse(
            {
                "path": str(file_path),
                "document_id": "doc-broken-file",
            }
        )


def _build_simple_pdf(tmp_path: Path, filename: str, lines: list[str]) -> Path:
    ps_path = tmp_path / f"{filename}.ps"
    pdf_path = tmp_path / filename
    ps_lines = ["%!PS-Adobe-3.0", "/Times-Roman findfont 12 scalefont setfont"]
    y = 720
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ps_lines.append(f"72 {y} moveto")
        ps_lines.append(f"({escaped}) show")
        y -= 20
    ps_lines.append("showpage")
    ps_path.write_text("\n".join(ps_lines) + "\n", encoding="utf-8")
    subprocess.run(
        ["ps2pdf", str(ps_path), str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return pdf_path
