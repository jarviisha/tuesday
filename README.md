# Tuesday

[![CI](https://github.com/jarviisha/tuesday/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jarviisha/tuesday/actions/workflows/ci.yml)

Tuesday is a FastAPI-based platform shell with capability-oriented modules under `src/`, currently centered on the `rag` capability.

## CI

GitHub Actions runs `ruff`, `pyright` (`standard` mode), and `pytest` on every push and pull request.

## Prerequisites

- Python 3.12+
- `pdftotext` on `PATH` if you want to ingest `.pdf` files through the internal file-ingestion flow

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
./.venv/bin/python -m uvicorn tuesday.api.app:app --reload
```

## Source-of-Truth Commands

These commands are the Phase 1 baseline for local development and CI:

```bash
./.venv/bin/python -m ruff check .
./.venv/bin/pyright
./.venv/bin/python -m pytest
./.venv/bin/python -m pytest tests/unit
./.venv/bin/python -m pytest tests/api/test_health.py
./.venv/bin/python -m uvicorn tuesday.api.app:app --reload
```

## Local API

Start the API locally:

```bash
./.venv/bin/python -m uvicorn tuesday.api.app:app --reload
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

Run static type checking with the same configuration used by CI:

```bash
./.venv/bin/pyright
```

## Runtime Configuration

Runtime configuration is loaded from:

1. OS environment variables with the `TUESDAY_` prefix
2. a local `.env` file in the repository root if present
3. built-in defaults in `RuntimeConfig`

If the same key exists in both places, the OS environment variable wins over `.env`.

You can start from [.env.example](/home/jarviisha/development/tuesday/.env.example). The Phase 1 runbook, config baseline, and release baseline are documented in `docs/history/post-mvp/phase-1/27-runbook-config-va-release-baseline-implementation.md` (historical archive).

Runtime and backend configuration includes:

```bash
TUESDAY_VECTOR_STORE_BACKEND=memory|file|qdrant
TUESDAY_VECTOR_STORE_FILE_PATH=.tuesday/vector_store.json
TUESDAY_QDRANT_URL=
TUESDAY_QDRANT_API_KEY=
TUESDAY_QDRANT_LOCATION=
TUESDAY_QDRANT_COLLECTION_PREFIX=tuesday
TUESDAY_QDRANT_DENSE_VECTOR_SIZE=512
TUESDAY_PDF_STARTUP_CHECK_MODE=off|warn|strict
TUESDAY_EMBEDDING_PROVIDER_BACKEND=demo|openai|gemini|azure_openai
TUESDAY_GENERATION_PROVIDER_BACKEND=demo|openai|gemini|azure_openai
TUESDAY_OPENAI_API_KEY=
TUESDAY_OPENAI_BASE_URL=https://api.openai.com/v1
TUESDAY_OPENAI_EMBEDDING_MODEL=
TUESDAY_OPENAI_GENERATION_MODEL=
TUESDAY_GEMINI_API_KEY=
TUESDAY_GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
TUESDAY_GEMINI_EMBEDDING_MODEL=
TUESDAY_GEMINI_GENERATION_MODEL=
TUESDAY_AZURE_OPENAI_API_KEY=
TUESDAY_AZURE_OPENAI_ENDPOINT=
TUESDAY_AZURE_OPENAI_API_VERSION=2024-10-21
TUESDAY_AZURE_OPENAI_EMBEDDING_DEPLOYMENT=
TUESDAY_AZURE_OPENAI_GENERATION_DEPLOYMENT=
TUESDAY_EMBEDDING_TIMEOUT_MS=1000
TUESDAY_EMBEDDING_MAX_RETRIES=0
TUESDAY_GENERATION_TIMEOUT_MS=1000
TUESDAY_GENERATION_MAX_RETRIES=0
TUESDAY_VECTOR_STORE_TIMEOUT_MS=1000
TUESDAY_VECTOR_STORE_MAX_RETRIES=0
```

Use the file-backed adapter when you want persistence across process restarts:

```bash
export TUESDAY_VECTOR_STORE_BACKEND=file
export TUESDAY_VECTOR_STORE_FILE_PATH=.tuesday/vector_store.json
```

Use Qdrant when you want a real vector-store backend:

```bash
export TUESDAY_VECTOR_STORE_BACKEND=qdrant
export TUESDAY_QDRANT_LOCATION=:memory:
export TUESDAY_QDRANT_COLLECTION_PREFIX=tuesday
export TUESDAY_QDRANT_DENSE_VECTOR_SIZE=512
```

For remote Qdrant, set `TUESDAY_QDRANT_URL` and `TUESDAY_QDRANT_API_KEY` instead of `TUESDAY_QDRANT_LOCATION`.

Provider backends default to `demo` for both embeddings and generation. To use real providers, set the backend selectors and the matching credentials/model or deployment env vars for `OpenAI`, `Gemini`, or `Azure OpenAI`.
When `TUESDAY_VECTOR_STORE_BACKEND=qdrant` and `TUESDAY_EMBEDDING_PROVIDER_BACKEND=demo`, runtime automatically switches to a deterministic dense demo embedding provider so cosine retrieval works with the real vector store.

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

PDF ingestion depends on the system `pdftotext` binary. If it is missing, PDF parsing fails at ingestion time by default.

You can also opt into a startup-time check:

- `TUESDAY_PDF_STARTUP_CHECK_MODE=off`: do not check at startup
- `TUESDAY_PDF_STARTUP_CHECK_MODE=warn`: log a warning if `pdftotext` is missing
- `TUESDAY_PDF_STARTUP_CHECK_MODE=strict`: fail fast during runtime startup if `pdftotext` is missing

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

- `src/tuesday/api/`: application shell for FastAPI. Contains the app entrypoint, middleware, error mapping, request-level observability, `/health`, and router mounting.
- `src/tuesday/runtime/`: composition root for the whole application. Contains config and container wiring that build adapters and use cases for mounted capabilities.
- `src/tuesday/shared/`: cross-cutting helpers reused by multiple capabilities. At the moment this mainly holds validation utilities for runtime limits and input guardrails that do not belong to one specific feature package.
- `src/tuesday/rag/api/`: RAG HTTP surface. Contains the RAG router and request/response schemas for `/documents/index`, `/retrieve`, and `/generate`.
- `src/tuesday/rag/domain/`: RAG domain contracts. Contains domain models, protocol-style ports, and domain errors that define the stable language between RAG use cases and infrastructure adapters.
- `src/tuesday/rag/ingestion/`: document indexing capability. Contains the ingestion use case, file-ingestion use case, and indexing service that turn source documents into chunks, embeddings, and stored indexed chunks.
- `src/tuesday/rag/retrieval/`: retrieval capability. Contains the retrieval use case and retriever service that embed a query, apply filter semantics, read from the vector store, and return ranked retrieved chunks.
- `src/tuesday/rag/generation/`: answer generation capability. Contains the generation use case, prompt builder, and generator service that decide whether context is sufficient, build a grounded prompt, and validate the generated answer/citations.
- `src/tuesday/rag/infrastructure/`: RAG adapter implementations for external or concrete mechanics. Contains chunking, embedding/LLM providers, vector-store adapters, resilience wrappers, and file-document parsing.
- `src/tuesday/rag/evaluation/`: evaluation assets for quality measurement. Contains golden cases and related inputs used by benchmark and regression flows to track retrieval/generation behavior over time.
- `tests/`: unit, API, and integration tests
- `docs/`: design notes and post-MVP planning

## Architecture Notes

- `api/` handles HTTP transport, schema mapping, and request-level observability.
- `runtime/` wires the app together through a shared container.
- Capability packages (`ingestion/`, `retrieval/`, `generation/`) hold orchestration logic close to each feature area.
- `domain/` and `infrastructure/` keep the ports-and-adapters boundary intact.
