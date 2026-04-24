# API Contract: LlamaIndex Migration

**Status**: UNCHANGED — the public HTTP contract is preserved exactly.

All three endpoints (`POST /documents/index`, `POST /retrieve`,
`POST /generate`) and `GET /health` retain their existing request and
response shapes as defined in `docs.md` (sourced from `docs/08-api-contract.md`).

No new fields, no removed fields, no status code changes.

## What changes internally (not observable via HTTP)

- Chunking now produces token-based boundaries instead of character-based.
  Chunk text content and `chunk_id` values will differ for the same
  document after re-indexing. This is expected and documented.
- Qdrant collection names use a new prefix (`tuesday_v2__`). Clients
  referencing `index_name` directly are unaffected.
- Error codes and HTTP status mappings are unchanged.
