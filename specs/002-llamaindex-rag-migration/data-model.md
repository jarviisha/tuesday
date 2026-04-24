# Data Model: LlamaIndex End-to-End RAG Migration

## Entity Changes

### Retained (unchanged at domain boundary)

| Entity | Location | Notes |
|---|---|---|
| `SourceDocument` | `rag/domain/models.py` | Unchanged |
| `Chunk` | `rag/domain/models.py` | Unchanged |
| `IndexedChunk` | `rag/domain/models.py` | Unchanged — still the domain model for a stored chunk |
| `RetrievedChunk` | `rag/domain/models.py` | Unchanged — domain model for retrieval results |
| `GeneratedAnswer` | `rag/domain/models.py` | Unchanged — domain model for generation results |
| `VectorStore` Protocol | `rag/domain/ports.py` | Unchanged — LlamaIndex adapters implement this |
| `EmbeddingProvider` Protocol | `rag/domain/ports.py` | Unchanged — LlamaIndex embed models implement this |
| `LLMProvider` Protocol | `rag/domain/ports.py` | Unchanged — LlamaIndex LLMs implement this |

### Replaced in infrastructure (not domain)

| Old | New | Location |
|---|---|---|
| `LlamaIndexQdrantBridge` | `LlamaIndexQdrantAdapter` | `rag/infrastructure/` |
| `CharacterChunker` | `LlamaIndexNodeParser` (wraps `SentenceSplitter`) | `rag/infrastructure/` |
| `OpenAIEmbeddingProvider` (urllib) | `LlamaIndexEmbeddingAdapter` (wraps LlamaIndex model) | `rag/infrastructure/` |
| `GeminiEmbeddingProvider` (urllib) | same adapter, different backend | `rag/infrastructure/` |
| `AzureOpenAIEmbeddingProvider` (urllib) | same adapter, different backend | `rag/infrastructure/` |
| `OpenAILLMProvider` (urllib) | `LlamaIndexLLMAdapter` (wraps LlamaIndex LLM) | `rag/infrastructure/` |
| `GeminiLLMProvider` (urllib) | same adapter, different backend | `rag/infrastructure/` |
| `AzureOpenAILLMProvider` (urllib) | same adapter, different backend | `rag/infrastructure/` |

### New infrastructure types

| Entity | Purpose |
|---|---|
| `LlamaIndexQdrantAdapter` | Implements `VectorStore` protocol; manages per-index `VectorStoreIndex` instances backed by LlamaIndex's `QdrantVectorStore` |
| `LlamaIndexEmbeddingAdapter` | Implements `EmbeddingProvider` protocol; wraps any `BaseEmbedding` subclass |
| `LlamaIndexLLMAdapter` | Implements `LLMProvider` protocol; wraps any `LLM` subclass; extracts answer + citations from structured LLM output |
| `LlamaIndexNodeParser` | Implements `Chunker` protocol; wraps `SentenceSplitter` with token-based config |

---

## Qdrant Storage Schema Change

### Current schema (bridge)
```json
{
  "document_id": "string",
  "chunk_id": "string",
  "text": "string",
  "metadata": { "...": "..." },
  "source_type": "string | null",
  "language": "string | null",
  "tags": ["string"] | null
}
```

### New schema (LlamaIndex QdrantVectorStore)
```json
{
  "_node_content": "{\"id_\": \"chunk_id\", \"text\": \"...\", \"metadata\": {\"document_id\": \"...\", \"chunk_id\": \"...\", \"tags\": [...], ...}}",
  "_node_type": "TextNode",
  "doc_id": "document_id",
  "document_id": "document_id",
  "ref_doc_id": "document_id"
}
```

**Migration impact**: Old collections are unreadable by LlamaIndex's
`QdrantVectorStore`. A new collection prefix (`tuesday_v2__<index_name>`)
is used for migrated data. Old `tuesday__<index_name>` collections are
left intact until explicitly deleted.

---

## Config Model (RuntimeConfig)

| Field | Change |
|---|---|
| `ingestion_chunk_size_chars_*` | Rename to `ingestion_chunk_size_tokens_*` — semantics change from chars to tokens |
| `ingestion_chunk_overlap_chars_*` | Rename to `ingestion_chunk_overlap_tokens_*` |
| `qdrant_collection_prefix` | Add `v2` suffix in default, or new field `qdrant_collection_prefix_v2` |
| All other fields | Unchanged |

**Env var impact**: `TUESDAY_INGESTION_CHUNK_SIZE_CHARS_DEFAULT` and related
vars must be updated to reflect token semantics. A deprecation note in
`.env.example` is required.
