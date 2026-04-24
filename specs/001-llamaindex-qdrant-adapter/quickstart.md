# Quickstart: Preserve Core Behavior with Infrastructure Adapter

## Goal

Verify that the adapter replacement preserves the current RAG core behavior
without changing public contracts or locked semantics.

## Expected Impact Before Coding

### Files / modules likely to be affected

- `src/tuesday/rag/infrastructure/qdrant_vector_store.py`
- `src/tuesday/runtime/container.py`
- `src/tuesday/runtime/config.py` only if existing backend wiring requires a
  minimal compatibility adjustment
- `tests/integration/test_qdrant_vector_store.py`
- `tests/api/test_contracts.py`
- `tests/api/test_error_mapping.py`
- `tests/smoke/test_qdrant_index_retrieve_generate.py`
- `tests/regression/` only if an existing locked behavior needs explicit
  regression protection
- `docs.md` and this feature directory if compatibility notes need refresh

### Data / API changes

- No public API changes are expected.
- No domain model changes are expected.
- No new persisted schema or metadata shape is intended.
- Internal adapter mapping behavior may change, but the observable compatibility
  surface must remain stable.

### Tests to add or update

- Update integration coverage for adapter replacement, including:
  - replace-by-document behavior
  - missing collection / empty result behavior
  - `tags` contains-any filtering
  - `document_id`, `source_type`, and `language` filtering
  - retrieval ordering compatibility
- Update API/error tests if backend failure mapping needs explicit protection.
- Re-run smoke and regression flows that exercise index -> retrieve -> generate.

### Technical risks

- Adapter mapping may subtly change filter semantics or payload shape.
- Backend-native scoring may alter pre-rerank ordering enough to affect final
  compatibility if rerank assumptions are too weak.
- Failure translation may drift if backend exceptions no longer map cleanly to
  existing application errors.
- Minimal runtime wiring changes can still affect backend selection behavior.

## Verification Steps

1. Run targeted integration tests for the real vector-store path.
2. Run API contract and error-mapping tests for affected flows.
3. Run smoke coverage for index -> retrieve -> generate.
4. Run regression coverage for locked semantics if affected.

## Implementation Notes

- The real Qdrant adapter path now goes through
  `src/tuesday/rag/infrastructure/llamaindex_qdrant_bridge.py` and keeps
  `QdrantVectorStore` as the existing infrastructure entry point.
- Runtime wiring in `src/tuesday/runtime/container.py` and config defaults in
  `src/tuesday/runtime/config.py` were intentionally left unchanged; the
  backend selection contract remains `vector_store_backend="qdrant"`.
- No public API, domain model, retrieval orchestration, or generation
  orchestration code changes were required in `src/tuesday/rag/api/` or
  `src/tuesday/rag/*/use_case.py`.
- The bridge prefers real `llama-index-core` types when they import cleanly.
  In the current local Python 3.14 environment, importing the upstream package
  raises a compatibility error, so the bridge falls back to a local
  infrastructure-only compatibility shim with the same minimal type surface.
  This keeps the adapter boundary aligned with the spec without leaking
  framework objects outside `infrastructure/`.

## Verification Outcomes

### Commands Run

```bash
./.venv/bin/python -m pytest tests/api/test_contracts.py tests/api/test_error_mapping.py tests/regression/test_retrieval_policy.py -q
./.venv/bin/python -m pytest tests/integration/test_qdrant_vector_store.py tests/smoke/test_qdrant_index_retrieve_generate.py tests/unit/test_runtime_container.py -q
```

### Results

- `tests/api/test_contracts.py`, `tests/api/test_error_mapping.py`, and
  `tests/regression/test_retrieval_policy.py`: `19 passed`
- `tests/integration/test_qdrant_vector_store.py`,
  `tests/smoke/test_qdrant_index_retrieve_generate.py`, and
  `tests/unit/test_runtime_container.py`: `14 passed`

## Completion Check

The feature is ready for task breakdown when maintainers can point to a bounded
set of infrastructure files, no public API change, explicit test coverage, and
a clear risk list tied to preserved behaviors.
