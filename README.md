# Tuesday RAG Core

Tuesday RAG Core is a FastAPI-based RAG service built under `src/` with a ports-and-adapters foundation and a capability-oriented package layout.

## Prerequisites

- Python 3.12+

## Development Setup

Create or reuse a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project with development dependencies:

```bash
pip install -e '.[dev]'
```

If the repository already has `.venv`, prefer running commands through it directly instead of using system Python:

```bash
./.venv/bin/python -m pytest
./.venv/bin/python -m uvicorn tuesday_rag.api.app:app --reload
```

## Source-of-Truth Commands

These commands are the Phase 1 baseline for local development and CI:

```bash
./.venv/bin/python -m ruff check .
./.venv/bin/python -m pytest
./.venv/bin/python -m pytest tests/unit
./.venv/bin/python -m pytest tests/api/test_health.py
./.venv/bin/python -m uvicorn tuesday_rag.api.app:app --reload
```

## Local API

Start the API locally:

```bash
./.venv/bin/python -m uvicorn tuesday_rag.api.app:app --reload
```

Health check endpoint:

```text
GET /health
```

Example quick check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Test Targets

Use targeted tests when iterating:

```bash
./.venv/bin/python -m pytest tests/unit
./.venv/bin/python -m pytest tests/api/test_health.py
./.venv/bin/python -m pytest tests/api tests/smoke/test_index_retrieve_generate.py tests/regression/test_quality_regression.py -q
```

## Runtime Configuration

Runtime configuration is loaded from environment variables with the `TUESDAY_RAG_` prefix. The Phase 1 runbook, config baseline, and release baseline are documented in `docs/post-mvp/phase-1/27-runbook-config-va-release-baseline-implementation.md`.

Phase 2 operational hardening adds:

```bash
TUESDAY_RAG_VECTOR_STORE_BACKEND=memory|file
TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/vector_store.json
TUESDAY_RAG_EMBEDDING_TIMEOUT_MS=1000
TUESDAY_RAG_EMBEDDING_MAX_RETRIES=0
TUESDAY_RAG_GENERATION_TIMEOUT_MS=1000
TUESDAY_RAG_GENERATION_MAX_RETRIES=0
TUESDAY_RAG_VECTOR_STORE_TIMEOUT_MS=1000
TUESDAY_RAG_VECTOR_STORE_MAX_RETRIES=0
```

Use the file-backed adapter when you want persistence across process restarts:

```bash
export TUESDAY_RAG_VECTOR_STORE_BACKEND=file
export TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/vector_store.json
```

## Smoke Test

Run the Phase 2 smoke test in-process:

```bash
./.venv/bin/python scripts/smoke_test.py
```

Run the same smoke test against a running local or staging-like API:

```bash
./.venv/bin/python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

## Quality Evaluation

Run the Phase 3 benchmark:

```bash
./.venv/bin/python scripts/benchmark_quality.py
```

Run the Phase 3 regression suite:

```bash
./.venv/bin/python -m pytest tests/regression
```

## Internal File Ingestion

Index a local `.txt`, `.md`, `.html`, or `.pdf` file through the internal file-ingestion entrypoint:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.md \
  --document-id doc-refund-file \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

This command does not change the public HTTP API. It uses the internal file-ingestion flow added in Phase 4.

HTML files are also supported:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.html \
  --document-id doc-refund-html \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

PDF files are also supported:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.pdf \
  --document-id doc-refund-pdf \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

Batch index every supported file in a local directory:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch
```

Include nested directories when needed:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch \
  --recursive
```

Write the batch summary to a JSON file while keeping `stdout` output:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch \
  --recursive \
  --output /tmp/tuesday-batch-summary.json
```

Filter files with include/exclude patterns on relative paths:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --recursive \
  --include '*.md' \
  --exclude 'handbook/*'
```

Preview a batch run without indexing anything:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --recursive \
  --include '*.md' \
  --exclude 'handbook/*' \
  --dry-run
```

## Repository Layout

- `src/tuesday_rag/api/`: FastAPI app, schemas, and request handling
- `src/tuesday_rag/runtime/`: composition root and runtime wiring
- `src/tuesday_rag/shared/`: shared validation helpers
- `src/tuesday_rag/ingestion/`: ingestion use case and indexing service
- `src/tuesday_rag/retrieval/`: retrieval use case and retrieval service
- `src/tuesday_rag/generation/`: generation use case, prompt builder, and generation service
- `src/tuesday_rag/domain/`: domain models, ports, and errors
- `src/tuesday_rag/infrastructure/`: chunking, providers, and vector store adapters
- `src/tuesday_rag/evaluation/`: golden cases used by benchmark/regression flows
- `tests/`: unit, API, and integration tests
- `docs/`: design notes and post-MVP planning

## Architecture Notes

- `api/` handles HTTP transport, schema mapping, and request-level observability.
- `runtime/` wires the app together through a shared container.
- Capability packages (`ingestion/`, `retrieval/`, `generation/`) hold orchestration logic close to each feature area.
- `domain/` and `infrastructure/` keep the ports-and-adapters boundary intact.
