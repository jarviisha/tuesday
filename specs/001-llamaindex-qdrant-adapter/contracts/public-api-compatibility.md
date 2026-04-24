# Public API Compatibility Contract

## Scope

This feature is an internal infrastructure refactor. The public HTTP interface
remains unchanged.

## Endpoints Covered

- `POST /documents/index`
- `POST /retrieve`
- `POST /generate`
- `GET /health`

## Contract Rules

- Request payload shapes for public endpoints remain unchanged.
- Response payload shapes for public endpoints remain unchanged.
- Existing error codes and status code mappings remain unchanged for indexing
  and retrieval failures.
- Retrieval responses continue to expose:
  - `query`
  - `top_k`
  - `index_name`
  - `applied_filters`
  - `chunks`
- Generation responses continue to expose:
  - `answer`
  - `citations`
  - `grounded`
  - `insufficient_context`
  - `used_chunks`

## Compatibility Behaviors

- Re-indexing the same `document_id` within the same `index_name` continues to
  replace the existing stored document content.
- `filters.tags` continues to use contains-any semantics.
- Retrieval ordering remains compatible after backend lookup, lexical reranking,
  and `top_k` trimming.
- `applied_filters` continues to reflect the supported filters actually used.
- Backend indexing and retrieval failures continue to surface through the
  existing application-level error mapping.

## Out of Scope

- New public endpoints
- New request or response fields
- New authentication or permission behavior
- Changes to domain model shape
