# Implementation Plan: Preserve Core Behavior with Infrastructure Adapter

**Branch**: `[001-llamaindex-qdrant-adapter]` | **Date**: 2026-04-24 | **Spec**: [spec.md](/home/jarviisha/development/tuesday/specs/001-llamaindex-qdrant-adapter/spec.md)
**Input**: Feature specification from `/specs/001-llamaindex-qdrant-adapter/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Replace the current direct real vector-store integration path with a controlled
infrastructure adapter path while preserving existing public API shapes, domain
contracts, locked retrieval/generation semantics, and backend failure mapping.
The work stays bounded to infrastructure, minimal runtime wiring, and
compatibility-focused test updates.

## Expected Impact Before Coding

**Files / modules likely to be affected**:

- `src/tuesday/rag/infrastructure/qdrant_vector_store.py`
- `src/tuesday/runtime/container.py`
- `src/tuesday/runtime/config.py` if minimal backend wiring adjustments are
  required
- `tests/integration/test_qdrant_vector_store.py`
- `tests/api/test_contracts.py`
- `tests/api/test_error_mapping.py`
- `tests/smoke/test_qdrant_index_retrieve_generate.py`
- `tests/regression/*` only where locked semantics need explicit protection
- `docs.md` and `specs/001-llamaindex-qdrant-adapter/*`

**Data / API changes**:

- No public API change is planned.
- No domain model change is planned.
- No persisted schema change is planned.
- Internal adapter mapping changes are allowed only if the observable behavior
  remains compatible.

**Tests to add or update**:

- Integration tests for adapter replacement behavior and filter compatibility.
- API tests for contract stability and indexing/retrieval failure mapping.
- Smoke coverage for index -> retrieve -> generate through the real backend.
- Regression checks for any locked semantics at risk from the adapter change.

**Technical risks**:

- adapter mapping drift for metadata and filters
- retrieval ordering drift after backend lookup and rerank interaction
- backend exception translation drift
- runtime/backend-selection regressions from minimal wiring changes

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic, qdrant-client, pytest, ruff, pyright  
**Storage**: Qdrant real vector-store backend, file-backed vector store, in-memory vector store  
**Testing**: pytest with unit, api, integration, smoke, and regression scopes  
**Target Platform**: Linux-like server/runtime environment for a Python web service  
**Project Type**: capability-oriented web service with internal scripts  
**Performance Goals**: Preserve current behavior and compatibility without degrading locked smoke/regression flows  
**Constraints**: No public API change, no domain model change, no broad refactor, preserve locked semantics and infrastructure boundaries  
**Scale/Scope**: Narrow infrastructure refactor limited to adapter replacement, minimal runtime wiring, and compatibility verification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Preserve the existing `src/tuesday/` architecture and keep changes inside the
  correct boundary (`api`, `runtime`, `shared`, `rag/*`, `infrastructure`).
- Keep the change set minimal; broad refactors require explicit spec
  justification.
- Identify any public API, persisted schema, config-bound, or locked-semantic
  change; if any are required, the active spec must say so explicitly.
- Define the verification strategy at the narrowest relevant test scope for any
  changed behavior.
- List active docs that must be updated if behavior, contract, or bounds change.

**Gate status before design**: PASS

- Boundary preservation: satisfied by infrastructure-only scope plus minimal runtime wiring.
- Minimal diff: satisfied by limiting planned code changes to adapter and compatibility paths.
- Public contract/schema stability: satisfied; no public API or data model change is authorized.
- Verification strategy: satisfied; integration, API, smoke, and regression coverage identified.
- Documentation impact: limited to `docs.md` and feature artifacts if compatibility notes change.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/tuesday/
├── api/
├── runtime/
├── shared/
└── rag/
    ├── api/
    ├── domain/
    ├── ingestion/
    ├── retrieval/
    ├── generation/
    ├── infrastructure/
    └── evaluation/

tests/
├── api/
├── integration/
├── smoke/
├── regression/
└── unit/

specs/001-llamaindex-qdrant-adapter/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

**Structure Decision**: Keep the existing single-project capability-oriented
layout. Restrict implementation changes to `src/tuesday/rag/infrastructure/`,
minimal runtime wiring in `src/tuesday/runtime/`, and the narrowest relevant
test directories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
