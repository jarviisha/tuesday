# 00. Core Brief — Bản Tóm Tắt Cho Phiên Làm Việc

> **Mục đích**: tài liệu nén cho future session (người và agent). Đọc file này trước khi code để bám đúng rule đã khóa. Khi mâu thuẫn với file nén này, spec gốc trong `docs/` và `docs/post-mvp/` mới là nguồn sự thật — cập nhật cả hai nơi khi chốt thay đổi.

## 1. Bản chất dự án

**Tuesday** là platform định hướng capability, khởi đầu với **RAG core** cho chatbot doanh nghiệp. Mục tiêu của core là pipeline `ingestion → retrieval → generation` ổn định, tách domain khỏi hạ tầng để thay engine (LLM, embedding, vector store) mà **không đổi HTTP contract công khai**. Phương pháp: **Spec-Driven Development + TDD**, Python 3.12+, FastAPI, ports-and-adapters.

## 2. Cấu trúc mã nguồn hiện tại (post-migration)

```
src/tuesday/
  api/              # product-level HTTP shell (app factory, middleware, error mapping, observability, /health)
  runtime/          # composition root (RuntimeConfig + Container + build_runtime_from_env + startup checks)
  shared/           # validation helpers dùng chung
  rag/              # capability RAG
    api/            # APIRouter + schemas (mount từ tuesday.api.app)
    domain/         # models, ports, errors — KHÔNG import framework
    ingestion/      # use_case, file_use_case, service
    retrieval/      # use_case, service
    generation/     # use_case, service, prompt_builder
    infrastructure/ # chunking, vector_store (memory, file), resilience, providers (demo + vendor), file_document_parser, http_client
    evaluation/     # golden_cases cho benchmark/regression
src/tuesday_rag/    # legacy shim: mỗi file 1 dòng re-export từ tuesday.* (xoá theo DL-xxx tương lai)
tests/              # api, unit, integration, smoke, regression, quality, fixtures.py, conftest.py
docs/               # spec gốc; post-mvp/ chứa phase 1-4 và migration specs
scripts/            # index_file, index_directory, smoke_test, benchmark_quality
examples/           # fixture thật dùng cho manual test ingestion
benchmarks/         # artifact đánh giá chất lượng
```

**Luồng phụ thuộc (bất biến)**: `api → runtime → capability → domain ports → infrastructure adapters`. Không có chiều ngược. Không có `domain` hay capability import framework.

## 3. Guardrail không được phá

### Boundary

- **Không** import LlamaIndex, SDK vector store, SDK provider trong `tuesday.rag.domain/`, `tuesday.rag.*/use_case.py`, `tuesday.rag.*/service.py`.
- **Không** để object framework (Node, Document, QueryEngine của LlamaIndex; Response SDK của provider) chảy ra ngoài `infrastructure/`.
- `Indexer`, `Retriever`, `Generator` là **service nội bộ gần capability**, không phải port lõi (DL-002) — không đẩy xuống adapter, không kéo lên thành framework abstraction.
- API layer chỉ làm: nhận request → validate schema → gọi use case → map response/lỗi. Không đặt business rule tại đây.

### Scope — không làm trong core trừ khi có spec + quyết định mới

- reranker, hybrid retrieval, async ingestion, streaming response, multi-tenant/RBAC, conversation memory, feedback loop, queue/batch orchestration ngoài CLI nội bộ hiện có, upload file qua HTTP công khai.
- Parser file **chỉ là ingestion path nội bộ** qua `FileIngestionUseCase` + scripts, không được khóa vào public HTTP contract (DL-008).

### Behavior

