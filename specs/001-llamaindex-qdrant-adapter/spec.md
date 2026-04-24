# Feature Specification: Preserve Core Behavior with Infrastructure Adapter

**Feature Branch**: `[001-llamaindex-qdrant-adapter]`  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "Hoàn thiện core behavior trên kiến trúc hiện có. Chỉ thêm LlamaIndex ở infrastructure/ nếu nó giúp giảm code adapter hoặc tận dụng integration sẵn có. Không đổi public contract, domain model, retrieval/generation semantics đã khóa. Refactor tối thiếu để thay qdarnt-client trực tiếp bằng một adapter dựa trên llamaindex nhưng vẫn giữ nguyên boundary hiện tại"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve existing RAG behavior (Priority: P1)

As a platform maintainer, I need the RAG core to keep returning the same
observable behavior after the vector-store adapter refactor so that current
clients and regression baselines remain valid.

**Why this priority**: The project already has locked API and semantic
expectations. Preserving them is the non-negotiable condition for any internal
acceleration work.

**Independent Test**: Run the existing index, retrieve, and generate flows
against the refactored adapter path and confirm that public responses, error
mapping, and locked semantics remain unchanged.

**Acceptance Scenarios**:

1. **Given** an indexed document set and an existing client request flow,
   **When** the core is run after the refactor, **Then** the public request and
   response shapes remain unchanged.
2. **Given** locked retrieval and generation semantics, **When** regression and
   contract tests are executed after the refactor, **Then** the system preserves
   re-index behavior, tag filtering behavior, insufficient-context handling, and
   citation validity.

---

### User Story 2 - Replace direct backend access with a controlled adapter (Priority: P2)

As a platform maintainer, I need the real vector-store integration to move from
direct backend-specific access to a controlled infrastructure adapter path so
that the project can use the approved integration layer without spreading
coupling through the codebase.

**Why this priority**: The approved feature goal is not a general cleanup. It is
the minimum refactor needed to replace the current direct integration path while
preserving the existing architecture and locked behavior.

**Independent Test**: Verify that the real vector-store behavior remains
compatible after replacing the direct integration path and that the rest of the
application continues to depend only on the existing internal contracts.

**Acceptance Scenarios**:

1. **Given** the existing application architecture, **When** the real
   vector-store integration path is replaced, **Then** domain, use case,
   service, API, and runtime boundaries continue to use the same internal
   contracts.
2. **Given** the approved infrastructure adapter path, **When** backend
   interactions occur, **Then** infrastructure-specific objects do not escape
   the infrastructure boundary.

---

### User Story 3 - Keep backend behavior stable for maintainers (Priority: P3)

As a project owner, I need the real vector-store behavior to remain stable for
maintainers after the adapter replacement so that future backend maintenance can
continue without revalidating the entire core.

**Why this priority**: Delivery speed matters, but only if the project avoids
unnecessary architectural churn and keeps backend-sensitive behavior stable.

**Independent Test**: Exercise backend-sensitive indexing and retrieval cases
and confirm that maintainers can verify replacement behavior, filter behavior,
ordering behavior, and failure behavior through existing test surfaces.

**Acceptance Scenarios**:

1. **Given** an existing indexed document, **When** it is indexed again into the
   same logical index after the adapter replacement, **Then** replacement
   behavior remains consistent for maintainers.
2. **Given** an existing retrieval request with supported filters, **When** the
   request is executed after the adapter replacement, **Then** returned chunks,
   applied filters, and result ordering remain compatible with the current
   baseline.

---

### Edge Cases

- What happens when the infrastructure adapter cannot reach the backend or
  returns malformed data during indexing or retrieval?
- How does the system handle missing collections, empty query results, or
  replacement of an existing document within the same index?
- How does the system preserve `tags` filtering with contains-any semantics
  after the adapter replacement?
- How does the system preserve post-retrieval ordering after lexical reranking
  and `top_k` trimming?
- How does the system preserve existing error surfaces when the backend times
  out, rejects requests, or returns unusable payloads?
- How does the system preserve `applied_filters` so they continue to reflect the
  filters actually accepted and used by the retrieval flow?
- This feature preserves existing public API and persisted schema behavior; no
  contract or schema change is in scope.
- The feature must not alter locked semantics for replace-by-document behavior,
  tag filtering, insufficient-context handling, citation validity, or
  deterministic result ordering.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preserve existing public index, retrieve, and generate
  request and response shapes throughout this feature.
- **FR-002**: System MUST preserve existing domain models and capability-layer
  contracts throughout this feature.
- **FR-003**: System MUST preserve locked core semantics for re-index behavior,
  supported filters, insufficient-context handling, and citation validity.
- **FR-004**: System MUST replace the current direct real vector-store
  integration path with the approved controlled infrastructure adapter path
  without requiring changes to domain, use case, service, or API behavior.
- **FR-005**: System MUST prevent infrastructure-specific object types from
  leaking outside the infrastructure boundary.
- **FR-006**: System MUST support the current real vector-store backend behavior
  used by the project for indexing, replacement, retrieval, and filtering.
- **FR-007**: System MUST retain existing configuration-driven backend selection
  behavior for the supported real vector-store path.
- **FR-008**: System MUST include verification for any changed infrastructure
  behavior in the narrowest relevant test scope, including adapter-level and
  regression-sensitive checks.
- **FR-009**: System MUST preserve `filters.tags` contains-any semantics for the
  real vector-store path after the adapter replacement.
- **FR-010**: System MUST preserve existing retrieval result ordering after
  vector-store lookup, lexical reranking, and `top_k` trimming.
- **FR-011**: System MUST preserve existing retrieval `applied_filters`
  behavior for supported filter inputs.
- **FR-012**: System MUST preserve existing backend failure mapping behavior for
  indexing and retrieval failures exposed through the current application
  surfaces.

### Key Entities *(include if feature involves data)*

- **Indexed Chunk Record**: A persisted searchable unit derived from a source
  document and associated with an index, document identity, chunk identity, text
  content, scoreable vector data, and filterable metadata.
- **Infrastructure Adapter Mapping**: The translation boundary between internal
  chunk-oriented records and backend-specific storage or retrieval structures.
- **Compatibility Baseline**: The set of current observable behaviors that must
  remain stable, including contract responses, error surfaces, and locked
  semantics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Existing API contract and regression tests covering the current
  RAG core behavior pass without requiring public response shape changes.
- **SC-002**: The refactored core preserves all currently locked retrieval and
  generation semantics in automated verification.
- **SC-003**: Existing automated checks for replacement behavior, supported
  filters, retrieval ordering, and backend failure handling pass after the
  adapter replacement.
- **SC-004**: The change is limited to the infrastructure integration path and
  directly related wiring, documentation, and tests, with no broad refactor of
  unrelated capability layers.

## Assumptions

- The current public API shapes and persisted schema expectations remain
  unchanged for this feature.
- Existing capability boundaries remain authoritative and are not being
  redesigned by this work.
- The current real vector-store behavior already represents the expected product
  behavior and must be preserved rather than redefined.
- The approved adapter replacement for this feature uses the infrastructure-only
  integration path described in the feature request rather than keeping the
  current direct backend-specific access path.
