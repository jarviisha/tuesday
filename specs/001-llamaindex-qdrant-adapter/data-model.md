# Data Model: Preserve Core Behavior with Infrastructure Adapter

## Overview

This feature does not introduce new public entities. It preserves the existing
core data shapes and defines the compatibility rules that the adapter
replacement must maintain.

## Entities

### Indexed Chunk Record

- **Purpose**: Persisted searchable chunk used by indexing and retrieval flows.
- **Existing fields**:
  - `chunk_id`
  - `document_id`
  - `text`
  - `embedding`
  - `metadata`
  - `index_name`
- **Validation rules**:
  - `embedding` must remain non-empty.
  - `metadata` must continue to carry filterable values used by retrieval, such
    as `document_id`, `source_type`, `language`, and `tags`.
- **State constraints**:
  - Re-indexing the same `document_id` within the same `index_name` must replace
    the prior persisted chunk set.

### Retrieved Chunk

- **Purpose**: Retrieval result returned from the vector-store path and consumed
  by retrieval and generation orchestration.
- **Existing fields**:
  - `chunk_id`
  - `document_id`
  - `text`
  - `score`
  - `metadata`
- **Validation rules**:
  - Returned chunks must remain compatible with the existing retrieval response
    schema.
  - Ordering must remain compatible after vector-store lookup, lexical rerank,
    and `top_k` trimming.

### Applied Filters

- **Purpose**: Record of supported retrieval filters that were accepted and used
  by the retrieval flow.
- **Existing fields**:
  - `document_id`
  - `source_type`
  - `language`
  - `tags`
- **Validation rules**:
  - `tags` semantics must remain contains-any.
  - Unsupported filters must continue to fail through the existing validation
    path rather than being silently passed through.

### Compatibility Baseline

- **Purpose**: Non-entity compatibility target describing the behaviors the
  adapter replacement must preserve.
- **Tracked behaviors**:
  - public request and response shapes
  - re-index replacement semantics
  - retrieval filter semantics
  - retrieval ordering after rerank and `top_k`
  - `applied_filters` behavior
  - backend failure mapping
  - insufficient-context and citation behavior in generation

## Relationships

- An **Indexed Chunk Record** belongs to one `document_id` and one `index_name`.
- A **Retrieved Chunk** is derived from an **Indexed Chunk Record** through the
  real vector-store lookup plus existing retrieval orchestration.
- **Applied Filters** constrain which **Indexed Chunk Records** can contribute to
  a **Retrieved Chunk** result set.
- The **Compatibility Baseline** constrains the acceptable behavior of every
  adapter mapping and backend interaction touched by this feature.