- **Re-index policy**: `replace-by-document_id-within-index_name` (DL-001). Idempotent: cùng `document_id + index_name + content` lặp lại vẫn hợp lệ.
- **Filter `tags`**: semantics `contains-any` (DL-003). Khóa đồng nhất ở fake adapter, adapter thật, contract test.
- **Insufficient context**: khi không có context, orchestration trả `GeneratedAnswer(insufficient_context=True, grounded=False, citations=[], used_chunks=[])` với `answer` là literal mặc định (`config.insufficient_context_answer`). **Không** gọi `LLMProvider` (DL-004).
- **Citations**: chỉ theo `chunk_id`, phải là tập con của `used_chunks.chunk_id`. Nếu `used_chunks` rỗng thì `citations` phải rỗng (DL-005).
- **Chunking**: theo **ký tự**, không theo token; `chunk_overlap < chunk_size` (DL-006).
- **Config runtime**: nạp một lần khi startup (qua `lifespan`), chỉ override trong biên spec, không đổi public contract (DL-007).
- **Observability**: mỗi request phải có `request_id`, `use_case`, `error_code`, `latency_ms`, `failure_group/component/mode`; **không** log raw content hoặc dữ liệu nhạy cảm (DL-009).
- **PDF parser**: dùng `pdftotext` qua subprocess; lỗi → `DOCUMENT_PARSE_ERROR`. Startup check có 3 mode `off/warn/strict` qua `TUESDAY_PDF_STARTUP_CHECK_MODE` (DL-024).

## 4. Domain model (không đổi schema nếu không có spec mới)

| Model | File | Invariant then chốt |
|---|---|---|
| `SourceDocument` | `rag/domain/models.py` | `document_id` duy nhất trong scope index/namespace; `content` đã trim không rỗng |
| `Chunk` | `rag/domain/models.py` | `chunk_id` duy nhất toàn chỉ mục; `document_id` tham chiếu tới `SourceDocument` hợp lệ |
| `IndexedChunk` | `rag/domain/models.py` | `embedding` không rỗng (enforce ở `__post_init__`) |
| `RetrievedChunk` | `rag/domain/models.py` | `score` chỉ để sort, không phải xác suất |
| `RetrievalRequest` | `rag/domain/models.py` | `top_k > 0` (enforce ở `__post_init__`) |
| `RetrievalResponse` | `rag/domain/models.py` | sort giảm dần theo score |
| `GenerationRequest` | `rag/domain/models.py` | phải có ít nhất một trong `retrieval_request` / `retrieved_chunks` (enforce); `retrieved_chunks=[]` hợp lệ, đi nhánh `insufficient_context` |
| `GeneratedAnswer` | `rag/domain/models.py` | citations ⊆ used_chunks.chunk_id; `insufficient_context=True` ⇒ `grounded=False` |
| `DocumentIndexResult` | `rag/domain/models.py` | status ∈ {`indexed`, `partial`, `failed`} — `partial` hiện chưa bật public (DL-010) |

## 5. Metadata schema của chunk (bắt buộc bám)

`document_id`, `chunk_id`, `title?`, `source_type`, `source_uri?`, `sequence_no`, `language?`, `tags?` (list[str]), `created_at?`, `version?` (chỉ metadata, chưa ảnh hưởng retrieval).

## 6. Ports & adapter (boundary cứng)

**Ports** (trong `rag/domain/ports.py`): `EmbeddingProvider`, `LLMProvider`, `VectorStore`, `DocumentParser`, `Chunker` — chỉ trả domain model hoặc primitive, **không** trả object SDK.

**Adapter hiện có** (`rag/infrastructure/`):
- `HashEmbeddingProvider` (demo, deterministic, hash SHA-256 token set)
- `DeterministicLLMProvider` (demo, echo chunk đầu)
- `OpenAI/Gemini/AzureOpenAI {Embedding,LLM}Provider` qua `providers_vendor.py` + `http_client.py` (stdlib `urllib`, không thêm dependency)
- `InMemoryVectorStore` / `FileBackedVectorStore` (cosine-like qua token set intersection; file-backed ghi atomic qua tempfile + fsync + os.replace)
- `CharacterChunker` — chunk theo ký tự + overlap
- `LocalFileDocumentParser` — txt/md/html/pdf
- `ResilientEmbeddingProvider/LLMProvider/VectorStore` — timeout + retry qua `ThreadPoolExecutor`, chỉ retry trên `ConnectionError`/`OSError`/`RetryableDependencyError`

