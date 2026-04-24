# Repository Guidelines

## Project Structure & Module Organization
The codebase uses a `src/` layout and the canonical package is `src/tuesday/`. The application shell lives in `src/tuesday/api/` and `src/tuesday/runtime/`, shared helpers live in `src/tuesday/shared/`, and the current capability is `src/tuesday/rag/`. Inside `src/tuesday/rag/`, keep the boundary split intact: `api/` for router and schemas, `domain/` for models, ports, and errors, `ingestion/`, `retrieval/`, and `generation/` for use cases and services, `infrastructure/` for adapters, and `evaluation/` for quality assets. The legacy `src/tuesday_rag/` shim has been removed and must not be reintroduced.

Tests are organized by scope under `tests/` (`unit/`, `api/`, `integration/`, `smoke/`, `regression/`, plus shared fixtures). Operational scripts live in `scripts/`, real sample documents live in `examples/`, and benchmark artifacts live in `benchmarks/`.

Documentation workflow is consolidated into a single file:

- `docs.md` is the consolidated project reference and should be read before substantial implementation work.
- The legacy `docs/` tree may still exist temporarily as migration input/archive material, but it is no longer the workflow source of truth.

## Build, Test, and Development Commands
Create or reuse a Python 3.12+ environment, then install the package in editable mode:

```bash
pip install -e '.[dev]'
```

Run the test suite:

```bash
pytest
```

Run a focused test target when iterating:

```bash
pytest tests/unit
pytest tests/api/test_health.py
```

Start the local API server with auto-reload:

```bash
python -m uvicorn tuesday.api.app:app --reload
```

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, type hints on public functions, and small focused modules. Use `snake_case` for functions, variables, and module names, `PascalCase` for classes, and explicit names such as `IngestionUseCase` or `test_generation_returns_citations`.

Keep architectural boundaries intact: API code should orchestrate requests, runtime should compose dependencies, and business rules should stay in capability use cases, services, and `domain/`. Do not import framework or provider SDK objects into `src/tuesday/rag/domain/`, `src/tuesday/rag/*/use_case.py`, or `src/tuesday/rag/*/service.py`. Do not leak infrastructure/framework response objects outside `infrastructure/`.

## Language Rules
Use English across the codebase by default, including source code, tests, commit messages, comments, identifiers, and non-spec documentation.

Exceptions:

- the consolidated `docs.md` file and feature specification artifacts may use Vietnamese with full diacritics when the content is part of the project's spec, planning, checklist, review, or decision-log flow. For these documents, do not write Vietnamese without diacritics.
- files under `prompt/` are not constrained by this language rule.
- input data, fixtures, sample payloads, benchmark cases, and other domain content are not constrained by the English-by-default rule. Unless a test or integration scenario explicitly requires another language, prefer Vietnamese for these inputs to match the project docs and evaluation baseline.

## Agent Working Rules
Before implementing, state assumptions explicitly when they matter. If multiple interpretations are possible, surface them instead of silently picking one. Prefer the simplest approach that satisfies the request, and avoid speculative abstractions, configurability, or extra features that were not asked for.

Keep changes surgical. Touch only the files and lines needed for the task, match the existing style, and do not refactor unrelated code. If you notice adjacent issues that are out of scope, mention them separately instead of folding them into the same change.

Define concrete success criteria before making substantial changes. For bug fixes or behavior changes, prefer a test or another verifiable check that demonstrates the problem and confirms the result. For multi-step work, use a short plan with a verification step for each major change.

For documentation-driven work, resolve questions in this order: `docs.md`, then the relevant active feature spec artifacts, then `.specify/memory/constitution.md` when process rules matter. Treat the legacy `docs/` tree as migration/archive background only unless the task is explicitly about documentation consolidation history.

Respect the project's lint rules as configured in `pyproject.toml` for every code change. New or modified code should pass the configured lint checks, and agents should avoid introducing style or import-order violations that conflict with the repository's lint setup.

## Testing Guidelines
`pytest` is the active test framework, with `httpx` used for API tests. Add tests in the narrowest relevant scope: `tests/unit/` for domain, use-case, script, and config behavior; `tests/api/` for HTTP contract and app-shell behavior; `tests/integration/` for adapters and persistence; `tests/smoke/` for end-to-end happy-path validation; and `tests/regression/` for quality/baseline protection. Name files `test_<feature>.py` and test functions `test_<expected_behavior>()`.

Prefer deterministic tests with fake ports for use-case coverage; reserve integration-style behavior for adapters, persistence, and API wiring. When changing locked semantics, config bounds, or API contract behavior, update the corresponding tests and the active docs together.

## Commit & Pull Request Guidelines
Use conventional-style commit prefixes for every commit message: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `build:`, or `ci:`. Keep the subject short, imperative, and scoped to one change, for example: `feat: add retrieval filter validation` or `fix: preserve replace-document semantics in qdrant adapter`. Avoid free-form commit subjects without one of these prefixes.

PRs should summarize the behavior change, list the commands run (`pytest`, targeted tests, manual API checks), and include request/response examples when endpoint behavior changes.

## Configuration & Runtime Notes
Runtime defaults are defined in `src/tuesday/runtime/config.py` and are expected to be loaded through the runtime/container path. When changing limits such as chunk size, overlap, retrieval bounds, provider selection, or startup checks, update tests alongside the code so the spec stays locked.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read [specs/001-llamaindex-qdrant-adapter/plan.md](/home/jarviisha/development/tuesday/specs/001-llamaindex-qdrant-adapter/plan.md)
<!-- SPECKIT END -->
