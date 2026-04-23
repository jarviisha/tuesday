# Repository Guidelines

## Project Structure & Module Organization
The codebase uses a `src/` layout. The application shell lives in `src/tuesday/`, with `api/` for the FastAPI app shell, `runtime/` for config and container wiring, `shared/` for cross-capability helpers, and capability modules such as `rag/`. Inside `src/tuesday/rag/`, code is organized by boundary: `api/` for the RAG router and schemas, `domain/` for models, ports, and errors, `ingestion/`, `retrieval/`, and `generation/` for use cases and services, `infrastructure/` for adapters, and `evaluation/` for quality assets. Tests live under `tests/unit/` and `tests/api/`. Design and implementation notes are in `docs/`, and prompt drafts are in `prompt/`.

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
Follow the existing Python style: 4-space indentation, type hints on public functions, and small focused modules. Use `snake_case` for functions, variables, and module names, `PascalCase` for classes, and explicit names such as `IngestionUseCase` or `test_generation_returns_citations`. Keep architectural boundaries intact: API code should orchestrate requests, while business rules stay in `application/` and `domain/`.

## Language Rules
Use English across the codebase by default, including source code, tests, commit messages, comments, identifiers, and non-spec documentation.

Exceptions:

- specification documents under `docs/` may use Vietnamese with full diacritics when the document is part of the project's spec, planning, checklist, review, or decision-log flow. For these spec documents, do not write Vietnamese without diacritics.
- files under `prompt/` are not constrained by this language rule.
- input data, fixtures, sample payloads, benchmark cases, and other domain content are not constrained by the English-by-default rule. Unless a test or integration scenario explicitly requires another language, prefer Vietnamese for these inputs to match the project docs and evaluation baseline.

## Agent Working Rules
Before implementing, state assumptions explicitly when they matter. If multiple interpretations are possible, surface them instead of silently picking one. Prefer the simplest approach that satisfies the request, and avoid speculative abstractions, configurability, or extra features that were not asked for.

Keep changes surgical. Touch only the files and lines needed for the task, match the existing style, and do not refactor unrelated code. If you notice adjacent issues that are out of scope, mention them separately instead of folding them into the same change.

Define concrete success criteria before making substantial changes. For bug fixes or behavior changes, prefer a test or another verifiable check that demonstrates the problem and confirms the result. For multi-step work, use a short plan with a verification step for each major change.

Respect the project's lint rules as configured in `pyproject.toml` for every code change. New or modified code should pass the configured lint checks, and agents should avoid introducing style or import-order violations that conflict with the repository's lint setup.

## Testing Guidelines
`pytest` is the active test framework, with `httpx` used for API tests. Add unit tests next to the relevant behavior in `tests/unit/`, and HTTP contract tests in `tests/api/`. Name files `test_<feature>.py` and test functions `test_<expected_behavior>()`. Prefer deterministic tests with fake ports for use-case coverage; reserve integration-style behavior for adapters and API wiring.

## Commit & Pull Request Guidelines
This repository has no established commit history yet, so use short imperative commit messages, for example: `Add retrieval filter validation`. Keep commits scoped to one change. PRs should summarize the behavior change, list the commands run (`pytest`, targeted tests, manual API checks), and include request/response examples when endpoint behavior changes.

## Configuration & Runtime Notes
Runtime defaults are defined in `src/tuesday/runtime/config.py`. When changing limits such as chunk size, overlap, or retrieval bounds, update tests alongside the code so the spec stays locked.