Container chọn adapter bằng config backend: `embedding_provider_backend`/`generation_provider_backend` ∈ `{demo, openai, gemini, azure_openai}`; `vector_store_backend` ∈ `{memory, file}`.

## 7. API contract (3 endpoint — đã khóa)

| Method | Endpoint | Use case | Trả về |
|---|---|---|---|
| `POST` | `/documents/index` | `IngestionUseCase` | `DocumentIndexResult` |
| `POST` | `/retrieve` | `RetrievalUseCase` | `RetrievalResponse` |
| `POST` | `/generate` | `GenerationUseCase` | `GeneratedAnswer` |
| `GET` | `/health` | product-level | `{"status":"ok"}` |

### Quy tắc mapping quan trọng

- `/generate` phải có ít nhất một trong `retrieval_request` hoặc `retrieved_chunks`.
- Nếu `retrieval_request.query` trống thì orchestration gán `query = question` trước khi gọi retrieval.
- Nếu `retrieval_request` có nhưng `index_name` thiếu cả ở trong lẫn ngoài → `RETRIEVAL_REQUIRED_INDEX_MISSING` (400).
- `retrieved_chunks=[]` → hợp lệ, vào nhánh `insufficient_context`.
- `applied_filters` của `/retrieve` phản ánh filter hợp lệ thực sự đã áp dụng.

### Error code → HTTP status (đã khóa)

| error_code | status | Nhóm |
|---|---|---|
| `INVALID_INPUT`, `UNSUPPORTED_FILTER`, `RETRIEVAL_REQUIRED_INDEX_MISSING` | 400 | application |
| `DOCUMENT_PARSE_ERROR`, `EMPTY_DOCUMENT`, `CHUNKING_ERROR` | 422 | application |
| `EMBEDDING_ERROR`, `GENERATION_ERROR`, `INVALID_GENERATION_OUTPUT` | 502 | provider |
| `INDEX_WRITE_ERROR`, `RETRIEVAL_ERROR` | 502 | storage |
| `PROMPT_BUILD_ERROR` | 500 | application |

## 8. Runtime defaults (override bằng env `TUESDAY_<FIELD>` hoặc legacy `TUESDAY_RAG_<FIELD>`; cũng đọc từ `.env`)

| Field | Default | Bounds |
|---|---|---|
| `retrieval_top_k` | 5 | 1..20 |
| `generation_max_context_chunks` | 5 | 1..10 |
| `ingestion_chunk_size_chars` | 1000 | 300..2000 |
| `ingestion_chunk_overlap_chars` | 150 | 0..300 (< chunk_size) |
| `ingestion_chunk_count_max` | 200 | 1..5000 |
| `content_length` | 100000 | 1..100000 |
| `query_length` / `question_length` | 2000 | 1..2000 |
| `document_id` length | — | 1..128 |
| `index_name` length | — | 1..64 |
| `*_timeout_ms` (embedding / generation / vector_store) | 1000 | 1..60000 |
| `*_max_retries` | 0 | 0..5 |
| `vector_store_backend` | `memory` | `memory`/`file` |
| `embedding_provider_backend` / `generation_provider_backend` | `demo` | `demo`/`openai`/`gemini`/`azure_openai` |
| `pdf_startup_check_mode` | `off` | `off`/`warn`/`strict` |
| `insufficient_context_answer` | `"Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn."` | chỉ override literal, không đổi schema |

## 9. Validation rules (tóm gọn)

- `source_type` ∈ `{text, pdf, html}`.
- Filters chỉ whitelist: `document_id`, `source_type`, `language`, `tags`. Key khác → `UNSUPPORTED_FILTER`.
- `filters.tags` và `metadata.tags` phải là `list[str]` không rỗng phần tử.
- `metadata` phải là JSON object hợp lệ; `metadata.language` nếu có phải là mã ngôn ngữ ngắn (`vi`, `en`).
- `content`/`query`/`question` sau trim không được rỗng.

