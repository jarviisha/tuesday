# Feature Specification: LlamaIndex End-to-End RAG Migration

**Feature Branch**: `[002-llamaindex-rag-migration]`
**Created**: 2026-04-24
**Status**: Draft
**Input**: User description: "Migrate RAG core to use LlamaIndex end-to-end ecosystem"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-Identical Migration (Priority: P1)

As a platform maintainer, I need the RAG core to deliver the same observable
behavior after migrating to LlamaIndex so that production clients, regression
baselines, and locked API contracts are not broken.

**Why this priority**: Every downstream user story depends on this guarantee.
Migration without behavioral parity is a regression, not a feature.

**Independent Test**: Run the full suite of existing regression, API contract,
and smoke tests against the migrated system and confirm identical public
responses, error shapes, and locked semantic behavior.

**Acceptance Scenarios**:

1. **Given** an existing index built before migration, **When** a retrieve
   request is issued after migration, **Then** the response shape, applied
   filters, and chunk scoring order are identical to pre-migration behavior.
2. **Given** a generate request with no matching context, **When** the
   migrated system processes it, **Then** the response contains the
   `insufficient_context` flag, the configured fallback answer, and no
   LLM call is made.
3. **Given** an index and retrieve flow with tag-based filtering, **When**
   filters are applied after migration, **Then** the `contains-any` tag
   semantics return the same chunk set as before.
4. **Given** existing regression golden cases, **When** run against the
   migrated system, **Then** all pass without modification.

---

### User Story 2 - LlamaIndex Embedding Integration (Priority: P2)

As a platform maintainer, I can configure the system to use LlamaIndex's
built-in embedding model connectors so that I don't need custom HTTP client
implementations to embed text.

**Why this priority**: Embedding is a prerequisite for both ingestion and
retrieval. Replacing the custom HTTP layer with LlamaIndex's connectors
reduces maintenance surface and unlocks LlamaIndex's model ecosystem.

**Independent Test**: Index a document and retrieve against it using
LlamaIndex-backed embedding (OpenAI, Gemini, or Azure) and confirm the
public indexing and retrieval responses are unchanged.

**Acceptance Scenarios**:

1. **Given** OpenAI or Gemini credentials in configuration, **When** a
   document is indexed, **Then** embeddings are produced via LlamaIndex's
   connector without any custom HTTP client code being invoked.
2. **Given** a retrieval request, **When** the query is embedded, **Then**
   the embedding is produced by the same LlamaIndex connector used during
   ingestion, preserving semantic consistency.

---

### User Story 3 - LlamaIndex LLM Integration (Priority: P3)

As a platform maintainer, I can configure the system to use LlamaIndex's
built-in LLM connectors for generation so that the project benefits from
LlamaIndex's provider ecosystem including prompt management and retry logic.

**Why this priority**: Depends on embedding integration (US2). Once
embedding is stable, replacing the custom LLM HTTP layer is the next
leverage point.

**Independent Test**: Issue a generate request with valid context and confirm
the answer is produced via a LlamaIndex LLM connector, citations are present,
and the response shape is unchanged.

**Acceptance Scenarios**:

1. **Given** a configured LLM provider (OpenAI, Gemini, or Azure), **When**
   a generate request is issued with sufficient context, **Then** the answer
   is produced via LlamaIndex's LLM connector and citations reference
   `chunk_id` values from retrieved chunks.
2. **Given** a generate request with no context, **When** the system
   evaluates context sufficiency, **Then** the LLM connector is not called
   and the configured fallback answer is returned.

---

### User Story 4 - LlamaIndex Retrieval Pipeline (Priority: P4)

As a platform maintainer, I can use LlamaIndex's retrieval abstractions
(VectorStoreIndex, retrievers) so that advanced capabilities such as
reranking and hybrid search can be added without redesigning the retrieval
layer.

**Why this priority**: Depends on vector store and embedding integration.
Enables future roadmap items (reranking, hybrid search) as configuration
rather than custom code.

**Independent Test**: Perform an end-to-end index → retrieve cycle using
LlamaIndex's retrieval pipeline and confirm results match the behavioral
guarantees of User Story 1.

**Acceptance Scenarios**:

1. **Given** an indexed document set, **When** a retrieval request is issued
   with `top_k` and optional filters, **Then** LlamaIndex's retriever
   produces the result set and the public response shape is unchanged.
2. **Given** a retrieval request with `tags` filter, **When** processed by
   the LlamaIndex retrieval pipeline, **Then** `contains-any` semantics are
   preserved exactly as before migration.

---

### User Story 5 - Chunking Strategy Decision (Priority: P5)

As a platform maintainer, I have a clearly documented and enforced chunking
strategy using LlamaIndex's node parsers so that chunking behavior is
predictable and configurable.

**Why this priority**: Lowest risk slice. Chunking affects ingestion quality
but the decision can be deferred without blocking other stories.

**Independent Test**: Index a document with a known size, confirm the number
and content of produced chunks matches the configured chunking strategy.

