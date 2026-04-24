<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
  - Template Principle 1 -> I. Preserve Existing Architecture
  - Template Principle 2 -> II. Minimal Diff Delivery
  - Template Principle 3 -> III. Tests for Changed Behavior
  - Template Principle 4 -> IV. Public Contract and Schema Stability
  - Template Principle 5 -> V. Follow Current Conventions
- Added sections:
  - Operational Guardrails
  - Delivery Workflow
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ updated .specify/templates/plan-template.md
  - ✅ updated .specify/templates/spec-template.md
  - ✅ updated .specify/templates/tasks-template.md
- Follow-up TODOs:
  - None
-->
# Tuesday Constitution

## Core Principles

### I. Preserve Existing Architecture
All feature work MUST preserve the current `src/tuesday/` architecture and the
existing boundary split in `src/tuesday/rag/`: `api/`, `domain/`, `ingestion/`,
`retrieval/`, `generation/`, `infrastructure/`, and `evaluation/`. Business
rules MUST remain in domain, use-case, or service modules. Framework code,
provider SDKs, storage SDKs, and transport details MUST stay outside
`rag/domain/`, `*/use_case.py`, and `*/service.py`. The removed
`src/tuesday_rag/` shim MUST NOT be reintroduced. Rationale: the repo is
already organized around a capability-oriented ports-and-adapters design, and
feature work must extend that design rather than erode it.

### II. Minimal Diff Delivery
Changes MUST be surgical and limited to the files and lines required for the
requested outcome. Feature work MUST NOT include broad refactors, speculative
abstractions, opportunistic renames, or repository-wide cleanup unless an
explicit spec requires them. When multiple interpretations are possible,
assumptions MUST be stated before substantial implementation. Rationale: this
project values predictable delivery in a brownfield codebase, and small diffs
reduce regression risk and review cost.

### III. Tests for Changed Behavior
Any change to behavior, semantics, config bounds, adapter behavior, or error
mapping MUST include verification in the narrowest relevant test scope. Unit
tests MUST cover domain and use-case rules; API tests MUST cover HTTP contract
changes; integration tests MUST cover adapter and persistence changes; smoke or
regression tests MUST be updated when end-to-end baselines or locked semantics
change. A behavior change without a test or equivalent verifiable check is not
complete. Rationale: the codebase already locks important semantics through
tests, and feature work must preserve that discipline.

### IV. Public Contract and Schema Stability
Public HTTP API shapes, error semantics, and persisted schema expectations MUST
remain backward compatible unless the active spec explicitly requires a change.
If a feature changes a public API contract, retrieval/generation semantics, or
storage schema expectations, the spec MUST say so directly and the change MUST
update active docs and affected tests in the same work. Internal file-ingestion
flows and backend selection MAY evolve, but they MUST NOT silently alter the
public contract. Rationale: Tuesday is designed to swap internals without
breaking callers.

### V. Follow Current Conventions
All new work MUST follow current repository conventions: Python 3.12+, 4-space
indentation, type hints on public functions, `snake_case` for functions and
modules, `PascalCase` for classes, English for code/tests/commits/comments, and
targeted documentation updates based on `docs.md`, relevant active feature spec
artifacts, and then `.specify/memory/constitution.md` when process rules are in
scope. New work MUST pass the lint and type-check configuration in
`pyproject.toml`. Rationale: repo consistency is a quality constraint, not a
style preference.

## Operational Guardrails

- Feature planning MUST identify the affected architectural boundary before code
  changes begin.
- Runtime composition belongs in `src/tuesday/runtime/`; request orchestration
  belongs in `src/tuesday/api/`; shared input validation belongs in
  `src/tuesday/shared/`; capability logic belongs in `src/tuesday/rag/`.
- Existing locked semantics such as replace-by-document reindexing, tags
  contains-any filtering, insufficient-context handling, citation validity, and
  deterministic reranking MUST be treated as stable unless an explicit active
  spec changes them.
- The legacy `docs/` tree is reference-only migration/archive material and MUST
  NOT be treated as the current behavioral contract.

## Delivery Workflow

- Before substantial implementation, define concrete success criteria and state
  any material assumptions.
- Read docs in this order when clarification is needed:
  `docs.md`, then the relevant active feature spec artifacts, then
  `.specify/memory/constitution.md` when process rules matter.
- When behavior or contract changes, update the corresponding tests and active
  documentation in the same change.
- Commits MUST use conventional prefixes: `feat:`, `fix:`, `refactor:`,
  `chore:`, `docs:`, `test:`, `build:`, or `ci:`.
- Pull requests MUST summarize the behavior change and list the verification
  commands that were run.

## Governance

This constitution is the default authority for engineering work in this
repository. Plans, specs, tasks, reviews, and implementation changes MUST pass
the Constitution Check before work proceeds. Amendments MUST be made by
updating this file together with any affected Spec Kit templates or guidance
documents. Versioning follows semantic versioning for governance:

- MAJOR for incompatible principle removals or redefinitions.
- MINOR for new principles, new mandatory sections, or materially stronger
  governance.
- PATCH for clarifications that do not change expected engineering behavior.

Compliance review is required in planning and implementation review. Any
constitution violation MUST be explicitly justified in the relevant plan or
spec, including why a simpler compliant approach was rejected.

**Version**: 1.0.0 | **Ratified**: 2026-04-24 | **Last Amended**: 2026-04-24