## 10. Test strategy

**Tỷ lệ MVP**: 60% unit / 25% use case / 10% API / 5% integration.

**Mock**: `EmbeddingProvider`, `LLMProvider`, `VectorStore`, `DocumentParser`, clock/UUID khi cần ổn định, config khi test bounds override.

**Không mock**: domain model + rule, mapper domain↔API schema, prompt builder, validation của use case; ở integration test không mock adapter đang test và không mock serialization HTTP.

**Test data rule**: deterministic; tiếng Việt ưu tiên cho fixture/input (AGENTS.md language rule); không chứa dữ liệu nhạy cảm thật.

## 11. Golden cases (bám vào `tuesday.rag.evaluation.GENERATION_GOLDEN_CASES` + fixture tại `docs/15-golden-cases-va-fixtures.md`)

| Fixture | Dùng cho |
|---|---|
| A: `doc-refund-001` (tiếng Việt ngắn) | ingestion thành công, retrieval VN, generation grounded |
| B: `doc-onboarding-001` (đủ dài, nhiều chunk) | chunking, metadata, top_k > 1 |
| C: `doc-empty-001` (rỗng sau trim) | validation error của `/documents/index` |
| D: query không match | `/retrieve` trả `chunks=[]`; `/generate` trả `insufficient_context` |

## 12. Quy tắc làm việc (agent working rules — từ AGENTS.md)

- **Ngôn ngữ**: English cho source, test, commit, identifier; tiếng Việt có dấu cho spec trong `docs/`; fixture/input ưu tiên tiếng Việt.
- **Thay đổi surgical**: chỉ sửa đúng file/line cần cho task. Không refactor lẫn vào. Vấn đề lân cận ghi riêng.
- **Trước khi implement thay đổi đáng kể**: nêu rõ giả định, đặt tiêu chí nghiệm thu, ưu tiên có test chứng minh.
- **Lint**: ruff với `E, F, I, B, UP` — mọi code mới phải pass.
- **Test**: chạy `./.venv/bin/python -m pytest` trước khi báo xong; nếu đổi contract/config bounds/semantics, phải cập nhật test + doc gốc.
- **Không viết comment giải thích WHAT**; chỉ viết khi WHY không hiển nhiên.
- **Không thêm doc .md mới trừ khi user yêu cầu** — mở rộng file hiện có.

## 13. Decision log — chỉ mục nhanh (xem `docs/14-decision-log.md` cho đầy đủ)

| ID | Nội dung chốt |
|---|---|
| DL-001 | Re-index policy `replace-by-document_id-within-index_name` |
| DL-002 | `Indexer`/`Retriever`/`Generator` là service nội bộ, không phải port lõi |
| DL-003 | `tags` semantics `contains-any` |
| DL-004 | Không gọi `LLMProvider` khi không có context |
| DL-005 | Citation theo `chunk_id`, chỉ lấy từ `used_chunks` |
| DL-006 | Chunking theo ký tự; default 1000/150 |
| DL-007 | Config runtime nạp khi startup, chỉ override trong biên spec |
| DL-008 | Public API MVP chỉ khóa JSON text; parser file là nội bộ |
| DL-009 | Không log raw content ngoài mức debug tối thiểu |
| DL-010 | `PARTIAL_INDEXED` chưa thuộc public MVP |
| DL-011 | Invariant khóa bằng unit test, không ép layer domain-behavior riêng |
| DL-012 | Public MVP đã đóng scope (3 endpoint + behavior cốt lõi + test + log cơ bản) |
| DL-013 | Thứ tự post-MVP: `stabilize → operational_hardening → quality_evaluation → feature_expansion` |
| DL-014 | Feature mới không mặc định là blocker; cần business case rõ |
| DL-015..017 | Workstream split cho phase 1/2/3 |
| DL-018 | Full migration `src/tuesday_rag` từng bị hoãn (đã `superseded` bởi DL-019) |
| DL-019 | **Chấp nhận full migration** sang capability-oriented (`src/tuesday/`) — đã thực hiện |
| DL-020 | Feature đầu Phase 4: `internal file ingestion` qua entrypoint nội bộ |
| DL-021 | Parser `.html` tối giản trong cùng Phase 4 |
| DL-022 | Batch ingestion nội bộ qua script — continue-on-error |
| DL-023 | `--recursive` opt-in; default quét 1 level |
| DL-024 | PDF qua `pdftotext` subprocess; thiếu tool → `DOCUMENT_PARSE_ERROR` |
| DL-025 | `--output` summary JSON song song stdout |
| DL-026 | `--include` / `--exclude` glob; `exclude` thắng cuối |
| DL-027 | `--dry-run` preview candidate + document_id, không ghi |
| DL-028 | Chương `post-mvp` đã đóng; nhịp mới chuyển track `core` |
| DL-029 | **Ưu tiên track `core`**: provider thật + env-based selection → vector store thật → container qua lifespan → context-sufficiency policy → retrieval hardening |

