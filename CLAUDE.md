# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Entry point for session context

Before substantial implementation work, read [docs.md](docs.md) — it is the consolidated project reference and source of truth for locked behavior, decision-log IDs, runtime defaults, error mapping, and boundary rules.

When a detail here conflicts with `docs.md` or active feature spec artifacts under `specs/`, those documents win.

- `docs.md` — consolidated active spec (replaces the legacy `docs/` tree).
- `specs/<NNN>-<feature>/` — feature-specific artifacts: `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `contracts/`, `checklists/`.
- `.specify/memory/constitution.md` — process principles that apply when spec questions arise.
- The legacy `docs/` tree exists as migration/archive background only; do not treat it as the current workflow source of truth.

## Commands

Use the in-repo virtualenv (`./.venv/bin/python`) rather than system Python; the repo ships a `.venv`.

```bash
./.venv/bin/python -m ruff check .
./.venv/bin/python -m pytest
./.venv/bin/python -m pytest tests/unit                            # focused
./.venv/bin/python -m pytest tests/api/test_health.py              # single file
./.venv/bin/python -m pytest tests/api/test_health.py::test_ok     # single test
./.venv/bin/python -m uvicorn tuesday.api.app:app --reload         # local API
```

Phase smoke / benchmark / internal ingestion scripts:

```bash
./.venv/bin/python scripts/smoke_test.py [--base-url http://127.0.0.1:8000]
./.venv/bin/python scripts/benchmark_quality.py
./.venv/bin/python scripts/index_file.py --path <file> --document-id <id> --index-name <name> [--language ..] [--tag ..]
./.venv/bin/python scripts/index_directory.py --dir <dir> --index-name <name> [--recursive] [--include GLOB] [--exclude GLOB] [--dry-run] [--output summary.json]
```

First-time setup only: `pip install -e '.[dev]'` into a Python 3.12+ venv.

## Spec-driven development (speckit)

This repo uses speckit for feature development. The current active feature directory is tracked in `.specify/feature.json`. Speckit skills drive the SDD cycle:

| Skill | Purpose |
|---|---|
| `/speckit-specify` | Create or update `spec.md` from a feature description |
| `/speckit-clarify` | Ask targeted questions to fill spec gaps |
| `/speckit-plan` | Generate `plan.md` design artifacts |
| `/speckit-tasks` | Generate dependency-ordered `tasks.md` |
| `/speckit-implement` | Execute tasks from `tasks.md` |
| `/speckit-analyze` | Cross-artifact consistency check across spec/plan/tasks |
| `/speckit-checklist` | Generate a custom checklist for the feature |
| `/speckit-constitution` | Create or update `.specify/memory/constitution.md` |

Feature artifacts live under `specs/<NNN>-<feature>/` (e.g. `specs/001-llamaindex-qdrant-adapter/`). The full SDD workflow is: specify → clarify → plan → tasks → implement.

## High-level architecture

Tuesday is a capability-oriented FastAPI platform. The only capability today is RAG (`src/tuesday/rag/`). The dependency flow is strictly one-directional and must not be broken:

```
api → runtime → capability (ingestion/retrieval/generation) → domain ports → infrastructure adapters
```

Packages map as:

- `src/tuesday/api/` — product-level HTTP shell: app factory, middleware, error mapping, request-level observability, `/health`, and router mounting. API code only validates, calls use cases, and maps responses/errors — no business rules.
- `src/tuesday/runtime/` — composition root: `RuntimeConfig`, `Container`, `build_runtime_from_env`, startup checks. Config is loaded once at startup through the `lifespan` hook (DL-007).
- `src/tuesday/shared/` — cross-capability validation helpers only.
- `src/tuesday/rag/api/` — `APIRouter` + Pydantic request/response schemas for `/documents/index`, `/retrieve`, `/generate`.
- `src/tuesday/rag/domain/` — models, protocol-style ports, domain errors. **Must not import framework or provider SDKs.**
- `src/tuesday/rag/{ingestion,retrieval,generation}/` — `use_case.py` + `service.py` (+ prompt builder, file use case). Orchestration only; also must not import SDKs/frameworks.
- `src/tuesday/rag/infrastructure/` — adapters: `CharacterChunker`, `InMemoryVectorStore`/`FileBackedVectorStore`, demo + vendor providers (OpenAI/Gemini/Azure via stdlib `urllib` in `http_client.py`), `LocalFileDocumentParser`, `ResilientEmbedding/LLM/VectorStore` wrappers. Framework/SDK types must not leak past this layer.
- `src/tuesday/rag/evaluation/` — `GENERATION_GOLDEN_CASES` and fixtures used by benchmark/regression.

Tests mirror the scopes: `tests/unit/` (domain, use cases, scripts, config bounds), `tests/api/` (HTTP contract, shell), `tests/integration/` (adapters, persistence), `tests/smoke/` (end-to-end happy path), `tests/regression/` (quality baseline), plus `tests/fixtures.py` and `tests/conftest.py`.

## Locked behavior (do not change without a decision-log entry)

These are frequent sources of accidental regressions. Full list lives in `docs.md` (sourced from `docs/14-decision-log.md`).

- **Re-index policy**: `replace-by-document_id-within-index_name`; idempotent on same `(document_id, index_name, content)` (DL-001).
- **`Indexer`/`Retriever`/`Generator`** are capability-local services, not core ports — do not push them down to adapters or up to framework abstractions (DL-002).
- **Filter `tags` semantics**: `contains-any` (DL-003). Keep this consistent across fake adapter, real adapter, and contract tests.
- **Insufficient context**: when no context exists, orchestration returns `GeneratedAnswer(insufficient_context=True, grounded=False, citations=[], used_chunks=[])` with the literal `config.insufficient_context_answer`, **without** calling `LLMProvider` (DL-004).
- **Citations**: always by `chunk_id`, always a subset of `used_chunks.chunk_id`; if `used_chunks` is empty, `citations` must be empty (DL-005).
- **Chunking**: token-based via `LlamaIndex SentenceSplitter`; `chunk_overlap < chunk_size` (DL-006 superseded by DL-035).
- **PDF parser**: `pdftotext` via subprocess; missing → `DOCUMENT_PARSE_ERROR`. Startup check modes via `TUESDAY_PDF_STARTUP_CHECK_MODE ∈ {off, warn, strict}` (DL-024).
- **Observability**: every request must log `request_id`, `use_case`, `error_code`, `latency_ms`, `failure_group/component/mode`; **never** log raw content or sensitive data (DL-009).
- **Public API surface**: exactly `POST /documents/index`, `POST /retrieve`, `POST /generate`, `GET /health`. File parsers are **internal** ingestion only via `FileIngestionUseCase` + scripts (DL-008). `PARTIAL_INDEXED` status is not part of public MVP (DL-010).

Error-code → HTTP status mapping, runtime defaults and bounds, and validation rules are in `docs.md` (sections 7–9 of the core brief); treat those tables as locked.

## Runtime config

Resolution order: OS env (`TUESDAY_*` prefix) > repo-root `.env` > built-in defaults in `RuntimeConfig`. The legacy `TUESDAY_RAG_*` prefix is still accepted as a fallback but is not the recommended path. Start from `.env.example`.

Backend selectors:

- `TUESDAY_VECTOR_STORE_BACKEND` ∈ `memory`|`file` (with `TUESDAY_VECTOR_STORE_FILE_PATH` for `file`).
- `TUESDAY_EMBEDDING_PROVIDER_BACKEND` / `TUESDAY_GENERATION_PROVIDER_BACKEND` ∈ `demo`|`openai`|`gemini`|`azure_openai`.
- `TUESDAY_PDF_STARTUP_CHECK_MODE` ∈ `off`|`warn`|`strict`.

## Language rules

- English by default for source, tests, commit messages, comments, and identifiers.
- `docs.md`, feature spec artifacts under `specs/`, and `.specify/memory/constitution.md` may use Vietnamese **with full diacritics** — do not write Vietnamese without diacritics in those files.
- Fixtures, sample payloads, benchmark cases, and other domain input prefer Vietnamese to match the evaluation baseline, unless the scenario explicitly requires another language.
- Files under `prompt/` are not constrained by this rule.

## Working rules specific to this repo

- **Surgical changes only**: touch only files/lines needed for the task; do not refactor adjacent code. Mention out-of-scope issues separately instead of folding them in.
- **No new `.md` files** (including in `docs/`) unless the user asks — extend existing documents. New feature specs go under `specs/` via speckit skills, not freehand.
- **Lint must pass**: ruff with rules `E, F, I, B, UP` (see `pyproject.toml`), `line-length = 100`, `target-version = py312`.
- **Commit prefix required**: use `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `build:`, or `ci:` on every commit. Keep the subject short, imperative, and scoped to one change.
- **When changing locked semantics, config bounds, or contract behavior**: update tests, the active spec in `docs.md`, the decision log, and the core brief section together — don't ship them apart.
- **Never re-introduce `src/tuesday_rag/`** — the legacy shim was deleted; all imports use `tuesday.*`.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read [specs/002-llamaindex-rag-migration/plan.md](/home/jarviisha/development/tuesday/specs/002-llamaindex-rag-migration/plan.md)
<!-- SPECKIT END -->
