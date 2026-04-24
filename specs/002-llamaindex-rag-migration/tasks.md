---
description: "Task list for LlamaIndex End-to-End RAG Migration"
---

# Tasks: LlamaIndex End-to-End RAG Migration

**Input**: Design documents from `specs/002-llamaindex-rag-migration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Include test tasks whenever the feature changes behavior, semantics,
config bounds, API contracts, persistence behavior, or other locked rules.
Tests are not optional for changed behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Python runtime prerequisite and dependency pinning — blocks all implementation work.

- [ ] T001 Install Python 3.12 via `pyenv install 3.12.9`, set `pyenv local 3.12.9`, recreate `.venv` with `python3.12 -m venv .venv && pip install -e '.[dev]'` (R-001)
- [ ] T002 Update `pyproject.toml` — add `llama-index-core>=0.14,<0.15`, `llama-index-vector-stores-qdrant>=0.4,<1.0`, `llama-index-embeddings-openai>=0.3,<1.0`, `llama-index-embeddings-gemini>=0.3,<1.0`, `llama-index-embeddings-azure-openai>=0.3,<1.0`, `llama-index-llms-openai>=0.4,<1.0`, `llama-index-llms-gemini>=0.4,<1.0`, `llama-index-llms-azure-openai>=0.3,<1.0`; remove obsolete `llama-index-core>=0.14,<0.15` duplicate if present; reinstall deps (R-002)
- [ ] T003 Verify LlamaIndex 0.14.x imports cleanly: run `python -c "from llama_index.core import VectorStoreIndex, Settings; from llama_index.vector_stores.qdrant import QdrantVectorStore; print('ok')"` inside `.venv` and confirm no pydantic.v1 errors

**Checkpoint**: Python 3.12 + LlamaIndex 0.14.x confirmed importable — implementation can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Remove obsolete files and rename config fields — must be complete before any user story begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Delete `src/tuesday/rag/infrastructure/llamaindex_qdrant_bridge.py` — the LlamaIndex bridge shim is superseded by the full LlamaIndex adapter; update any imports that reference it
- [ ] T005 [P] Delete `src/tuesday/rag/infrastructure/http_client.py` — custom urllib HTTP layer removed as all providers migrate to LlamaIndex connectors; remove any imports
- [ ] T006 Rename config fields in `src/tuesday/runtime/config.py`: `ingestion_chunk_size_chars_default` → `ingestion_chunk_size_tokens_default`, `ingestion_chunk_overlap_chars_default` → `ingestion_chunk_overlap_tokens_default`; update all validators, bounds, and `TUESDAY_INGESTION_CHUNK_SIZE_CHARS_*` env-var aliases to `TUESDAY_INGESTION_CHUNK_SIZE_TOKENS_*` (data-model.md config change)
- [ ] T007 [P] Update `.env.example`: rename `TUESDAY_INGESTION_CHUNK_SIZE_CHARS_DEFAULT` → `TUESDAY_INGESTION_CHUNK_SIZE_TOKENS_DEFAULT` and `TUESDAY_INGESTION_CHUNK_OVERLAP_CHARS_DEFAULT` → `TUESDAY_INGESTION_CHUNK_OVERLAP_TOKENS_DEFAULT`; add inline comments noting values are now token counts (default 1024 / 200) not character counts

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Behavior-Identical Migration (Priority: P1) 🎯 MVP

**Goal**: The fully migrated system operates correctly end-to-end in demo mode (no API keys), passing all existing API contract, unit, integration, and smoke tests.

**Independent Test**: `pytest tests/api/ tests/unit/ tests/integration/ tests/smoke/` all pass against the migrated system with demo backends.

### Implementation for User Story 1

- [ ] T008 [US1] Replace `src/tuesday/rag/infrastructure/qdrant_vector_store.py` with `LlamaIndexQdrantAdapter` implementing the `VectorStore` protocol: (a) maintain `dict[str, QdrantVectorStore]` and `dict[str, VectorStoreIndex]` keyed by `index_name` per R-003; (b) use collection prefix `tuesday_v2__{index_name}` per R-005; (c) implement replace-by-document via existence check → `index.delete_ref_doc(document_id)` → `index.insert()` returning `replaced: bool` per R-004; (d) implement contains-any tag filter via `MetadataFilters(filters=[MetadataFilter(key="tags", value=tag, operator=FilterOperator.EQ) for tag in tags], condition=FilterCondition.OR)` per R-008; (e) store `chunk_id` as LlamaIndex node `id_` per R-007; (f) catch LlamaIndex/Qdrant exceptions and translate to `VectorStoreError` per R-009
- [ ] T009 [P] [US1] Rewrite `DeterministicDenseEmbeddingProvider` in `src/tuesday/rag/infrastructure/providers.py` to subclass `llama_index.core.embeddings.BaseEmbedding`; implement `_get_text_embedding` and `_get_query_embedding` using the existing deterministic vector logic; keep the class usable as `Settings.embed_model` per R-010
- [ ] T010 [US1] Implement `DeterministicLLM` in `src/tuesday/rag/infrastructure/providers.py` subclassing `llama_index.core.llms.LLM`; implement `complete()` and `chat()` returning structured JSON with answer + citations (as `chunk_id` values from `source_nodes`) without any HTTP call; usable as `Settings.llm` per R-010
- [ ] T011 [US1] Replace `src/tuesday/rag/infrastructure/chunking.py` with `LlamaIndexNodeParser` implementing the `Chunker` protocol: wrap `llama_index.core.node_parser.SentenceSplitter` initialized with `chunk_size` and `chunk_overlap` from `RuntimeConfig` token fields (T006); ensure `chunk_overlap < chunk_size` validation preserved; produce chunks with the same domain `Chunk` model per R-011
- [ ] T012 [US1] Rewire `src/tuesday/runtime/container.py`: initialize `llama_index.core.Settings` with `embed_model=DeterministicDenseEmbeddingProvider(...)` and `llm=DeterministicLLM()` for demo mode; wire `LlamaIndexQdrantAdapter` as the vector store; wire `LlamaIndexNodeParser` as the chunker; apply `ResilientEmbedding`, `ResilientLLM`, `ResilientVectorStore` wrappers from `resilience.py` at the adapter boundary; keep existing `build_runtime_from_env` function signature unchanged
- [ ] T013 [US1] Add pre-LLM insufficient-context guard in `src/tuesday/rag/generation/service.py`: before delegating to `LLMProvider.generate()`, check if `retrieved_chunks` is empty; if so, return `GeneratedAnswer(insufficient_context=True, grounded=False, citations=[], used_chunks=[])` with `config.insufficient_context_answer` without calling LLM per DL-004, R-006

### Tests for User Story 1

- [ ] T014 [US1] Update `tests/unit/` for changed modules: (a) update config field-name tests for `ingestion_chunk_size_tokens_*` and `ingestion_chunk_overlap_tokens_*`; (b) update chunking tests for `LlamaIndexNodeParser` token-based boundaries; confirm `chunk_overlap < chunk_size` validator still enforced
- [ ] T015 [US1] Update `tests/integration/` for `LlamaIndexQdrantAdapter`: rewrite integration tests to use new `tuesday_v2__` collection prefix; test replace-by-document returning `replaced=True` on re-index; test contains-any tag filter returns correct chunks; verify `chunk_id` equality between stored and retrieved nodes
- [ ] T016 [P] [US1] Update `tests/smoke/` for new `tuesday_v2__` collection prefix: update any hardcoded collection name references or fixture setup that creates/reads Qdrant collections
- [ ] T017 [US1] Run `pytest tests/api/ tests/unit/ tests/integration/ tests/smoke/` and confirm all pass; document any failures and fix before marking US1 complete

**Checkpoint**: US1 complete — all existing tests pass against the migrated system in demo mode

---

## Phase 4: User Story 2 — LlamaIndex Embedding Integration (Priority: P2)

**Goal**: Real embedding providers (OpenAI, Gemini, Azure) operate via LlamaIndex connectors with no custom urllib code invoked.

**Independent Test**: Index a document and retrieve against it using `TUESDAY_EMBEDDING_PROVIDER_BACKEND=openai` (or `gemini`, `azure_openai`) and confirm indexing/retrieval responses are unchanged.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `LlamaIndexEmbeddingAdapter` in `src/tuesday/rag/infrastructure/providers_vendor.py` implementing the `EmbeddingProvider` protocol: accept any `llama_index.core.embeddings.BaseEmbedding` instance; implement `embed_text(text: str) -> list[float]` and `embed_query(text: str) -> list[float]`; catch LlamaIndex embedding exceptions and translate to `EmbeddingError`
- [ ] T019 [P] [US2] Add OpenAI embedding backend in `src/tuesday/rag/infrastructure/providers_vendor.py`: function `build_openai_embedding(config: RuntimeConfig) -> LlamaIndexEmbeddingAdapter` using `llama_index.embeddings.openai.OpenAIEmbedding` with model and API key from config
- [ ] T020 [P] [US2] Add Gemini embedding backend in `src/tuesday/rag/infrastructure/providers_vendor.py`: function `build_gemini_embedding(config: RuntimeConfig) -> LlamaIndexEmbeddingAdapter` using `llama_index.embeddings.gemini.GeminiEmbedding`
- [ ] T021 [P] [US2] Add Azure OpenAI embedding backend in `src/tuesday/rag/infrastructure/providers_vendor.py`: function `build_azure_openai_embedding(config: RuntimeConfig) -> LlamaIndexEmbeddingAdapter` using `llama_index.embeddings.azure_openai.AzureOpenAIEmbedding`
- [ ] T022 [US2] Update `src/tuesday/runtime/container.py` embedding backend selection: when `TUESDAY_EMBEDDING_PROVIDER_BACKEND` is `openai`, `gemini`, or `azure_openai`, instantiate the corresponding `LlamaIndexEmbeddingAdapter` via T019–T021 builders; also set `Settings.embed_model` to the LlamaIndex model for consistency; keep `demo` path using `DeterministicDenseEmbeddingProvider`

### Tests for User Story 2

- [ ] T023 [US2] Update `tests/unit/` for embedding backends: add unit tests for `LlamaIndexEmbeddingAdapter` (mock `BaseEmbedding`); verify `EmbeddingError` translation; verify provider backend selection in container builds correct adapter type

**Checkpoint**: US1 + US2 functional — real embeddings via LlamaIndex, no urllib HTTP

---

## Phase 5: User Story 3 — LlamaIndex LLM Integration (Priority: P3)

**Goal**: Real LLM providers (OpenAI, Gemini, Azure) operate via LlamaIndex connectors; citations are extracted from `source_nodes`; insufficient-context guard remains intact.

**Independent Test**: Issue a generate request with valid context; confirm answer produced via LlamaIndex LLM, citations reference `chunk_id` values from retrieved chunks, and response shape is unchanged.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `LlamaIndexLLMAdapter` in `src/tuesday/rag/infrastructure/providers_vendor.py` implementing `LLMProvider` protocol: accept any `llama_index.core.llms.LLM` instance; implement `generate(context_chunks, query) -> GeneratedAnswer`; extract citations as `node.node_id` from `response.source_nodes` (per R-007, DL-005); translate LlamaIndex LLM exceptions to `LLMError`
- [ ] T025 [P] [US3] Add OpenAI LLM backend in `src/tuesday/rag/infrastructure/providers_vendor.py`: function `build_openai_llm(config: RuntimeConfig) -> LlamaIndexLLMAdapter` using `llama_index.llms.openai.OpenAI`
- [ ] T026 [P] [US3] Add Gemini LLM backend in `src/tuesday/rag/infrastructure/providers_vendor.py`: function `build_gemini_llm(config: RuntimeConfig) -> LlamaIndexLLMAdapter` using `llama_index.llms.gemini.Gemini`
- [ ] T027 [P] [US3] Add Azure OpenAI LLM backend in `src/tuesday/rag/infrastructure/providers_vendor.py`: function `build_azure_openai_llm(config: RuntimeConfig) -> LlamaIndexLLMAdapter` using `llama_index.llms.azure_openai.AzureOpenAI`
- [ ] T028 [US3] Update `src/tuesday/runtime/container.py` LLM backend selection: when `TUESDAY_GENERATION_PROVIDER_BACKEND` is `openai`, `gemini`, or `azure_openai`, instantiate the corresponding `LlamaIndexLLMAdapter` via T025–T027 builders; also set `Settings.llm` for consistency; keep `demo` path using `DeterministicLLM`

### Tests for User Story 3

- [ ] T029 [US3] Update `tests/unit/` for LLM backends: add unit tests for `LlamaIndexLLMAdapter` (mock LLM); verify citation extraction from `source_nodes` (DL-005); verify `LLMError` translation; add integration test confirming LLM is not called when context is empty (DL-004 — the guard added in T013 prevents the call)

**Checkpoint**: US1 + US2 + US3 functional — full LlamaIndex E2E pipeline operational

---

## Phase 6: User Story 4 — LlamaIndex Retrieval Pipeline (Priority: P4)

**Goal**: Confirm the LlamaIndex VectorStoreIndex retrieval pipeline is correctly wired end-to-end and that the architecture admits future reranking/hybrid search without modifying API or domain layers.

**Independent Test**: End-to-end index → retrieve cycle using LlamaIndex's retrieval pipeline; results satisfy US1 behavioral guarantees.

### Implementation for User Story 4

- [ ] T030 [P] [US4] Add integration test in `tests/integration/test_retrieval_pipeline.py`: index a set of Vietnamese-language test documents; retrieve with `top_k=3` and confirm result count ≤ 3 and response schema matches `RetrievedChunk` domain model
- [ ] T031 [P] [US4] Add integration test in `tests/integration/test_retrieval_pipeline.py`: index documents with tags; retrieve with `tags` filter; confirm only documents matching any requested tag are returned (contains-any, DL-003); confirm no regression from LlamaIndex `MetadataFilters` OR condition
- [ ] T032 [US4] Run `scripts/benchmark_quality.py` and record retrieve + generate latency; confirm each within 20% of pre-migration baseline; document results in a comment in `specs/002-llamaindex-rag-migration/plan.md` under a "Performance Results" note (SC-003)

**Checkpoint**: US1–US4 functional — retrieval pipeline verified end-to-end with behavioral guarantees

---

## Phase 7: User Story 5 — Chunking Strategy (Priority: P5)

**Goal**: Token-based chunking via `SentenceSplitter` is enforced and documented; golden cases and regression baselines reflect the new chunk boundaries.

**Independent Test**: Index a document with known size; confirm chunk count and content match expected `SentenceSplitter` output for the configured token chunk size.

### Implementation for User Story 5

- [ ] T033 [US5] Verify `LlamaIndexNodeParser` in `src/tuesday/rag/infrastructure/chunking.py` initializes `SentenceSplitter` with `chunk_size` and `chunk_overlap` from RuntimeConfig token fields (T006/T011); confirm token-based splitting is active (not character mode); add a `__init__` guard that raises `ValueError` if `chunk_overlap >= chunk_size` (DL-006 validator reused for token semantics)
- [ ] T034 [US5] Regenerate `GENERATION_GOLDEN_CASES` in `src/tuesday/rag/evaluation/`: re-run ingestion of the golden-case source documents with the token-based `LlamaIndexNodeParser`; capture the new `chunk_id` values, chunk boundaries, and expected generation answers; update the fixture so regression tests use accurate post-migration expected values (R-011)
- [ ] T035 [US5] Run `pytest tests/regression/` against the fully migrated system; update any `expected_chunks` or `expected_citations` assertions that fail due to new token-based chunk boundaries; confirm all regression tests pass after update

**Checkpoint**: All five user stories implemented and independently tested

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, code hygiene, and final validation pass

- [ ] T036 Update `docs.md` decision log: (a) mark DL-006 (character-based chunking) as superseded by this migration; (b) add a new DL entry for the LlamaIndex migration authorizing the `infrastructure/` replacement scope, Qdrant schema change, and token chunking switch; (c) update error-mapping section if any error codes changed
- [ ] T037 [P] Run `ruff check . --select E,F,I,B,UP` across all changed files; fix all violations before marking complete (lint must pass per CLAUDE.md)
- [ ] T038 [P] Dead code audit in `src/tuesday/rag/infrastructure/`: search for any remaining `import urllib`, `from .http_client`, or `from .llamaindex_qdrant_bridge` references; remove them; verify no other module imports the deleted files
- [ ] T039 [P] Run `quickstart.md` verification steps end-to-end: prerequisites, architecture overview, and verification sections; confirm all commands succeed in the Python 3.12 + LlamaIndex 0.14.x environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — must complete before US2–US5
- **US2 (Phase 4)**: Depends on US1 completion (embedding adapter builds on demo adapter pattern)
- **US3 (Phase 5)**: Depends on US1 completion (LLM adapter builds on demo LLM pattern)
- **US4 (Phase 6)**: Depends on US1 completion (retrieval pipeline is wired in US1)
- **US5 (Phase 7)**: Depends on US1 completion (LlamaIndexNodeParser implemented in T011)
- **Polish (Phase 8)**: Depends on all user story phases complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Can start after US1 — independent from US3/US4/US5
- **US3 (P3)**: Can start after US1 — independent from US2/US4/US5
- **US4 (P4)**: Can start after US1 — benefits from US2 being complete for real embedding testing
- **US5 (P5)**: Can start after US1 — independent of US2/US3/US4

### Within Each User Story

- Infrastructure adapter before container wiring
- Container wiring before test updates
- Unit tests before integration tests
- Integration tests before checkpoint validation

### Parallel Opportunities

- T004 and T005 (file deletions) in Phase 2
- T009 and T011 can start in parallel with T008 (different files) in Phase 3
- T019, T020, T021 (embedding backends) in Phase 4
- T025, T026, T027 (LLM backends) in Phase 5
- T030 and T031 (retrieval integration tests) in Phase 6
- T037, T038, T039 (polish) in Phase 8
- US2, US3, US4, US5 can be worked in parallel by different developers once US1 is done

---

## Parallel Example: User Story 1

```bash
# After T007 (Foundational complete), launch US1 infrastructure tasks together:
Task T008: Implement LlamaIndexQdrantAdapter (qdrant_vector_store.py)
Task T009: Wrap DeterministicDenseEmbeddingProvider as BaseEmbedding (providers.py)
Task T011: Implement LlamaIndexNodeParser (chunking.py)
# T009 and T011 can run while T008 is in progress

