# Codebase Memory

## Architecture Overview

Tuesday uses a `src/` layout with a thin FastAPI shell and a capability-oriented RAG core.

- `src/tuesday/api/` is the product HTTP shell.
- `src/tuesday/runtime/` is the composition root and environment-driven runtime setup.
- `src/tuesday/rag/` is the main capability, organized with ports-and-adapters boundaries.
- `src/tuesday/shared/` contains shared validation helpers.

Dependency direction is intentionally one-way:

`api -> runtime -> rag use cases/services -> domain ports -> infrastructure adapters`

Business rules stay in `rag/*/use_case.py`, `rag/*/service.py`, and `rag/domain/`. Framework code and provider SDK details stay in `api/` or `rag/infrastructure/`.

## Main Modules

### App Shell

- `src/tuesday/api/app.py`
  Builds the FastAPI app, loads the container in lifespan, mounts `/health`, installs middleware, and maps `DomainError` to HTTP responses.
- `src/tuesday/api/middleware.py`
  Adds request-scoped metadata such as `x-request-id` and latency headers.
- `src/tuesday/api/observability.py`
  Classifies errors for logs and operational metrics.

### Runtime

- `src/tuesday/runtime/config.py`
  Defines runtime defaults, env loading from `.env` and `TUESDAY_*`, and config validation.
- `src/tuesday/runtime/container.py`
  Wires the selected vector store, embedding provider, generation provider, resilience wrappers, chunker, parser, and use cases.

### RAG Capability

- `src/tuesday/rag/api/`
  Public schemas and the 3 main endpoints: `/documents/index`, `/retrieve`, `/generate`.
- `src/tuesday/rag/domain/`
  Core models, ports, and domain errors. This layer is framework-independent.
- `src/tuesday/rag/ingestion/`
  Input validation, source-document normalization, chunking, embedding, and indexing.
- `src/tuesday/rag/retrieval/`
  Retrieval orchestration plus lexical reranking after vector store results.
- `src/tuesday/rag/generation/`
  Context sufficiency policy, prompt building, and grounded answer generation.
- `src/tuesday/rag/infrastructure/`
  Adapters for chunking, vector stores, file parsing, resilience wrappers, demo providers, and vendor providers.
- `src/tuesday/rag/evaluation/`
  Golden cases used by benchmark/regression flows.

### Operational Scripts

- `scripts/index_file.py`
  Internal file ingestion for a single file.
- `scripts/index_directory.py`
  Internal batch ingestion with `--recursive`, include/exclude patterns, `--dry-run`, and optional summary output.
- `scripts/smoke_test.py`
  End-to-end sanity check for index -> retrieve -> generate.
- `scripts/benchmark_quality.py`
  Runs golden-case benchmarks and writes JSON metrics under `benchmarks/`.

## Main Data Flow

### 1. Document Indexing

`POST /documents/index`

1. API schema parses the request.
2. `IngestionUseCase` validates fields and metadata, trims content, computes checksum, and creates `SourceDocument`.
3. `CharacterChunker` splits the document into chunks.
4. `IndexerService` requests embeddings from the configured embedding provider.
5. The selected vector store replaces existing chunks for the same `document_id` within the same `index_name`.
6. A `DocumentIndexResult` is returned to the API layer.

### 2. Retrieval

`POST /retrieve`

1. `RetrievalUseCase` validates `query`, `top_k`, `filters`, and `index_name`.
2. `RetrieverService` embeds the query.
3. The vector store returns candidate chunks.
4. `retrieval/ranking_policy.py` reranks results lexically and trims to `top_k`.
5. `RetrievalResponse` is returned with `applied_filters`.

### 3. Generation

`POST /generate`

Two modes are supported:

- external retrieval: caller passes `retrieved_chunks`
- internal retrieval: caller passes `retrieval_request`, and the use case retrieves first

Then:

1. `GenerationUseCase` validates the request and resolves chunks.
2. `GeneratorService` limits context to `max_context_chunks`.
3. `generation/context_policy.py` decides whether the available chunks are sufficient.
4. If context is insufficient, the service returns the configured fallback answer without calling the LLM provider.
5. If context is sufficient, `prompt_builder.py` builds a grounded prompt and the LLM provider returns JSON with `answer` and `citations`.
6. The service validates that citations are a subset of `used_chunks`.

## Auth / Permission

There is no authentication, authorization, RBAC, or permission layer in the current codebase.

- Public app surface is the FastAPI shell plus the 3 RAG endpoints and `/health`.
- The only request-level metadata added by middleware is tracing/observability state such as `request_id` and latency.
- Internal-only file ingestion is exposed through scripts and `FileIngestionUseCase`, not through a separate auth-protected HTTP surface.

