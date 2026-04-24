# Quickstart: LlamaIndex End-to-End RAG Migration

## Prerequisites (must complete before any code changes)

### 1. Install Python 3.12

```bash
pyenv install 3.12.9
pyenv local 3.12.9
python3.12 --version   # → Python 3.12.9
```

### 2. Recreate the venv

```bash
rm -rf .venv
python3.12 -m venv .venv
./.venv/bin/pip install -e '.[dev]'
```

### 3. Verify LlamaIndex imports

```bash
./.venv/bin/python -c "
from llama_index.core import Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.schema import TextNode
print('LlamaIndex imports: OK')
"
```

Expected output: `LlamaIndex imports: OK`

---

## Architecture After Migration

```
FastAPI shell (unchanged)
    ↓
runtime/Container  ←  LlamaIndex Settings configured here
    ↓
rag/*/use_case.py  ←  unchanged, depends on domain Protocols
    ↓
rag/*/service.py   ←  unchanged, depends on domain Protocols
    ↓
rag/infrastructure/
  LlamaIndexQdrantAdapter      ← new, implements VectorStore Protocol
  LlamaIndexEmbeddingAdapter   ← new, implements EmbeddingProvider Protocol
  LlamaIndexLLMAdapter         ← new, implements LLMProvider Protocol
  LlamaIndexNodeParser         ← new, implements Chunker Protocol
```

Domain ports (`VectorStore`, `EmbeddingProvider`, `LLMProvider`, `Chunker`)
are **preserved**. LlamaIndex lives entirely in `infrastructure/`.

---

## Locked Semantics — Implementation Notes

| Semantic | DL | Implementation |
|---|---|---|
| Replace-by-document | DL-001 | `index.delete_ref_doc(doc_id)` + `index.insert(doc)`. Check pre-existence for `replaced` bool. |
| Tags contains-any | DL-003 | `MetadataFilters(filters=[...], condition=FilterCondition.OR)` |
| Insufficient context | DL-004 | Check `len(retrieved_nodes) == 0` in `GenerationUseCase` **before** calling LlamaIndex QueryEngine |
| Citations by chunk_id | DL-005 | Extract from `response.source_nodes`; each node's `node_id` == `chunk_id` |
| Observability | DL-009 | FastAPI middleware unchanged; LlamaIndex exceptions translated to domain errors at adapter boundary |
| Chunking (superseded) | DL-006 | Token-based `SentenceSplitter` replaces character-based `CharacterChunker` |

---

## Qdrant Collection Migration

Old collections (`tuesday__<index_name>`) use the bridge payload schema and
are unreadable by LlamaIndex's QdrantVectorStore. After migration:

1. New collections use prefix `tuesday_v2__<index_name>`.
2. Existing data in old collections must be re-indexed via `scripts/index_directory.py`.
3. Old collections can be deleted manually once re-indexing is verified.

---

## Verification Commands

```bash
# Unit + API tests (must all pass after each phase)
./.venv/bin/python -m pytest tests/unit tests/api -q

# Integration test (requires Qdrant running)
./.venv/bin/python -m pytest tests/integration/ -q

# Smoke test end-to-end
./.venv/bin/python -m pytest tests/smoke/ -q

# Regression (golden cases — will need update after chunking change)
./.venv/bin/python -m pytest tests/regression/ -q

# Lint
./.venv/bin/python -m ruff check .
```
