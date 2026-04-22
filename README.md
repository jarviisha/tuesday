# Tuesday RAG Core

Tuesday RAG Core is a FastAPI-based MVP RAG service built with a ports-and-adapters structure under `src/`.

## Prerequisites

- Python 3.12+
- `pip`

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

## Source-of-Truth Commands

These commands are the Phase 1 baseline for local development and CI:

```bash
ruff check .
pytest
pytest tests/unit
pytest tests/api/test_health.py
python -m uvicorn tuesday_rag.api.app:app --reload
```

## Local API

Start the API locally:

```bash
python -m uvicorn tuesday_rag.api.app:app --reload
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
pytest tests/unit
pytest tests/api/test_health.py
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
python scripts/smoke_test.py
```

Run the same smoke test against a running local or staging-like API:

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

## Quality Evaluation

Run the Phase 3 benchmark:

```bash
python scripts/benchmark_quality.py
```

Run the Phase 3 regression suite:

```bash
pytest tests/regression
```

## Repository Layout

- `src/tuesday_rag/api/`: FastAPI app, schemas, and request handling
- `src/tuesday_rag/application/`: use cases and services
- `src/tuesday_rag/domain/`: domain models, ports, and errors
- `src/tuesday_rag/infrastructure/`: chunking, providers, and vector store adapters
- `tests/`: unit, API, and integration tests
- `docs/`: design notes and post-MVP planning