## 14. Dấu hiệu đang lệch khỏi đường ray (checklist tự rà)

- [ ] Code ở `rag/*/use_case.py` hoặc `rag/*/service.py` đang import SDK provider hoặc `llama_index` → vi phạm boundary.
- [ ] Adapter bắt đầu quyết định prompt format, citation format, response schema → kéo lên `generation/` hoặc `api/`.
- [ ] Endpoint mới xuất hiện không có spec trong `docs/` hoặc `docs/post-mvp/`.
- [ ] Config mới thêm để mở rộng behavior thay vì siết/nới trong biên đã khóa.
- [ ] Test phải sửa hàng loạt do semantics chưa được khóa rõ — dừng, ghi decision log trước.
- [ ] Comment giải thích WHAT thay vì WHY.
- [ ] Thêm file markdown mới ngoài `docs/` mà user không yêu cầu.

## 15. Tham chiếu gốc (khi cần chi tiết)

| Chủ đề | File gốc |
|---|---|
| Tổng quan + nguyên tắc thiết kế | `docs/01-tong-quan-du-an.md` |
| Kiến trúc chi tiết + hot/non-hot path | `docs/02-kien-truc-tong-the.md` |
| Domain model đầy đủ | `docs/03-domain-model.md` |
| Ports + boundary + adapter | `docs/04-ports-va-adapters.md` |
| Ingestion use case đầy đủ | `docs/05-use-case-ingestion.md` |
| Retrieval use case đầy đủ | `docs/06-use-case-retrieval.md` |
| Generation use case đầy đủ | `docs/07-use-case-generation.md` |
| API contract + error mapping + runtime defaults | `docs/08-api-contract.md` |
| Test strategy đầy đủ | `docs/09-test-strategy.md` |
| Kế hoạch sprint | `docs/10-ke-hoach-trien-khai-theo-sprint.md` |
| Glossary | `docs/11-glossary.md` |
| Review + điểm thiếu + decision đã khóa | `docs/12-review-tong-hop.md` |
| Checklist trước khi code | `docs/13-checklist-truoc-khi-code.md` |
| Decision log (nguồn chính) | `docs/14-decision-log.md` |
| Golden cases + fixture | `docs/15-golden-cases-va-fixtures.md` |
| Implementation guardrails | `docs/16-implementation-guardrails.md` |
| Post-MVP phase 1-4 | `docs/post-mvp/` |
| Migration structure | `docs/post-mvp/40-spec-quyet-dinh-migration-cau-truc-src.md`, `41-spec-target-layout-migration-phase-4.md` |

## 16. Khi có thay đổi, cập nhật ở đâu

- **Đổi behavior, contract, config bounds, semantics** → ghi decision log mới (`docs/14-decision-log.md`) + cập nhật spec gốc tương ứng + cập nhật **file này** + cập nhật test.
- **Đổi layout src** → cập nhật mục 2 của file này + README + AGENTS.md + migration spec trong `docs/post-mvp/`.
- **Đóng phase/track mới** → decision log + README section tương ứng.
