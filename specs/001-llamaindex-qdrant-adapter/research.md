# Research: Preserve Core Behavior with Infrastructure Adapter

## Decision 1: Keep the refactor inside `src/tuesday/rag/infrastructure/`

- **Decision**: Restrict the adapter replacement to the infrastructure layer,
  plus the minimum runtime wiring and tests needed to preserve compatibility.
- **Rationale**: The repository constitution and current codebase both require
  the existing `api -> runtime -> rag capability -> domain ports ->
  infrastructure adapters` dependency direction to remain intact. The feature
  explicitly excludes public contract, domain model, and capability semantic
  changes.
- **Alternatives considered**:
  - Refactor use cases and services to depend on a new orchestration layer:
    rejected because it violates the minimal-diff and preserve-architecture
    rules.
  - Rework the public API or domain contracts to match a new backend:
    rejected because the feature explicitly forbids it.

## Decision 2: Replace direct backend-specific access with a controlled adapter path

- **Decision**: Replace the current direct real vector-store integration path
  with a controlled adapter path while keeping the existing internal
  `VectorStore` contract stable.
- **Rationale**: The desired outcome is backend decoupling without capability
  layer churn. The stable internal port already exists and should continue to be
  the only dependency used by ingestion and retrieval orchestration.
- **Alternatives considered**:
  - Keep direct backend-specific access and only tidy the implementation:
    rejected because it does not satisfy the feature goal of replacing the
    direct integration path.
  - Introduce a second application-facing contract for the new adapter:
    rejected because it broadens scope and increases migration risk.

## Decision 3: Preserve all currently locked semantics as explicit compatibility targets

- **Decision**: Treat replace-by-document behavior, `filters.tags`
  contains-any semantics, `applied_filters`, retrieval ordering after reranking,
  insufficient-context behavior, citation validity, and backend failure mapping
  as mandatory compatibility targets.
- **Rationale**: These behaviors are already reinforced by tests and are called
  out in project memory and governance. The adapter replacement is acceptable
  only if these semantics remain unchanged.
- **Alternatives considered**:
  - Preserve only public request and response shapes:
    rejected because this would miss behavior regressions that clients and
    maintainers already depend on.
  - Rebaseline ranking or failure semantics as part of the refactor:
    rejected because the feature does not authorize semantic changes.

## Decision 4: No data model or public API change is in scope

- **Decision**: Keep external request/response shapes, domain models, metadata
  schema expectations, and configuration surface behavior stable.
- **Rationale**: The spec and constitution both state that public contracts and
  persisted schema expectations must not change unless explicitly authorized.
- **Alternatives considered**:
  - Add new request fields or backend-specific response metadata:
    rejected because it would be a public contract change.
  - Change stored metadata shape to match backend-native structures:
    rejected because it would increase migration risk and leak storage concerns.

## Decision 5: Concentrate verification in integration, API, smoke, and regression layers

- **Decision**: Add or update tests primarily in `tests/integration/`,
  `tests/api/`, `tests/smoke/`, and `tests/regression/`, with targeted unit
  tests only where adapter mapping logic becomes complex enough to justify them.
- **Rationale**: The feature risk is concentrated in backend behavior,
  compatibility, and boundary preservation. Those risks are best caught at the
  adapter and contract layers.
- **Alternatives considered**:
  - Rely only on unit tests for the new adapter:
    rejected because adapter compatibility depends on end-to-end behavior.
  - Expand smoke coverage into a larger system rewrite:
    rejected because the feature must remain narrowly scoped.
