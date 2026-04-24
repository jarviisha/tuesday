---

description: "Task list for preserving core behavior while replacing the real vector-store adapter path"
---

# Tasks: Preserve Core Behavior with Infrastructure Adapter

**Input**: Design documents from `/specs/001-llamaindex-qdrant-adapter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are required for this feature because it changes infrastructure behavior tied to locked semantics and compatibility expectations.

**Organization**: Tasks are grouped by user story to keep each increment reviewable, safe to implement, and independently verifiable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `[US1]`, `[US2]`, `[US3]`)
- Every task includes a concrete file path

## Path Conventions

- Source code lives under `src/tuesday/`
- Tests live under `tests/`
- Feature artifacts live under `specs/001-llamaindex-qdrant-adapter/`

## Phase 1: Setup

**Purpose**: Capture the implementation boundary and make review/verification artifacts ready before code changes.

- [X] T001 Document the adapter replacement scope and compatibility targets in `specs/001-llamaindex-qdrant-adapter/plan.md`
- [X] T002 Create the executable task breakdown in `specs/001-llamaindex-qdrant-adapter/tasks.md`
- [X] T003 [P] Review current real-backend behavior and list exact assertions to preserve from `tests/integration/test_qdrant_vector_store.py`, `tests/api/test_contracts.py`, and `tests/api/test_error_mapping.py`

---

## Phase 2: Foundational

**Purpose**: Prepare shared prerequisites that block all user story work.

**⚠️ CRITICAL**: No user story implementation should start until this phase is complete.

- [X] T004 Add or update shared adapter test fixtures/helpers in `tests/integration/test_qdrant_vector_store.py` for replacement, filtering, and ordering scenarios
- [X] T005 [P] Add or update shared API compatibility assertions in `tests/api/test_contracts.py` for unchanged retrieval response shape and `applied_filters`
- [X] T006 [P] Add or update shared API failure-mapping assertions in `tests/api/test_error_mapping.py` for indexing and retrieval backend failures
- [X] T007 Verify the current runtime backend-selection assumptions in `src/tuesday/runtime/container.py` and `src/tuesday/runtime/config.py` so later changes stay minimal

**Checkpoint**: Shared compatibility assertions and runtime assumptions are explicit; user story work can proceed safely.

---

## Phase 3: User Story 1 - Preserve existing RAG behavior (Priority: P1) 🎯 MVP

**Goal**: Preserve public responses, locked semantics, and compatibility-sensitive behavior after the adapter refactor.

**Independent Test**: Existing index -> retrieve -> generate flows still return the same public shapes and preserve locked behaviors after the new adapter path is in place.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests first and confirm they fail against incomplete implementation.**

- [X] T008 [P] [US1] Extend replacement and empty-result compatibility coverage in `tests/integration/test_qdrant_vector_store.py`
- [X] T009 [P] [US1] Extend public contract preservation coverage in `tests/api/test_contracts.py`
- [X] T010 [P] [US1] Extend smoke coverage for the real-backend flow in `tests/smoke/test_qdrant_index_retrieve_generate.py`

### Implementation for User Story 1

- [X] T011 [US1] Refactor the real vector-store adapter entry path in `src/tuesday/rag/infrastructure/qdrant_vector_store.py` to preserve existing indexing and retrieval behavior
- [X] T012 [US1] Preserve runtime wiring for the real vector-store path in `src/tuesday/runtime/container.py`
- [X] T013 [US1] Apply only the minimal backend-selection or config adjustments needed in `src/tuesday/runtime/config.py`
- [X] T014 [US1] Verify no public response or orchestration code changes are required in `src/tuesday/rag/api/` and `src/tuesday/rag/*/use_case.py`; if none are needed, document that in `specs/001-llamaindex-qdrant-adapter/quickstart.md`

**Checkpoint**: The real adapter path is replaced and the public RAG behavior remains stable for the MVP compatibility flow.

---

## Phase 4: User Story 2 - Replace direct backend access with a controlled adapter (Priority: P2)

**Goal**: Replace direct backend-specific access while keeping all application layers dependent only on existing internal contracts.

**Independent Test**: Real-backend integration still works, supported filters still behave correctly, and no infrastructure-specific objects escape the infrastructure boundary.

### Tests for User Story 2 ⚠️

- [X] T015 [P] [US2] Add filter compatibility coverage for `tags`, `document_id`, `source_type`, and `language` in `tests/integration/test_qdrant_vector_store.py`
- [X] T016 [P] [US2] Add API assertions that supported filters and `applied_filters` remain compatible in `tests/api/test_contracts.py`

### Implementation for User Story 2

- [X] T017 [US2] Implement the controlled adapter mapping for backend reads and writes in `src/tuesday/rag/infrastructure/qdrant_vector_store.py`
- [X] T018 [US2] Add or refine infrastructure-only mapping helpers in `src/tuesday/rag/infrastructure/qdrant_vector_store.py` so backend-specific objects do not escape the adapter boundary
- [X] T019 [US2] Recheck runtime/container wiring in `src/tuesday/runtime/container.py` so capability services continue to depend only on the existing `VectorStore` contract

**Checkpoint**: Direct backend-specific access has been replaced by a controlled adapter path without boundary leakage.

---

## Phase 5: User Story 3 - Keep backend behavior stable for maintainers (Priority: P3)

**Goal**: Preserve backend-sensitive replacement, ordering, and failure behavior so future maintenance does not require revalidating the full core.

**Independent Test**: Maintainers can verify replace-by-document behavior, retrieval ordering, and backend failure mapping through focused integration/API/regression checks.

### Tests for User Story 3 ⚠️

- [X] T020 [P] [US3] Add retrieval-ordering compatibility checks in `tests/integration/test_qdrant_vector_store.py`
- [X] T021 [P] [US3] Add backend failure-mapping coverage for adapter-driven failures in `tests/api/test_error_mapping.py`
- [X] T022 [P] [US3] Add or update regression protection for locked semantics at risk in `tests/regression/test_retrieval_policy.py`

### Implementation for User Story 3

- [X] T023 [US3] Normalize backend failure translation inside `src/tuesday/rag/infrastructure/qdrant_vector_store.py` so existing application-level error mapping remains stable
- [X] T024 [US3] Verify retrieval ordering compatibility across backend lookup and rerank interaction by adjusting only adapter-return behavior in `src/tuesday/rag/infrastructure/qdrant_vector_store.py`
- [X] T025 [US3] Refresh compatibility notes and maintainer verification guidance in `specs/001-llamaindex-qdrant-adapter/quickstart.md`

**Checkpoint**: Backend-sensitive behavior remains stable and maintainers have explicit verification guidance.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final review, docs sync, and complete verification across stories.

- [X] T026 [P] Update consolidated documentation if compatibility notes changed in `docs.md`
- [X] T027 Run the focused verification commands documented in `specs/001-llamaindex-qdrant-adapter/quickstart.md` and record outcomes in `specs/001-llamaindex-qdrant-adapter/quickstart.md`
- [X] T028 Review the final diff for boundary preservation and remove any accidental broad refactor across `src/tuesday/runtime/`, `src/tuesday/rag/`, and `tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks all story implementation.
- **User Story 1 (Phase 3)**: Depends on Foundational; establishes the MVP compatibility path.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because the controlled adapter path builds on the replaced integration entry path.
- **User Story 3 (Phase 5)**: Depends on User Story 2 because behavior stabilization and failure translation depend on the final adapter path.
- **Polish (Phase 6)**: Depends on all story phases being complete.

### User Story Dependencies

- **US1**: First deliverable; proves public behavior remains stable after adapter replacement.
- **US2**: Extends US1 by tightening the infrastructure boundary and replacing direct backend-specific access fully.
- **US3**: Locks backend-sensitive maintenance behavior after the new adapter path is established.

### Within Each User Story

- Write the compatibility tests first and confirm they fail before implementation.
- Change the smallest infrastructure surface possible before touching runtime wiring.
- Re-run the story’s independent test before moving to the next story.

### Parallel Opportunities

- T003 can run in parallel with T001-T002.
- T005 and T006 can run in parallel after T004.
- In US1, T008-T010 can run in parallel.
- In US2, T015-T016 can run in parallel.
- In US3, T020-T022 can run in parallel.
- T026 and T028 can run in parallel after T027 has the verification outcome ready.

---

## Parallel Example: User Story 1

```bash
# Launch US1 test work together:
Task: "Extend replacement and empty-result compatibility coverage in tests/integration/test_qdrant_vector_store.py"
Task: "Extend public contract preservation coverage in tests/api/test_contracts.py"
Task: "Extend smoke coverage for the real-backend flow in tests/smoke/test_qdrant_index_retrieve_generate.py"
```

## Parallel Example: User Story 2

```bash
# Launch US2 test work together:
Task: "Add filter compatibility coverage for tags, document_id, source_type, and language in tests/integration/test_qdrant_vector_store.py"
Task: "Add API assertions that supported filters and applied_filters remain compatible in tests/api/test_contracts.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 compatibility checks together:
Task: "Add retrieval-ordering compatibility checks in tests/integration/test_qdrant_vector_store.py"
Task: "Add backend failure-mapping coverage for adapter-driven failures in tests/api/test_error_mapping.py"
Task: "Add or update regression protection for locked semantics at risk in tests/regression/test_retrieval_policy.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup.
2. Complete Foundational compatibility assertions.
3. Complete User Story 1.
4. Stop and validate the preserved public behavior before continuing.

### Incremental Delivery

1. Establish compatibility assertions and runtime assumptions.
2. Replace the adapter entry path while preserving current behavior (US1).
3. Tighten the controlled adapter boundary and remove direct backend-specific access (US2).
4. Lock down replacement, ordering, and failure stability for maintainers (US3).
5. Finish with docs sync and focused verification.

### Suggested MVP Scope

- Deliver **User Story 1** first.
- This is the smallest safe slice because it proves the refactor can preserve public behavior before deeper adapter cleanup work proceeds.

---

## Notes

- All tasks follow the checklist format: checkbox, task ID, optional `[P]`, required story label in story phases, and explicit file path.
- Each story is reviewable as a small increment with matching tests.
- The task order is intentionally conservative to reduce regression risk in a locked-semantics codebase.