**Acceptance Scenarios**:

1. **Given** configured chunk size and overlap parameters, **When** a
   document is ingested, **Then** the number and boundaries of chunks match
   the expected output of the chosen LlamaIndex node parser.

---

### Edge Cases

- What happens when a retrieve or generate request arrives during a
  dependency upgrade or LlamaIndex version bump?
- How does the system handle a LlamaIndex connector failure (network error,
  rate limit) compared to current resilience wrappers?
- Does LlamaIndex's `replace_ref_doc` / `delete_ref_doc` flow preserve
  exact replace-by-document_id semantics (DL-001) including the `replaced`
  boolean return?
- If Qdrant collections were created before migration, are existing payloads
  readable by LlamaIndex's QdrantVectorStore, or is a data migration step
  required?
- Which locked semantics (DL-001 through DL-009) require explicit
  re-implementation on top of LlamaIndex, and which are preserved naturally?
- Does the system maintain correct behavior when Python version is later
  upgraded (the migration requires Python 3.12 or 3.13 at minimum)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The migrated system MUST produce identical public HTTP
  responses for `/documents/index`, `/retrieve`, and `/generate` as the
  pre-migration system for all existing test cases.
- **FR-002**: The system MUST preserve replace-by-document_id semantics:
  re-indexing the same `(document_id, index_name)` replaces all prior
  chunks and returns a `replaced` indicator (DL-001).
- **FR-003**: The system MUST preserve tag filtering with `contains-any`
  semantics: a chunk is returned if it matches any of the requested tags (DL-003).
- **FR-004**: The system MUST preserve insufficient-context behavior: when
  no usable context exists, the system returns the configured fallback
  answer without calling the LLM (DL-004).
- **FR-005**: The system MUST produce citations as `chunk_id` values that
  are a subset of the `used_chunks` in every generate response (DL-005).
- **FR-006**: The system MUST preserve request-level observability: every
  request logs `request_id`, `use_case`, `error_code`, `latency_ms`, and
  failure context (DL-009). LlamaIndex's internal instrumentation MUST NOT
  replace this.
- **FR-007**: The system MUST support all existing provider backends
  (OpenAI, Gemini, Azure OpenAI) for both embedding and generation via
  LlamaIndex connectors, selectable through existing `TUESDAY_*` env vars.
- **FR-008**: The system MUST retain a demo/test mode that operates without
  API keys for local development and CI.
- **FR-009**: Chunking MUST switch to token-based splitting using
  LlamaIndex's default node parser (SentenceSplitter). DL-006
  (character-based chunking) is intentionally superseded by this
  migration. Golden cases and regression baselines must be re-evaluated
  after migration to reflect new chunk boundaries.
- **FR-010**: The system MUST continue to support the `qdrant` vector store
  backend via LlamaIndex's QdrantVectorStore.

### Key Entities

- **Node**: LlamaIndex's unit of indexed content, replacing `IndexedChunk`
  at the infrastructure boundary. Must carry `document_id`, `chunk_id`,
  `tags`, `source_type`, `language` as metadata.
- **VectorStoreIndex**: LlamaIndex's index abstraction that combines vector
  store, embedding model, and retrieval into one manageable unit.
- **Settings**: LlamaIndex's global configuration object for embedding
  model, LLM, and node parser. Replaces the project's per-component
  construction in `Container`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing regression, API contract, error-mapping, and
  smoke tests pass against the migrated system without modification.
- **SC-002**: The end-to-end index → retrieve → generate cycle completes
  successfully with each supported provider (OpenAI, Gemini, Azure) and
  the demo mode.
- **SC-003**: Response latency for retrieve and generate requests does not
  increase by more than 20% compared to the pre-migration baseline under
  equivalent load.
- **SC-004**: LlamaIndex ecosystem features (reranking, hybrid search) can
  be enabled through configuration changes without modifying the API or
  domain layers.
- **SC-005**: The system operates correctly on Python 3.12 or 3.13 with
  LlamaIndex types actually imported (not shim fallback).

## Assumptions

- Python 3.12 or 3.13 will be installed and the venv recreated before
  implementation begins. This is a hard prerequisite; work cannot start
  without it.
- The public HTTP contract (`POST /documents/index`, `POST /retrieve`,
  `POST /generate`, `GET /health`) and Pydantic request/response schemas
  remain unchanged.
- Existing `TUESDAY_*` environment variable names are preserved; only
  the underlying wiring changes.
- `InMemoryVectorStore` and `FileBackedVectorStore` (non-Qdrant paths)
  are out of scope for LlamaIndex migration. They remain as-is or are
  deprecated explicitly in a follow-up decision.
- Existing Qdrant collections may need a data migration step if
  LlamaIndex's payload schema differs from the current schema. This will
  be assessed during planning.
- The FastAPI shell (`api/`, `runtime/` wiring, middleware, error mapping)
  is not changed by this migration.
- LlamaIndex version constraints will be determined during planning based
  on Python 3.12/3.13 compatibility and available package versions.