If auth is introduced later, it should stay in `src/tuesday/api/` or a dedicated app-shell boundary, not in `rag/domain/` or use-case business logic.

## Current Conventions

### Code and Structure

- Python 3.12+.
- `snake_case` for functions, variables, and modules.
- `PascalCase` for classes.
- Public functions use type hints.
- Keep modules small and focused.
- Preserve the boundary split inside `src/tuesday/rag/`.
- Do not import framework or provider SDK objects into `rag/domain/`, `*/use_case.py`, or `*/service.py`.
- Do not leak infrastructure/framework response objects outside `rag/infrastructure/`.

### Runtime and Config

- Runtime config is loaded through `RuntimeConfig.from_env()`.
- Environment prefix is `TUESDAY_*`; `.env` is also supported.
- The container validates config and runs startup checks before serving requests.
- PDF ingestion depends on `pdftotext`; startup behavior is controlled by `pdf_startup_check_mode`.

### Locked Behaviors

The following semantics are already reinforced by tests and should be preserved unless specs change:

- re-index behavior is replace-by-`document_id` within `index_name`
- `filters.tags` uses contains-any semantics
- generation returns `insufficient_context=True` without calling the LLM when context is missing or too weak
- citations must reference only `used_chunks`
- retrieval applies lexical reranking after vector-store lookup

### Documentation and Specs

- Read `docs.md` first before substantial work.
- Treat `docs.md` as the consolidated project reference.
- Treat the legacy `docs/` tree as migration/archive material only.

## Test / Build / Lint

### Setup

```bash
pip install -e '.[dev]'
```

### Run the API locally

```bash
python -m uvicorn tuesday.api.app:app --reload
```

### Tests

```bash
pytest
pytest tests/unit
pytest tests/api/test_health.py
python scripts/smoke_test.py
python scripts/benchmark_quality.py --iterations 5
```

### Lint and Type Check

Commands are implied by `pyproject.toml`:

```bash
ruff check src tests scripts
ruff format --check src tests scripts
pyright
```

### Build

There is no separate build pipeline in the repo. The package is installed in editable mode via setuptools:

```bash
pip install -e '.[dev]'
```

## Risky Areas

- `src/tuesday/runtime/container.py`
  Backend switching is centralized here. Changes can quietly affect provider selection, resilience wrappers, or startup checks.
- `src/tuesday/runtime/config.py`
  Config bounds and provider requirements are tightly validated and covered by tests; small changes can break runtime boot.
- `src/tuesday/rag/infrastructure/qdrant_vector_store.py`
  Real vector backend integration, collection shape, payload schema, and dense-vector conversion all live here.
- `src/tuesday/rag/infrastructure/file_vector_store.py`
  Persistence is file-backed and uses atomic replace; changes can affect local durability semantics.
- `src/tuesday/rag/infrastructure/file_document_parser.py`
  File parsing behavior, HTML extraction, and PDF subprocess integration are operationally fragile.
- `src/tuesday/rag/generation/context_policy.py`
  This is a deterministic guardrail for insufficient-context behavior. Small threshold changes can shift contract and regression results.
- `src/tuesday/rag/retrieval/ranking_policy.py`
  Post-retrieval lexical reranking influences user-visible ordering and regression baselines.
- `src/tuesday/shared/validation.py`
  Input, filter, and metadata rules are shared across public flows and are easy to break accidentally.

## How To Add a New Feature in Repo Style

1. Start with the consolidated reference.
   Read `docs.md`, then the relevant active feature spec artifacts, then `.specify/memory/constitution.md` if process rules matter.
2. Decide the correct boundary first.
   Put HTTP concerns in `api/`, dependency wiring in `runtime/`, business logic in `rag/*`, and SDK/storage details in `rag/infrastructure/`.
3. Extend domain-safe contracts before adapters.
   If a feature changes business behavior, update domain models, validation, ports, use cases, and services before touching adapters.
4. Keep API handlers thin.
   The router should translate request/response shapes and call a use case, nothing more.
5. Prefer deterministic tests at the narrowest scope.
   Use `tests/unit/` for domain/use-case rules, `tests/api/` for contracts, `tests/integration/` for adapters, and `tests/smoke/` only for happy-path flow checks.
6. Preserve locked semantics unless the spec explicitly changes them.
   Re-index policy, filter semantics, insufficient-context behavior, and citation validity are not casual refactor targets.
7. Update `docs.md` or the relevant active feature spec artifacts when semantics or config bounds change.
   Do not treat the legacy `docs/` tree as the current contract.
8. Keep changes surgical.
   Avoid repo-wide refactors or speculative abstraction. Match the existing style and naming.