# After T008–T011: wire container, add guard, update tests:
Task T012: Rewire container.py
Task T013: Add insufficient-context guard (generation/service.py)
# T014, T015, T016 can run in parallel once T012 done
```

## Parallel Example: User Stories 2 & 3

```bash
# After US1 checkpoint, launch US2 and US3 in parallel:

# US2 — Embedding:
Task T018: LlamaIndexEmbeddingAdapter base
Tasks T019, T020, T021: OpenAI / Gemini / Azure embedding (parallel)
Task T022: Update container.py embedding selection

# US3 — LLM (parallel with US2):
Task T024: LlamaIndexLLMAdapter base
Tasks T025, T026, T027: OpenAI / Gemini / Azure LLM (parallel)
Task T028: Update container.py LLM selection
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — **CRITICAL, blocks all stories**
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `pytest tests/api/ tests/unit/ tests/integration/ tests/smoke/`
5. Deploy/demo in demo mode if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → All existing tests pass in demo mode → **MVP!**
3. US2 → Real embeddings via LlamaIndex
4. US3 → Real LLM via LlamaIndex → Full provider coverage
5. US4 → Retrieval pipeline verified, latency benchmarked
6. US5 → Token chunking finalized, baselines regenerated
7. Polish → Docs, lint, dead code clean

### Parallel Team Strategy

With multiple developers after US1 is complete:

- **Developer A**: US2 (Embedding — T018–T023)
- **Developer B**: US3 (LLM — T024–T029)
- **Developer C**: US5 (Chunking/Baselines — T033–T035)
- **All**: US4 (Retrieval verification — T030–T032) can be shared

---

## Notes

- [P] tasks = different files, no unresolved dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- **Never re-introduce `src/tuesday_rag/`** — all imports use `tuesday.*`
- **LlamaIndex types must not leak past `infrastructure/`** — domain Protocols are the boundary
- DL-001 through DL-009 must be verified at the adapter boundary, not assumed from LlamaIndex defaults
- Commit after each task or logical group with the required prefix (`feat:`, `fix:`, `refactor:`, `chore:`, etc.)
- Stop at each checkpoint to validate the story independently before proceeding
