import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_index_directory_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "index_directory.py"
    spec = spec_from_file_location("index_directory", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _patch_runtime_factory(
    *,
    monkeypatch: pytest.MonkeyPatch,
    module,
    runtime_container,
) -> None:
    monkeypatch.setattr(module, "build_runtime_from_env", lambda: runtime_container)


def test_index_directory_script_indexes_supported_files(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )
    (tmp_path / "onboarding.txt").write_text(
        "New employees must complete onboarding documents within 3 days.",
        encoding="utf-8",
    )
    (tmp_path / "refund.html").write_text(
        "<html><body><p>Refund requests must use the support portal.</p></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "ignore.docx").write_text("unsupported", encoding="utf-8")

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--language",
            "en",
            "--tag",
            "batch",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert summary["total_files"] == 3
    assert summary["indexed_files"] == 3
    assert summary["failed_files"] == 0
    assert {result["document_id"] for result in summary["results"]} == {
        "onboarding-txt",
        "refund-html",
        "refund-md",
    }

    retrieval_result = runtime_container.retrieval_use_case.execute(
        {
            "query": "How long do new employees have to complete onboarding documents?",
            "index_name": "enterprise-kb",
            "filters": {"tags": ["batch"]},
        }
    )
    assert retrieval_result.chunks


def test_index_directory_script_writes_summary_to_output_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )
    output_path = tmp_path / "reports" / "batch-summary.json"

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--output",
            str(output_path),
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    stdout_summary = json.loads(captured.out)
    file_summary = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout_summary == file_summary
    assert stdout_summary["output"] == str(output_path)


def test_index_directory_script_dry_run_does_not_index_files(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--dry-run",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["dry_run"] is True
    assert summary["planned_files"] == 1
    assert summary["indexed_files"] == 0
    assert summary["results"][0]["status"] == "dry_run"

    retrieval_result = runtime_container.retrieval_use_case.execute(
        {
            "query": "How long can customers request a refund?",
            "index_name": "enterprise-kb",
        }
    )
    assert retrieval_result.chunks == []


def test_index_directory_script_ignores_nested_files_without_recursive_flag(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    nested_directory = tmp_path / "nested"
    nested_directory.mkdir()
    (nested_directory / "manager-notes.md").write_text(
        "Managers must schedule an introduction meeting with the team.",
        encoding="utf-8",
    )
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["recursive"] is False
    assert summary["total_files"] == 1
    assert {result["document_id"] for result in summary["results"]} == {"refund-md"}


def test_index_directory_script_indexes_nested_files_with_recursive_flag(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    nested_directory = tmp_path / "handbook" / "team"
    nested_directory.mkdir(parents=True)
    (nested_directory / "manager-notes.md").write_text(
        "Managers must schedule an introduction meeting with the team.",
        encoding="utf-8",
    )
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--recursive",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["recursive"] is True
    assert summary["total_files"] == 2
    assert {result["document_id"] for result in summary["results"]} == {
        "handbook-team-manager-notes-md",
        "refund-md",
    }


def test_index_directory_script_filters_with_include_pattern(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )
    (tmp_path / "onboarding.txt").write_text(
        "New employees must complete onboarding documents within 3 days.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--include",
            "*.md",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["include_patterns"] == ["*.md"]
    assert {result["document_id"] for result in summary["results"]} == {"refund-md"}


def test_index_directory_script_filters_with_exclude_pattern(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )
    (tmp_path / "onboarding.txt").write_text(
        "New employees must complete onboarding documents within 3 days.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--exclude",
            "*.txt",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["exclude_patterns"] == ["*.txt"]
    assert {result["document_id"] for result in summary["results"]} == {"refund-md"}


def test_index_directory_script_exclude_wins_over_include(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    nested_directory = tmp_path / "handbook" / "team"
    nested_directory.mkdir(parents=True)
    (nested_directory / "manager-notes.md").write_text(
        "Managers must schedule an introduction meeting with the team.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--recursive",
            "--include",
            "**/*.md",
            "--exclude",
            "handbook/**/*.md",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert '"error_code": "INVALID_INPUT"' in captured.err


def test_index_directory_script_dry_run_respects_recursive_and_patterns(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    nested_directory = tmp_path / "handbook" / "team"
    nested_directory.mkdir(parents=True)
    (nested_directory / "manager-notes.md").write_text(
        "Managers must schedule an introduction meeting with the team.",
        encoding="utf-8",
    )
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--dry-run",
            "--recursive",
            "--include",
            "*.md",
            "--exclude",
            "handbook/*",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["dry_run"] is True
    assert summary["planned_files"] == 1
    assert {result["document_id"] for result in summary["results"]} == {"refund-md"}


def test_index_directory_script_returns_error_for_missing_directory(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    missing_directory = tmp_path / "missing"
    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(missing_directory),
            "--index-name",
            "enterprise-kb",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert '"error_code": "INVALID_INPUT"' in captured.err


def test_index_directory_script_returns_error_when_no_supported_files(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "ignore.docx").write_text("unsupported", encoding="utf-8")

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert '"error_code": "INVALID_INPUT"' in captured.err


def test_index_directory_script_continues_on_file_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )
    (tmp_path / "blank.txt").write_text("   \n\t", encoding="utf-8")

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 1
    assert captured.err == ""
    assert summary["total_files"] == 2
    assert summary["indexed_files"] == 1
    assert summary["failed_files"] == 1
    assert summary["errors"][0]["document_id"] == "blank-txt"
    assert summary["errors"][0]["error_code"] == "EMPTY_DOCUMENT"


def test_index_directory_script_writes_partial_failure_summary_to_output_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_container,
    tmp_path: Path,
) -> None:
    (tmp_path / "refund.md").write_text(
        "Customers can request a refund within 7 days.",
        encoding="utf-8",
    )
    (tmp_path / "blank.txt").write_text("   \n\t", encoding="utf-8")
    output_path = tmp_path / "reports" / "batch-summary.json"

    index_directory = _load_index_directory_module()
    _patch_runtime_factory(
        monkeypatch=monkeypatch,
        module=index_directory,
        runtime_container=runtime_container,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "index_directory.py",
            "--dir",
            str(tmp_path),
            "--index-name",
            "enterprise-kb",
            "--output",
            str(output_path),
        ],
    )

    exit_code = index_directory.main()
    captured = capsys.readouterr()
    stdout_summary = json.loads(captured.out)
    file_summary = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert stdout_summary == file_summary
    assert stdout_summary["failed_files"] == 1
    assert stdout_summary["errors"][0]["error_code"] == "EMPTY_DOCUMENT"
