# Research: LlamaIndex End-to-End RAG Migration

## R-001: Python Runtime Prerequisite

**Decision**: Install Python 3.12 via pyenv before any implementation work.

**Rationale**: `llama-index-core` 0.14.x imports cleanly on Python 3.12 and 3.13.
On Python 3.14 the `pydantic.v1` compatibility layer fails at model class
creation time — unfixable without upstream changes to llama-index or pydantic.

**Steps**:
```bash
pyenv install 3.12.9        # or latest 3.12.x
pyenv local 3.12.9
python3.12 -m venv .venv
pip install -e '.[dev]'
```

**Alternatives considered**: Pin pydantic to a version where pydantic.v1 works on
3.14 — not viable; the failure is in pydantic.v1.validators at class creation
time regardless of pydantic version.

---

## R-002: LlamaIndex Package Set

**Decision**: Add the following packages to `pyproject.toml` as runtime
dependencies, replacing the current `llama-index-core>=0.14,<0.15` entry:

```
llama-index-core>=0.14,<0.15
llama-index-vector-stores-qdrant>=0.4,<1.0
llama-index-embeddings-openai>=0.3,<1.0
llama-index-embeddings-gemini>=0.3,<1.0
llama-index-embeddings-azure-openai>=0.3,<1.0
llama-index-llms-openai>=0.4,<1.0
llama-index-llms-gemini>=0.4,<1.0
llama-index-llms-azure-openai>=0.3,<1.0
```

**Note**: Exact version bounds must be verified against Python 3.12 availability
during implementation. `llama-index-vector-stores-qdrant` official PyPI package
(0.4.x+) must replace the current local 0.1.4 build.

**Rationale**: Each integration is a separate optional LlamaIndex package.
Splitting avoids pulling in unnecessary SDKs.

---

## R-003: Multi-Index Support with LlamaIndex QdrantVectorStore

**Decision**: Maintain a `dict[str, QdrantVectorStore]` and
`dict[str, VectorStoreIndex]` keyed by `index_name` inside a new
`LlamaIndexQdrantAdapter`. Each index gets its own Qdrant collection
(`{prefix}__{index_name}`).

**Rationale**: LlamaIndex's `QdrantVectorStore` is initialized per-collection.
The project's domain Protocol requires `index_name` on every call. The adapter
manages the per-index instances, keeping multi-index routing inside
`infrastructure/`.

**Pattern**:
```python
class LlamaIndexQdrantAdapter:
    def get_or_create_index(self, index_name: str) -> VectorStoreIndex: ...
```

---

## R-004: Replace-by-Document Semantics (DL-001)

**Decision**: Implement replace-by-document using LlamaIndex's
`index.delete_ref_doc(doc_id)` followed by `index.insert(document)`. Check
existence before delete to determine `replaced` boolean.

**Pattern**:
```python
# Check existence
existing = vector_store.get_nodes(filters=..., doc_id=document_id)
replaced = len(existing) > 0
if replaced:
    index.delete_ref_doc(document_id, delete_from_docstore=True)
index.insert(document)
return replaced
```

**Alternatives considered**: `index.refresh_ref_docs()` — only updates changed
documents; does not give control over whether replacement occurred.

---

## R-005: Qdrant Payload Schema Migration

**Decision**: LlamaIndex's `QdrantVectorStore` stores node content in
`_node_content` (JSON-serialized) and `_node_type` fields, with metadata
flattened into the Qdrant payload. This is **incompatible** with the current
bridge schema (`document_id`, `chunk_id`, `text`, `metadata` as top-level
payload fields).

**Impact**: Existing Qdrant collections must be re-indexed after migration.
There is no in-place migration path. The implementation plan must include a
step to flush and re-index any existing collections, or to coordinate a
collection rename/prefix change so old and new collections coexist during
transition.

**Decision**: Use a new collection prefix (`tuesday_v2`) for migrated data so
old collections remain intact until explicitly deleted.

---

## R-006: Insufficient-Context Handling (DL-004)

**Decision**: Keep the insufficient-context check in `GenerationUseCase` before
delegating to LlamaIndex's query engine. If `len(retrieved_nodes) == 0`, return
the fallback answer immediately without constructing or calling a `QueryEngine`.

**Rationale**: LlamaIndex's `QueryEngine` calls the LLM even with empty
source nodes (it synthesizes a "no context" response). The DL-004 semantic
(zero LLM calls when no context) must be enforced at the orchestration layer.

---

## R-007: Citation Semantics (DL-005)

**Decision**: Use LlamaIndex's `response.source_nodes` to extract citations.
Each `NodeWithScore` has a `node.node_id` which maps to the stored `chunk_id`.
Citations are the `node_id` values from `source_nodes` where score > 0.

**Requirement**: The `chunk_id` must be stored as the LlamaIndex node's `id_`
so that `node.node_id` == `chunk_id` after retrieval.

---

## R-008: Tag Filtering with Contains-Any (DL-003)

**Decision**: Implement `contains-any` tag filtering via LlamaIndex's
`MetadataFilters` with `FilterCondition.OR`:

```python
MetadataFilters(
    filters=[
        MetadataFilter(key="tags", value=tag, operator=FilterOperator.EQ)
        for tag in requested_tags
    ],
    condition=FilterCondition.OR,
)
```

**Verified**: LlamaIndex's QdrantVectorStore translates `FilterCondition.OR`
to Qdrant's `should` clause, which implements "any" semantics.

---

## R-009: Observability Preservation (DL-009)

**Decision**: The existing FastAPI middleware (`request_id`, `latency_ms`,
`use_case`, `error_code`, `failure_group`) is not touched. LlamaIndex's
internal instrumentation runs independently and does not replace it.

LlamaIndex exceptions must be caught at the infrastructure adapter boundary
and translated to the project's domain errors (`VectorStoreError`,
`EmbeddingError`, `LLMError`) so the existing API error-mapping middleware
continues to produce correct `error_code` values.

---

## R-010: Demo Mode Without API Keys

**Decision**: Keep `DeterministicDenseEmbeddingProvider` as a LlamaIndex
`BaseEmbedding` subclass (or wrap it). For LLM demo mode, implement a
`DeterministicLLM(LLM)` that returns structured JSON without an API call.

**Rationale**: LlamaIndex requires `Settings.embed_model` and `Settings.llm`
to be set. Wrapping the existing demo providers as LlamaIndex types is the
least-disruptive path and keeps CI working without API keys.

---

## R-011: Token-Based Chunking (FR-009, supersedes DL-006)

**Decision**: Use `SentenceSplitter` with `chunk_size` in tokens (default
1024) and `chunk_overlap` in tokens (default 200). The `TUESDAY_*` config
variables `ingestion_chunk_size` and `ingestion_chunk_overlap` are reused
but now express token counts, not character counts.

**Impact**: Golden cases and regression baselines in `rag/evaluation/` must
be re-generated after migration. The `GENERATION_GOLDEN_CASES` fixture may
need updated `used_chunks` sets.

---

## R-012: Domain Port Strategy

**Decision**: Preserve the `VectorStore`, `EmbeddingProvider`, and
`LLMProvider` domain Protocols. LlamaIndex components live in `infrastructure/`
and implement these ports. Use cases and services continue to depend only on
the protocol interfaces.

**Rationale**: Keeps the architecture honest — LlamaIndex is an infrastructure
choice, not a domain concern. Preserves the ability to swap LlamaIndex for
another framework in the future without touching domain or API layers.
