import shutil
import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_index_file_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "index_file.py"
    spec = spec_from_file_location("index_file", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_index_file_script_indexes_supported_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "refund.md"
    file_path.write_text("Customers can request a refund within 7 days.", encoding="utf-8")

    index_file = _load_index_file_module()
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_file.py",
            "--path",
            str(file_path),
            "--document-id",
            "doc-refund-file",
            "--index-name",
            "enterprise-kb",
            "--language",
            "en",
            "--tag",
            "refund",
        ],
    )

    exit_code = index_file.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "indexed"' in captured.out
    assert captured.err == ""


def test_index_file_script_indexes_html_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "refund.html"
    file_path.write_text(
        (
            "<html><head><title>Refund policy</title></head>"
            "<body><p>Customers can request a refund within 7 days.</p></body></html>"
        ),
        encoding="utf-8",
    )

    index_file = _load_index_file_module()
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_file.py",
            "--path",
            str(file_path),
            "--document-id",
            "doc-refund-html",
            "--index-name",
            "enterprise-kb",
            "--language",
            "en",
            "--tag",
            "refund",
        ],
    )

    exit_code = index_file.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "indexed"' in captured.out
    assert captured.err == ""


def test_index_file_script_indexes_pdf_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
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

    index_file = _load_index_file_module()
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_file.py",
            "--path",
            str(pdf_path),
            "--document-id",
            "doc-refund-pdf",
            "--index-name",
            "enterprise-kb",
            "--language",
            "en",
            "--tag",
            "refund",
        ],
    )

    exit_code = index_file.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "indexed"' in captured.out
    assert captured.err == ""


def test_index_file_script_returns_error_for_unsupported_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "refund.docx"
    file_path.write_text("unsupported", encoding="utf-8")

    index_file = _load_index_file_module()
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_file.py",
            "--path",
            str(file_path),
            "--document-id",
            "doc-refund-file",
            "--index-name",
            "enterprise-kb",
        ],
    )

    exit_code = index_file.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert '"error_code": "INVALID_INPUT"' in captured.err


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


def test_index_file_script_returns_error_for_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.md"

    index_file = _load_index_file_module()
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_file.py",
            "--path",
            str(missing_path),
            "--document-id",
            "doc-refund-file",
            "--index-name",
            "enterprise-kb",
        ],
    )

    exit_code = index_file.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert '"error_code": "INVALID_INPUT"' in captured.err
