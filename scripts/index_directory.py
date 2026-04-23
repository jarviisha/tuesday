import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from tuesday_rag.domain.errors import DomainError, InvalidInputError
from tuesday_rag.infrastructure.file_document_parser import LocalFileDocumentParser
from tuesday_rag.runtime.container import build_runtime_from_env


def main() -> int:
    container = build_runtime_from_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--index-name", required=True)
    parser.add_argument("--output")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--language")
    parser.add_argument("--tag", action="append", default=[])
    args = parser.parse_args()

    metadata: dict[str, object] = {}
    if args.language:
        metadata["language"] = args.language
    if args.tag:
        metadata["tags"] = args.tag

    try:
        directory = _validate_directory(args.dir)
        candidate_paths = _supported_files(
            directory,
            recursive=args.recursive,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
        )
        if not candidate_paths:
            raise InvalidInputError(
                "directory does not contain supported files",
                details={"field": "dir"},
            )
    except DomainError as exc:
        print(
            json.dumps(
                {
                    "error_code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            ),
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        summary = {
            "directory": str(directory),
            "index_name": args.index_name,
            "output": args.output,
            "dry_run": True,
            "recursive": args.recursive,
            "include_patterns": args.include,
            "exclude_patterns": args.exclude,
            "total_files": len(candidate_paths),
            "planned_files": len(candidate_paths),
            "indexed_files": 0,
            "failed_files": 0,
            "results": [
                {
                    "path": str(path),
                    "document_id": _document_id_from_relative_path(directory, path),
                    "index_name": args.index_name,
                    "status": "dry_run",
                }
                for path in candidate_paths
            ],
            "errors": [],
        }
        summary_json = json.dumps(summary)
        if args.output:
            _write_output(args.output, summary_json)
        print(summary_json)
        return 0

    results: list[dict] = []
    errors: list[dict] = []

    for path in candidate_paths:
        document_id = _document_id_from_relative_path(directory, path)
        try:
            result = container.file_ingestion_use_case.execute(
                {
                    "path": str(path),
                    "document_id": document_id,
                    "index_name": args.index_name,
                    "metadata": metadata or None,
                }
            )
        except DomainError as exc:
            errors.append(
                {
                    "path": str(path),
                    "document_id": document_id,
                    "error_code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            )
            continue
        results.append(
            {
                "path": str(path),
                "document_id": document_id,
                **asdict(result),
            }
        )

    summary = {
        "directory": str(directory),
        "index_name": args.index_name,
        "output": args.output,
        "dry_run": False,
        "recursive": args.recursive,
        "include_patterns": args.include,
        "exclude_patterns": args.exclude,
        "total_files": len(candidate_paths),
        "planned_files": len(candidate_paths),
        "indexed_files": len(results),
        "failed_files": len(errors),
        "results": results,
        "errors": errors,
    }
    summary_json = json.dumps(summary)
    if args.output:
        _write_output(args.output, summary_json)
    print(summary_json)
    return 0 if not errors else 1


def _validate_directory(raw_directory: str) -> Path:
    if not raw_directory.strip():
        raise InvalidInputError("dir must not be blank", details={"field": "dir"})
    directory = Path(raw_directory).expanduser()
    if not directory.exists():
        raise InvalidInputError("dir does not exist", details={"field": "dir"})
    if not directory.is_dir():
        raise InvalidInputError("dir must point to a directory", details={"field": "dir"})
    return directory.resolve()


def _supported_files(
    directory: Path,
    *,
    recursive: bool,
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> list[Path]:
    supported_extensions = LocalFileDocumentParser.supported_extensions()
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    return sorted(
        path.resolve()
        for path in iterator
        if path.is_file()
        and path.suffix.lower() in supported_extensions
        and _matches_patterns(
            relative_path=path.relative_to(directory).as_posix(),
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
    )


def _document_id_from_relative_path(directory: Path, path: Path) -> str:
    relative_path = path.relative_to(directory).as_posix().lower()
    document_id = re.sub(r"[^a-z0-9._-]+", "-", relative_path)
    document_id = document_id.replace("/", "-").replace(".", "-")
    document_id = re.sub(r"-{2,}", "-", document_id).strip("-")
    return document_id


def _write_output(output_path: str, summary_json: str) -> None:
    path = Path(output_path).expanduser()
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{summary_json}\n", encoding="utf-8")


def _matches_patterns(
    *,
    relative_path: str,
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> bool:
    if include_patterns and not any(
        fnmatch.fnmatch(relative_path, pattern) for pattern in include_patterns
    ):
        return False
    if any(fnmatch.fnmatch(relative_path, pattern) for pattern in exclude_patterns):
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
