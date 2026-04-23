import argparse
import json
import sys
from dataclasses import asdict

from tuesday_rag.domain.errors import DomainError
from tuesday_rag.runtime.container import container


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--index-name", required=True)
    parser.add_argument("--title")
    parser.add_argument("--language")
    parser.add_argument("--tag", action="append", default=[])
    args = parser.parse_args()

    metadata: dict[str, object] = {}
    if args.language:
        metadata["language"] = args.language
    if args.tag:
        metadata["tags"] = args.tag

    try:
        result = container.file_ingestion_use_case.execute(
            {
                "path": args.path,
                "document_id": args.document_id,
                "index_name": args.index_name,
                "title": args.title,
                "metadata": metadata or None,
            }
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

    print(json.dumps(asdict(result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
