# Tuesday Consolidated Docs

> This file consolidates all Markdown files previously stored under `docs/`.
> Source sections are preserved with their original relative paths for traceability.
> Legacy path references inside copied content are preserved verbatim and should be
> read as historical source labels, not as the current workflow structure.


---

## Source: `docs/00-core-brief.md`

# 00. Core Brief — Bản Tóm Tắt Cho Phiên Làm Việc

> **Mục đích**: tài liệu nén cho future session (người và agent). Đọc file này trước khi code để bám đúng rule đã khóa. Khi mâu thuẫn với file nén này, spec hiện hành ở `docs/` root và `docs/core/` mới là nguồn sự thật — cập nhật cả hai nơi khi chốt thay đổi. `docs/history/` chỉ là hồ sơ lịch sử, không áp dụng trực tiếp cho hành vi hiện tại.

## 1. Bản chất dự án

**Tuesday** là platform định hướng capability, khởi đầu với **RAG core** cho chatbot doanh nghiệp. Mục tiêu của core là pipeline `ingestion → retrieval → generation` ổn định, tách domain khỏi hạ tầng để thay engine (LLM, embedding, vector store) mà **không đổi HTTP contract công khai**. Phương pháp: **Spec-Driven Development + TDD**, Python 3.12+, FastAPI, ports-and-adapters.

## 2. Cấu trúc mã nguồn hiện tại

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
tests/              # api, unit, integration, smoke, regression, quality, fixtures.py, conftest.py
docs/               # spec gốc; post-mvp/ chứa phase 1-4 và migration specs
scripts/            # index_file, index_directory, smoke_test, benchmark_quality
examples/           # fixture thật dùng cho manual test ingestion
benchmarks/         # artifact đánh giá chất lượng
```

> Package cũ `src/tuesday_rag/` (legacy shim) đã được xoá hoàn toàn. Mọi import phải dùng `tuesday.*`; không tái tạo đường dẫn cũ kể cả qua re-export.

**Luồng phụ thuộc (bất biến)**: `api → runtime → capability → domain ports → infrastructure adapters`. Không có chiều ngược. Không có `domain` hay capability import framework.

## 3. Guardrail không được phá

### Boundary

- **Không** import LlamaIndex, SDK vector store, SDK provider trong `tuesday.rag.domain/`, `tuesday.rag.*/use_case.py`, `tuesday.rag.*/service.py`.
- LlamaIndex chỉ được phép dùng trong `tuesday.rag.infrastructure/` như adapter/helper hạ tầng; không dùng các orchestration object như `Settings`, `IngestionPipeline`, `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer` (DL-032).
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
- `DeterministicDenseEmbeddingProvider` (demo cho `Qdrant`, fixed-size dense vector để tương thích cosine retrieval thật)
- `DeterministicLLMProvider` (demo, echo chunk đầu)
- `OpenAI/Gemini/AzureOpenAI {Embedding,LLM}Provider` qua `providers_vendor.py` + `http_client.py` (stdlib `urllib`, không thêm dependency)
- `InMemoryVectorStore` / `FileBackedVectorStore` (cosine-like qua token set intersection; file-backed ghi atomic qua tempfile + fsync + os.replace)
- `QdrantVectorStore` (backend thật; local `:memory:` cho integration test, remote qua `url`/`api_key`)
- `CharacterChunker` — chunk theo ký tự + overlap
- `LocalFileDocumentParser` — txt/md/html/pdf
- `ResilientEmbeddingProvider/LLMProvider/VectorStore` — timeout + retry qua `ThreadPoolExecutor`, chỉ retry trên `ConnectionError`/`OSError`/`RetryableDependencyError`

Container chọn adapter bằng config backend: `embedding_provider_backend`/`generation_provider_backend` ∈ `{demo, openai, gemini, azure_openai}`; `vector_store_backend` ∈ `{memory, file, qdrant}`. Khi `vector_store_backend=qdrant` và `embedding_provider_backend=demo`, runtime dùng `DeterministicDenseEmbeddingProvider` thay cho `HashEmbeddingProvider`.

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

## 8. Runtime defaults (override bằng env `TUESDAY_<FIELD>`; cũng đọc từ `.env`. Prefix legacy `TUESDAY_RAG_` vẫn được container chấp nhận như fallback nhưng không còn là đường dẫn khuyến nghị)

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
| `vector_store_backend` | `memory` | `memory`/`file`/`qdrant` |
| `qdrant_url` / `qdrant_location` | — | cần ít nhất một giá trị khi `vector_store_backend=qdrant` |
| `qdrant_collection_prefix` | `tuesday` | non-blank |
| `qdrant_dense_vector_size` | `512` | 8..4096 |
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
- **Lint/typing**: ruff với `E, F, I, B, UP` và `pyright` (mode `standard`) — mọi code mới phải pass.
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
| DL-019 | **Chấp nhận full migration** sang capability-oriented (`src/tuesday/`) — đã hoàn tất, legacy shim `tuesday_rag` đã xoá |
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
| DL-030 | Journey docs tách sang `docs/history/`; `docs/` root = spec hiện hành, `docs/core/` = track đang mở |
| DL-031 | Nhịp 1 track `core` (provider integration + runtime lifecycle, spec 57/60) đã hoàn tất `2026-04-23` |
| DL-032 | Spec 58 chọn `Qdrant` cho v1; LlamaIndex chỉ được dùng chọn lọc trong `infrastructure/`, không được trở thành orchestration spine |
| DL-033 | Spec 59 khóa deterministic context-sufficiency policy trước khi gọi `LLMProvider`; thiếu context thì trả `insufficient_context` và vẫn giữ `used_chunks` |
| DL-034 | Spec 56 khóa deterministic post-retrieval lexical reranking/filter trong `RetrieverService` trước khi trả response |

## 14. Dấu hiệu đang lệch khỏi đường ray (checklist tự rà)

- [ ] Code ở `rag/*/use_case.py` hoặc `rag/*/service.py` đang import SDK provider hoặc `llama_index` → vi phạm boundary.
- [ ] `infrastructure/` bắt đầu dùng `Settings`, `IngestionPipeline`, `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer` của LlamaIndex như orchestration spine → lệch khỏi DL-032.
- [ ] Adapter bắt đầu quyết định prompt format, citation format, response schema → kéo lên `generation/` hoặc `api/`.
- [ ] Endpoint mới xuất hiện không có spec trong `docs/` root hoặc `docs/core/`.
- [ ] Config mới thêm để mở rộng behavior thay vì siết/nới trong biên đã khóa.
- [ ] Test phải sửa hàng loạt do semantics chưa được khóa rõ — dừng, ghi decision log trước.
- [ ] Comment giải thích WHAT thay vì WHY.
- [ ] Thêm file markdown mới ngoài `docs/` mà user không yêu cầu.

## 15. Tham chiếu gốc (khi cần chi tiết)

### Spec hiện hành (`docs/` root)

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
| Glossary | `docs/11-glossary.md` |
| Decision log (nguồn chính, sống chung với spec) | `docs/14-decision-log.md` |
| Golden cases + fixture | `docs/15-golden-cases-va-fixtures.md` |
| Implementation guardrails | `docs/16-implementation-guardrails.md` |

### Track đang mở (`docs/core/`)

| Chủ đề | File gốc | Trạng thái |
|---|---|---|
| Core track overview + ưu tiên hiện tại | `docs/core/55-core-track-overview.md` | — |
| Retrieval core hardening v1 | `docs/core/56-spec-retrieval-core-hardening-v1.md` | `accepted` (`2026-04-23`) — vừa hoàn tất |
| Provider integration + runtime lifecycle v1 | `docs/core/57-spec-provider-integration-and-runtime-lifecycle-v1.md` | `accepted` (`2026-04-23`) |
| Real vector store adapter v1 | `docs/core/58-spec-real-vector-store-adapter-v1.md` | `accepted` (`2026-04-23`) |
| Generation context policy v1 | `docs/core/59-spec-generation-context-policy-v1.md` | `accepted` (`2026-04-23`) — vừa hoàn tất |
| Provider runtime implementation v1 | `docs/core/60-spec-provider-runtime-implementation-v1.md` | `accepted` (`2026-04-23`) |

### Archive lịch sử (`docs/history/` — tham khảo cho provenance, không áp dụng cho behavior hiện tại)

| Chủ đề | File |
|---|---|
| Kế hoạch sprint MVP | `docs/history/10-ke-hoach-trien-khai-theo-sprint.md` |
| Review tổng hợp pre-code | `docs/history/12-review-tong-hop.md` |
| Checklist trước khi code MVP | `docs/history/13-checklist-truoc-khi-code.md` |
| Closeout post-MVP | `docs/history/54-closeout-post-mvp.md` |
| Journey post-MVP phase 1-4 | `docs/history/post-mvp/` |
| Migration structure spec | `docs/history/post-mvp/40-spec-quyet-dinh-migration-cau-truc-src.md`, `41-spec-target-layout-migration-phase-4.md` |

## 16. Khi có thay đổi, cập nhật ở đâu

- **Đổi behavior, contract, config bounds, semantics** → ghi decision log mới (`docs/14-decision-log.md`) + cập nhật spec hiện hành tương ứng + cập nhật **file này** + cập nhật test.
- **Đổi layout src** → cập nhật mục 2 của file này + README + AGENTS.md + spec trong `docs/core/` nếu có liên quan.
- **Đóng phase/track mới, hoặc di chuyển doc sang archive** → decision log + README section tương ứng + cập nhật mục 15 của file này.
- **Không thêm doc mới vào `docs/history/`** — spec mới đi vào `docs/core/` hoặc `docs/` root.


---

## Source: `docs/01-tong-quan-du-an.md`

# 01. Tổng Quan Dự Án

## Mục lục
- Mục tiêu dự án
- Phạm vi MVP
- Ngoài phạm vi
- Giả định kỹ thuật
- Ràng buộc kiến trúc
- Nguyên tắc thiết kế

## Mục tiêu dự án

Xây dựng một RAG core cho chatbot doanh nghiệp với các mục tiêu:

- Cung cấp pipeline nền tảng cho `ingestion`, `retrieval`, `generation`.
- Tách biệt rõ domain và hạ tầng để tránh phụ thuộc trực tiếp vào LlamaIndex hoặc provider cụ thể.
- Cho phép thay thế vector store, cloud LLM, cloud embedding với chi phí thay đổi thấp.
- Tạo nền đặc tả đủ rõ để team triển khai theo hướng Spec-Driven Development kết hợp TDD.

## Phạm vi MVP

MVP bao gồm:

- Nhận tài liệu đầu vào ở dạng văn bản đã chuẩn hóa cho public API MVP.
- Cho phép parser file tồn tại ở infrastructure để phục vụ nguồn nhập nội bộ hoặc mở rộng sau MVP, nhưng không khóa contract HTTP công khai vào upload file ngay từ sprint đầu.
- Tách tài liệu thành `Chunk`, gắn metadata chuẩn, sinh embedding, và lập chỉ mục vào vector store.
- Nhận truy vấn, thực hiện truy hồi ngữ cảnh theo `top_k` và bộ lọc metadata cơ bản.
- Sinh câu trả lời dựa trên ngữ cảnh truy hồi được.
- Trả về citation theo `chunk_id`.
- Cung cấp API đồng bộ qua FastAPI cho:
  - `POST /documents/index`
  - `POST /retrieve`
  - `POST /generate`
- Ghi log kỹ thuật tối thiểu để trace request.
- Khi không có context phù hợp, trả kết quả `insufficient_context` trực tiếp ở orchestration/capability layer, không gọi LLM.

## Ngoài phạm vi

Các hạng mục chưa thuộc MVP:

- Giao diện người dùng chat hoàn chỉnh.
- Quản trị người dùng, phân quyền đa tenant, RBAC.
- Đồng bộ tài liệu theo lịch, CDC, webhook ingestion.
- OCR nâng cao, parse bảng phức tạp, parse layout nâng cao.
- Reranker chuyên biệt.
- Bộ nhớ hội thoại dài hạn.
- Streaming response.
- Cơ chế feedback loop, evaluation tự động, A/B test.
- Workflow orchestration phân tán, hàng đợi nền, batch job quy mô lớn.

## Giả định kỹ thuật

- Hệ thống ưu tiên tài liệu tiếng Việt và tiếng Anh dạng văn bản.
- Tài liệu đầu vào ban đầu có kích thước vừa phải, phục vụ MVP nội bộ.
- Cloud embedding model hỗ trợ embedding cho nội dung tài liệu và truy vấn.
- Cloud LLM hỗ trợ sinh câu trả lời không cần fine-tune.
- Vector store ban đầu có thể là một giải pháp managed hoặc self-hosted, nhưng phải được che sau port nội bộ.
- LlamaIndex chỉ được dùng trong adapter hoặc engine layer, không đi vào domain model và use case.
- MVP chấp nhận xử lý ingestion đồng bộ trước, nếu cần tối ưu sẽ tách bất đồng bộ sau MVP.
- Public API MVP ưu tiên JSON đơn giản; các mode ingestion phức tạp hơn có thể bổ sung sau khi luồng text chuẩn hóa ổn định.
- Re-index policy của MVP là `replace-by-document_id-within-index_name`.
- Cấu hình runtime của MVP được nạp một lần khi khởi động ứng dụng; cho phép override các default/min/max đã khóa trong spec nhưng không được làm thay đổi public contract.

## Ràng buộc kiến trúc

- Ngôn ngữ triển khai: Python.
- API layer: FastAPI.
- Kiến trúc: ports/adapters.
- Domain model nội bộ là nguồn sự thật duy nhất cho use case.
- Business logic không phụ thuộc trực tiếp vào:
  - object model của LlamaIndex
  - SDK riêng của vector store
  - SDK riêng của cloud LLM/embedding
- Mọi object framework-specific phải được map về model nội bộ trước khi đi vào orchestration/capability layer.
- Hành vi `generation` phải grounding vào context đã truy hồi.

## Nguyên tắc thiết kế

- Ưu tiên đơn giản nhưng tách lớp đúng chỗ.
- Chỉ đặc tả những gì cần để triển khai MVP thật.
- Tách rõ 3 boundary:
  - `ingestion`
  - `retrieval`
  - `generation`
- Mỗi use case phải có input, output, validation, error cases, acceptance criteria và test case mức use case.
- Mọi cổng tích hợp ngoài hệ thống phải đi qua port.
- Metadata của chunk phải đủ để:
  - lọc theo tài liệu
  - truy vết citation
  - hỗ trợ mở rộng sau MVP
- Ưu tiên deterministic behavior ở orchestration/capability layer; phần không deterministic được cô lập trong adapter gọi mô hình.
- Thiết kế để thay thế engine mà không làm đổi API contract công khai.
- Với trường hợp không có context phù hợp, orchestration/capability layer nên trả kết quả `insufficient_context` có kiểm soát thay vì phụ thuộc hoàn toàn vào hành vi ngẫu nhiên của LLM.


---

## Source: `docs/02-kien-truc-tong-the.md`

# 02. Kiến Trúc Tổng Thể

## Mục lục
- Kiến trúc tổng thể MVP
- Thành phần chính
- Hot path và non-hot path
- Vai trò công nghệ
- Luồng online và offline
- Hướng mở rộng sau MVP

## Kiến trúc tổng thể MVP

MVP khởi đầu theo kiến trúc 4 lớp, và sau nhịp migration Phase 4 đầu tiên repo đang ở trạng thái capability-oriented nhẹ:

1. `api/`
   - FastAPI nhận request, validate schema, map lỗi và giữ request-level observability.
2. `runtime/`
   - Chứa composition root và runtime wiring dùng chung.
3. Capability packages
   - `ingestion/`, `retrieval/`, `generation/` chứa use case/service gần với từng capability.
4. `domain/`
   - Chứa domain model, invariant, interface/port.
5. `infrastructure/`
   - Adapter cho chunking, provider, resilience và vector store.

Luồng phụ thuộc hiện tại:

- `api -> runtime -> capability packages -> domain ports -> infrastructure adapters`
- Không có chiều ngược lại từ `domain` hoặc capability packages sang framework object.

## Các thành phần chính

| Thành phần | Vai trò | Ghi chú |
|---|---|---|
| FastAPI API | Điểm vào HTTP cho MVP | Không chứa business logic |
| Runtime Container | Composition root và runtime wiring | Không neo trực tiếp vào HTTP layer |
| Ingestion Use Case | Parse, chunk, embed, index | Nằm trong capability `ingestion/` |
| Retrieval Use Case | Embed query, tìm kiếm, lọc metadata | Nằm trong capability `retrieval/` |
| Generation Use Case | Build prompt, grounding, sinh answer | Nằm trong capability `generation/` |
| Domain Models | Mô hình dữ liệu nội bộ | Không phụ thuộc framework |
| Ports | Khai báo interface lõi | Là hợp đồng giữa app và hạ tầng |
| Capability Services | Điều phối port gần với capability | Gồm `Indexer`, `Retriever`, `Generator` |
| LlamaIndex Adapter | Tận dụng engine indexing/retrieval nếu cần | Chỉ là adapter |
| Vector Store Adapter | Lưu và truy vấn vector | Có thể thay thế |
| Cloud Embedding Adapter | Sinh embedding | Có thể thay thế |
| Cloud LLM Adapter | Sinh câu trả lời | Có thể thay thế |

## Hot path và non-hot path

### Hot path

Hot path là các luồng ảnh hưởng trực tiếp đến độ trễ request online:

- `POST /retrieve`
- `POST /generate`

Yêu cầu:

- Số bước xử lý ít, rõ ràng.
- Không parse lại tài liệu gốc ở hot path.
- Không gọi adapter không cần thiết.
- Truy vết được `request_id`, `chunk_id`.

### Non-hot path

Non-hot path là các luồng chấp nhận độ trễ cao hơn:

- `POST /documents/index`
- Chuẩn hóa tài liệu
- Re-index khi đổi chiến lược chunking hoặc embedding

Yêu cầu:

- Ưu tiên tính đúng và khả năng phục hồi.
- Có thể nâng cấp sang bất đồng bộ sau MVP.

## Vai trò của FastAPI, LlamaIndex, vector store, cloud LLM, cloud embedding

| Công nghệ | Vai trò trong MVP | Boundary |
|---|---|---|
| FastAPI | HTTP transport, schema validation, error mapping | Chỉ ở API layer |
| LlamaIndex | Engine/adaptor hỗ trợ indexing/retrieval/generation plumbing | Chỉ ở infrastructure |
| Vector store | Lưu vector và metadata, truy hồi tương đồng | Sau port `VectorStore` |
| Cloud embedding | Biến text thành vector embedding | Sau port `EmbeddingProvider` |
| Cloud LLM | Sinh câu trả lời từ prompt có context | Sau port `LLMProvider` |

## Luồng online và luồng offline

### Luồng offline: ingestion

1. API nhận tài liệu đầu vào.
2. Với public API MVP, request JSON được map trực tiếp thành `SourceDocument`.
3. `DocumentParser` chỉ được gọi khi nguồn vào không phải văn bản đã chuẩn hóa hoặc khi có ingestion path nội bộ riêng.
4. Capability `ingestion` gọi `Chunker` để tạo danh sách `Chunk`.
5. Capability `ingestion` gọi `EmbeddingProvider` để sinh embedding cho từng chunk.
6. Capability `ingestion` gọi service `Indexer` để map `Chunk` thành `IndexedChunk` và ghi vào `VectorStore`.
7. Trước khi ghi mới, hệ thống xóa hoặc thay thế toàn bộ dữ liệu cũ của cùng `document_id` trong cùng `index_name` theo policy `replace-by-document_id-within-index_name`.
8. Trả về `DocumentIndexResult`.

### Luồng online: retrieval

1. API nhận truy vấn.
2. Capability `retrieval` tạo `RetrievalRequest`.
3. Gọi service `Retriever`.
4. `Retriever` dùng `EmbeddingProvider` + `VectorStore`.
5. Kết quả được map về `RetrievalResponse` gồm danh sách `RetrievedChunk`.

### Luồng online: generation

1. API nhận câu hỏi và tùy chọn retrieved context hoặc yêu cầu hệ thống tự retrieval.
2. Capability `generation` chuẩn hóa thành `GenerationRequest`.
3. Nếu chưa có context, gọi service `Retriever`.
4. Nếu sau retrieval không có context phù hợp, capability `generation` có thể trả trực tiếp kết quả `insufficient_context` theo policy MVP mà không cần gọi `LLMProvider`.
5. Nếu có context, build prompt theo quy tắc grounding.
6. Gọi service `Generator`, bên dưới dùng `LLMProvider`.
7. Trả về `GeneratedAnswer` với citation theo `chunk_id`.

## Hướng mở rộng sau MVP

- Tách ingestion sang job queue.
- Bổ sung reranker qua port riêng.
- Hỗ trợ nhiều parser theo loại file.
- Bổ sung hybrid retrieval: vector + keyword.
- Thêm tenant boundary và quyền truy cập metadata.
- Thêm evaluation harness cho retrieval precision và answer grounding.
- Bổ sung streaming, conversation state, caching.


---

## Source: `docs/03-domain-model.md`

# 03. Domain Model

## Mục lục
- Danh sách model cốt lõi
- Mô tả và thuộc tính
- Invariant
- Metadata schema cho chunk
- Quan hệ giữa các model

## Danh sách domain model cốt lõi

- `SourceDocument`
- `Chunk`
- `IndexedChunk`
- `RetrievedChunk`
- `RetrievalRequest`
- `RetrievalResponse`
- `GenerationRequest`
- `GeneratedAnswer`
- `DocumentIndexResult`

## Mô tả từng model

### SourceDocument

Biểu diễn tài liệu nguồn sau khi parse và chuẩn hóa.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | Định danh duy nhất của tài liệu |
| `title` | string | Không | Tiêu đề tài liệu nếu có |
| `content` | string | Có | Nội dung văn bản đã chuẩn hóa |
| `source_type` | string | Có | Loại nguồn, ví dụ `text`, `pdf`, `html` |
| `source_uri` | string | Không | Đường dẫn hoặc URI nguồn |
| `language` | string | Không | Ngôn ngữ chính của tài liệu |
| `metadata` | object | Có | Metadata cấp tài liệu |
| `checksum` | string | Không | Dấu vết nội dung để phát hiện thay đổi |

### Chunk

Đơn vị văn bản nhỏ nhất được dùng cho embedding và retrieval.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `chunk_id` | string | Có | Định danh duy nhất của chunk |
| `document_id` | string | Có | Tham chiếu tới `SourceDocument` |
| `text` | string | Có | Nội dung chunk |
| `sequence_no` | int | Có | Vị trí tuần tự trong tài liệu |
| `token_count` | int | Không | Số token ước lượng |
| `char_start` | int | Không | Vị trí bắt đầu trong tài liệu |
| `char_end` | int | Không | Vị trí kết thúc trong tài liệu |
| `metadata` | object | Có | Metadata chuẩn cho retrieval/citation |

### IndexedChunk

Chunk đã được gắn embedding và lưu được vào chỉ mục truy hồi.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `chunk_id` | string | Có | Trùng với `Chunk.chunk_id` |
| `document_id` | string | Có | Tài liệu nguồn |
| `text` | string | Có | Nội dung chunk |
| `embedding` | list[float] | Có | Vector embedding |
| `metadata` | object | Có | Metadata lưu cùng vector |
| `index_name` | string | Có | Tên logical index |

### RetrievedChunk

Chunk được trả về từ retrieval.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `chunk_id` | string | Có | Định danh chunk |
| `document_id` | string | Có | Tài liệu nguồn |
| `text` | string | Có | Nội dung chunk |
| `score` | float | Có | Điểm liên quan tương đối |
| `metadata` | object | Có | Metadata để lọc và citation |

### RetrievalRequest

Yêu cầu truy hồi ngữ cảnh.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Có | Câu hỏi hoặc truy vấn |
| `top_k` | int | Có | Số chunk tối đa cần trả về |
| `filters` | object | Không | Bộ lọc metadata |
| `index_name` | string | Có | Logical index cần truy vấn |
| `request_id` | string | Không | ID trace |

### RetrievalResponse

Kết quả trả về từ retrieval.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Có | Truy vấn gốc |
| `top_k` | int | Có | Giá trị đã áp dụng |
| `chunks` | list[RetrievedChunk] | Có | Danh sách chunk trả về |
| `applied_filters` | object | Có | Bộ lọc đã áp dụng thực tế |
| `index_name` | string | Có | Logical index đã truy vấn |

### GenerationRequest

Yêu cầu sinh câu trả lời.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `question` | string | Có | Câu hỏi người dùng |
| `retrieval_request` | RetrievalRequest | Không | Dùng khi hệ thống tự retrieval |
| `retrieved_chunks` | list[RetrievedChunk] | Không | Dùng khi context đã có sẵn |
| `max_context_chunks` | int | Không | Giới hạn số chunk dùng để build prompt |
| `request_id` | string | Không | ID trace |

### GeneratedAnswer

Kết quả cuối cùng của generation.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `answer` | string | Có | Câu trả lời cho người dùng |
| `citations` | list[string] | Có | Danh sách `chunk_id` được viện dẫn |
| `grounded` | bool | Có | Có đủ căn cứ từ context hay không |
| `insufficient_context` | bool | Có | Có thiếu ngữ cảnh hay không |
| `used_chunks` | list[RetrievedChunk] | Có | Các chunk thực tế đã dùng |

### DocumentIndexResult

Kết quả của use case ingestion.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | Tài liệu đã xử lý |
| `index_name` | string | Có | Logical index đã ghi |
| `chunk_count` | int | Có | Số chunk đã tạo |
| `indexed_count` | int | Có | Số chunk đã lưu thành công |
| `status` | string | Có | `indexed`, `partial`, `failed` |
| `errors` | list[string] | Có | Danh sách lỗi mức nghiệp vụ |
| `replaced_document` | bool | Có | Có thay thế dữ liệu cũ của cùng `document_id` trong `index_name` hay không |

## Invariant / rule quan trọng

- `document_id` phải duy nhất trong phạm vi logical index hoặc namespace.
- `chunk_id` phải duy nhất trong toàn bộ chỉ mục.
- `Chunk.document_id` phải tham chiếu tới một `SourceDocument` hợp lệ.
- `IndexedChunk.embedding` không được rỗng.
- Khi ingest lại cùng `document_id` trong cùng `index_name`, hệ thống phải thay thế dữ liệu cũ theo policy `replace-by-document_id-within-index_name`.
- `RetrievalRequest.top_k` phải > 0 và không vượt trần cấu hình.
- `RetrievedChunk.score` chỉ dùng để sắp xếp tương đối, không được coi là xác suất.
- `GenerationRequest` phải có ít nhất một trong hai trường sau được cung cấp:
  - `retrieval_request`
  - `retrieved_chunks`
- Nếu `retrieved_chunks` đã được cung cấp thì application không được tự ý gọi retrieval lại.
- Nếu `retrieved_chunks` được cung cấp dưới dạng danh sách rỗng thì request vẫn hợp lệ và phải đi theo nhánh `insufficient_context`.
- `GeneratedAnswer.citations` phải là tập con của `used_chunks.chunk_id`.
- Nếu `insufficient_context = true` thì `grounded` không được là `true`.
- Nếu `used_chunks` rỗng thì `citations` phải rỗng.

## Metadata schema cho chunk

Schema metadata chuẩn cho `Chunk`, `IndexedChunk`, `RetrievedChunk`:

| Trường | Kiểu | Bắt buộc | Mục đích |
|---|---|---|---|
| `document_id` | string | Có | Truy vết tài liệu |
| `chunk_id` | string | Có | Citation và trace |
| `title` | string | Không | Hiển thị nguồn |
| `source_type` | string | Có | Lọc theo loại nguồn |
| `source_uri` | string | Không | Truy vết nguồn |
| `sequence_no` | int | Có | Bảo toàn thứ tự |
| `language` | string | Không | Lọc ngôn ngữ |
| `tags` | list[string] | Không | Lọc nghiệp vụ cơ bản |
| `created_at` | string | Không | Theo dõi thời điểm ingest |
| `version` | string | Không | Chỉ để theo dõi version metadata, chưa ảnh hưởng retrieval logic ở MVP |

Nguyên tắc:

- Metadata phải đủ để truy vết và lọc nhưng không nhồi dữ liệu lớn.
- Không lưu object framework-specific vào metadata domain.
- Không lưu thông tin bí mật nhạy cảm trong metadata nếu không có cơ chế kiểm soát phù hợp.

## Mối quan hệ giữa các model

- Một `SourceDocument` sinh ra nhiều `Chunk`.
- Một `Chunk` sau khi được embed trở thành `IndexedChunk`.
- Từ một `RetrievalRequest`, hệ thống trả về một `RetrievalResponse` gồm nhiều `RetrievedChunk`.
- Một `GenerationRequest` dùng danh sách `RetrievedChunk` để tạo `GeneratedAnswer`.
- Một `SourceDocument` sau ingestion trả về một `DocumentIndexResult`.


---

## Source: `docs/04-ports-va-adapters.md`

# 04. Ports Và Adapters

## Mục lục
- Cách áp dụng kiến trúc ports/adapters
- Boundary orchestration/capability và infrastructure
- Danh sách port
- Service nội bộ gần capability
- Trách nhiệm từng port
- Adapter sử dụng LlamaIndex và cloud provider
- Nguyên tắc thay thế engine

## Cách áp dụng ports/adapters cho dự án

Mục tiêu của ports/adapters trong dự án này:

- Ổn định orchestration nội bộ khi thay đổi công nghệ hạ tầng.
- Cô lập SDK và object model bên ngoài.
- Cho phép test use case bằng fake hoặc mock adapter.

Quy tắc:

- Orchestration/capability layer chỉ biết interface.
- Infrastructure chịu trách nhiệm:
  - gọi SDK
  - map dữ liệu vào/ra domain model
  - chuyển lỗi kỹ thuật sang lỗi hạ tầng có kiểm soát

## Boundary giữa orchestration/capability và infrastructure

### Orchestration/capability layer chịu trách nhiệm

- Validate nghiệp vụ.
- Điều phối thứ tự xử lý use case.
- Ghép dữ liệu từ nhiều port.
- Quyết định fallback và error mapping ở mức use case.

### Infrastructure layer chịu trách nhiệm

- Gọi LlamaIndex nếu được dùng như engine phụ trợ.
- Gọi cloud provider cho embedding và LLM.
- Gọi vector store cụ thể.
- Parse file đầu vào.
- Chuyển object bên ngoài thành domain model nội bộ.

## Danh sách interface/port lõi cần có

- `EmbeddingProvider`
- `LLMProvider`
- `VectorStore`
- `DocumentParser`
- `Chunker`

## Service nội bộ gần capability

Trong MVP này:

- `Indexer`
- `Retriever`
- `Generator`

được xem là service nội bộ gần capability, chưa phải port lõi.

Nguyên tắc:

- Service nội bộ có thể điều phối nhiều port lõi.
- Service nội bộ không làm thay đổi boundary giữa orchestration/capability và infrastructure.
- Nếu sau này cần thay engine hoặc tách abstraction sâu hơn, khi đó mới cân nhắc nâng chúng thành port riêng.

## Trách nhiệm của từng port

### EmbeddingProvider

Trách nhiệm:

- Nhận danh sách text hoặc một query text.
- Trả về embedding dưới dạng `list[float]`.
- Không trả về object SDK.

Đầu ra kỳ vọng:

- Embedding cùng kích thước ổn định theo cấu hình model.

### LLMProvider

Trách nhiệm:

- Nhận prompt hoàn chỉnh hoặc message đã chuẩn hóa nội bộ.
- Trả về văn bản sinh ra.
- Không tự ý fetch thêm dữ liệu ngoài context đã cung cấp.

### VectorStore

Trách nhiệm:

- Upsert `IndexedChunk`.
- Truy vấn theo embedding + filter metadata.
- Xóa hoặc thay thế bản ghi nếu cần ở mức kỹ thuật.

Lưu ý:

- Port này không được buộc orchestration/capability layer biết chi tiết engine của vector store.

### DocumentParser

Trách nhiệm:

- Nhận input tài liệu thô.
- Parse và chuẩn hóa thành `SourceDocument`.

### Chunker

Trách nhiệm:

- Nhận `SourceDocument`.
- Trả về danh sách `Chunk`.
- Bảo toàn mapping thứ tự và metadata nền.

### Indexer

Vai trò hiện tại: service nội bộ gần capability, không phải port lõi.

Trách nhiệm:

- Điều phối bước biến `Chunk` thành `IndexedChunk`.
- Thường dùng:
  - `EmbeddingProvider`
  - `VectorStore`
- Áp dụng policy `replace-by-document_id-within-index_name` trước khi ghi mới.
- Có thể dùng helper hạ tầng như LlamaIndex nhưng phải trả về model nội bộ.

### Retriever

Vai trò hiện tại: service nội bộ gần capability, không phải port lõi.

Trách nhiệm:

- Nhận `RetrievalRequest`.
- Gọi embedding cho query.
- Gọi vector store để truy hồi.
- Map kết quả thành `RetrievalResponse`.

### Generator

Vai trò hiện tại: service nội bộ gần capability, không phải port lõi.

Trách nhiệm:

- Nhận `GenerationRequest`.
- Build prompt từ retrieved context theo quy tắc grounding.
- Gọi `LLMProvider`.
- Map kết quả thành `GeneratedAnswer`.
- Nếu không có context khả dụng thì trả trực tiếp `insufficient_context`, không gọi `LLMProvider`.

## Adapter nào dùng LlamaIndex

LlamaIndex chỉ được dùng trong infrastructure với vai trò engine phụ trợ. Các helper hoặc adapter hạ tầng có thể dùng LlamaIndex để phục vụ:

| Thành phần hạ tầng | Có thể dùng LlamaIndex | Ghi chú |
|---|---|---|
| `VectorStore` adapter | Có | Được phép dùng wrapper/backend client của LlamaIndex nhưng phải map về contract `VectorStore` nội bộ |
| `DocumentParser` adapter | Có | Chỉ như parser/reader hạ tầng, không đổi ingestion contract |
| `Chunker` helper | Có điều kiện | Chỉ khi có spec mới; hiện tại DL-006 vẫn khóa chunking theo ký tự |
| `Retriever`/`Generator` helper | Không phải mặc định | Không dùng orchestration object của LlamaIndex để thay vai trò capability service |

Ràng buộc:

- Không expose `Node`, `Document`, `QueryEngine`, `Response` của LlamaIndex ra orchestration/capability layer.
- Không dùng `Settings`, `IngestionPipeline`, `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer` làm orchestration spine của hệ thống nếu chưa có decision mới.
- Nếu LlamaIndex bị thay thế, domain và use case không phải sửa contract.

## Adapter nào dùng cloud provider

| Port | Loại adapter | Ví dụ vai trò |
|---|---|---|
| `EmbeddingProvider` | Cloud embedding adapter | Gọi API embedding |
| `LLMProvider` | Cloud LLM adapter | Gọi API chat/completion |
| `VectorStore` | Vector database adapter | Gọi SDK/query API |
| `DocumentParser` | Parser adapter | Parse text, pdf cơ bản |

## Nguyên tắc thay thế engine

- Port phải mô tả bằng ngôn ngữ nghiệp vụ hoặc kỹ thuật mức hệ thống, không gắn SDK.
- Mọi adapter phải có bài test contract tối thiểu.
- Không đưa kiểu dữ liệu riêng của provider vào domain.
- Mọi field trả về ra ngoài API phải lấy từ domain model nội bộ.
- Khi thay engine:
  - không đổi API contract
  - không đổi use case behavior đã chốt
  - chỉ thay adapter và test integration tương ứng


---

## Source: `docs/05-use-case-ingestion.md`

# 05. Use Case Ingestion

## Mục lục
- Mục tiêu
- Input / output
- Luồng xử lý
- Validation rules
- Error cases
- Definition of done
- Acceptance criteria
- Test cases mức use case

## Mục tiêu use case ingestion

Nhận một tài liệu đầu vào, chuẩn hóa thành domain model, chia chunk, sinh embedding, lưu vào vector store và trả về kết quả chỉ mục hóa.

## Input / output

### Input

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | ID tài liệu |
| `content` | string | Có | Nội dung văn bản đã chuẩn hóa cho public API MVP |
| `title` | string | Không | Tiêu đề |
| `source_type` | string | Có | Loại nguồn |
| `source_uri` | string | Không | URI nguồn |
| `metadata` | object | Không | Metadata tài liệu |
| `index_name` | string | Có | Logical index |

### Output

`DocumentIndexResult`

## Luồng xử lý chi tiết

1. Validate request mức API và use case.
2. Với public API MVP, map request trực tiếp thành `SourceDocument`.
3. Chỉ gọi `DocumentParser` nếu có ingestion path nội bộ hoặc nguồn vào chưa ở dạng văn bản chuẩn hóa.
4. Kiểm tra nội dung sau chuẩn hóa không rỗng.
5. Gọi `Chunker` tạo danh sách `Chunk`.
6. Kiểm tra danh sách chunk không rỗng.
7. Gọi `Indexer` để:
   - thay thế dữ liệu cũ nếu đã tồn tại cùng `document_id` trong `index_name`
   - sinh embedding cho từng chunk
   - map thành `IndexedChunk`
   - upsert vào `VectorStore`
8. Thu thập kết quả thành `DocumentIndexResult`.

## Validation rules

- `document_id` không rỗng.
- `index_name` không rỗng.
- `content` sau trim không được rỗng.
- `content` nên có giới hạn mặc định `1..100000` ký tự cho MVP; ngưỡng thực thi có thể override bằng config runtime.
- `document_id` nên có giới hạn mặc định `1..128` ký tự.
- `index_name` nên có giới hạn mặc định `1..64` ký tự.
- `Chunker` của MVP dùng cấu hình theo ký tự để tránh phụ thuộc tokenizer/provider:
  - `chunk_size`: mặc định `1000`, min `300`, max `2000`
  - `chunk_overlap`: mặc định `150`, min `0`, max `300`
- `chunk_overlap` không được lớn hơn hoặc bằng `chunk_size`.
- `source_type` phải thuộc tập giá trị cho phép của MVP, ví dụ `text`, `pdf`, `html`.
- Metadata tài liệu phải là object phẳng hoặc object JSON hợp lệ.
- Nếu `metadata.language` có mặt thì phải là mã ngôn ngữ ngắn ổn định, ví dụ `vi`, `en`.
- Nếu `metadata.tags` có mặt thì phải là danh sách string không rỗng phần tử.
- Tổng số chunk sinh ra không được vượt giới hạn cấu hình cứng của MVP.
  - `ingestion_chunk_count_max`: mặc định `200`, có thể override bằng config runtime.

## Error cases

| Mã lỗi gợi ý | Tình huống |
|---|---|
| `INVALID_INPUT` | Thiếu trường bắt buộc hoặc giá trị không hợp lệ |
| `DOCUMENT_PARSE_ERROR` | Parse tài liệu thất bại |
| `EMPTY_DOCUMENT` | Tài liệu rỗng sau chuẩn hóa |
| `CHUNKING_ERROR` | Không tạo được chunk hợp lệ |
| `EMBEDDING_ERROR` | Provider embedding lỗi |
| `INDEX_WRITE_ERROR` | Ghi vector store thất bại |
| `PARTIAL_INDEXED` | Chỉ mục hóa thành công một phần |

Ghi chú triển khai MVP hiện tại:

- Public API hiện chỉ khóa mode JSON text chuẩn hóa, nên nhánh `DOCUMENT_PARSE_ERROR` là cho ingestion path nội bộ hoặc phase sau.
- Nhánh `PARTIAL_INDEXED` chưa được bật trong adapter MVP hiện tại; mặc định hệ thống phản ánh thất bại toàn phần khi vector store ghi lỗi.

## Definition of done

- Tài liệu được map thành `SourceDocument`.
- Chunk được tạo với metadata chuẩn.
- Mỗi chunk hợp lệ được embed và lưu vào vector store.
- Trả về `DocumentIndexResult` phản ánh đúng số lượng đã xử lý.
- `DocumentIndexResult.replaced_document` phản ánh đúng việc có thay thế dữ liệu cũ hay không.
- Lỗi được chuẩn hóa, không lộ object hoặc stack trace framework ra contract công khai.

## Acceptance criteria

- Khi input hợp lệ và hạ tầng hoạt động, hệ thống trả `status = indexed`.
- `chunk_count` lớn hơn 0 với tài liệu đủ dài.
- `indexed_count` bằng số chunk đã lưu thành công.
- Nếu cùng `document_id` đã tồn tại trong cùng `index_name`, dữ liệu cũ phải được thay thế trước khi ghi mới.
- Nếu cùng `document_id` chưa từng tồn tại trong cùng `index_name`, `replaced_document = false`.
- Nếu cùng request ingestion được gửi lặp lại với cùng `document_id`, `index_name` và nội dung chuẩn hóa không đổi, hệ thống vẫn hợp lệ và kết quả phải tương đương về mặt nghiệp vụ.
- Mỗi chunk lưu xuống phải có:
  - `chunk_id`
  - `document_id`
  - metadata chuẩn
- Nếu tài liệu rỗng sau chuẩn hóa, use case thất bại có kiểm soát.
- Nếu một phần chunk ghi thất bại, hệ thống phải phản ánh `partial` hoặc thất bại toàn phần theo chiến lược đã cấu hình.
- Public API MVP không bắt buộc hỗ trợ upload file; nếu chưa có ingestion path riêng cho file thì contract vẫn nhất quán với mode text chuẩn hóa.
- Với adapter MVP hiện tại, partial write chưa được hỗ trợ; hành vi đang khóa là fail toàn phần khi ghi lỗi.

## Test cases mức use case

| ID | Kịch bản | Input chính | Kỳ vọng |
|---|---|---|---|
| ING-01 | Index tài liệu text hợp lệ | Nội dung ngắn hợp lệ | `status = indexed`, `indexed_count > 0` |
| ING-02 | Nội dung chỉ có khoảng trắng | `content = "   "` | Lỗi `EMPTY_DOCUMENT` hoặc `INVALID_INPUT` |
| ING-03 | Parser thất bại | File hỏng hoặc format không hỗ trợ | Lỗi `DOCUMENT_PARSE_ERROR` |
| ING-04 | Chunker tạo 0 chunk | Nội dung bất thường | Lỗi `CHUNKING_ERROR` |
| ING-05 | Embedding provider lỗi | Provider timeout | Lỗi `EMBEDDING_ERROR` |
| ING-06 | Vector store ghi lỗi toàn phần | Upsert thất bại | Lỗi `INDEX_WRITE_ERROR` |
| ING-07 | Vector store ghi lỗi một phần | Một số chunk lỗi | `status = partial`, có `errors` |
| ING-08 | Re-index cùng `document_id` | Tài liệu đã tồn tại | Dữ liệu cũ bị thay thế theo policy MVP |
| ING-09 | Gửi lại cùng tài liệu không đổi | Cùng `document_id`, `index_name`, `content` | Thành công hợp lệ, không làm sai semantics nghiệp vụ |


---

## Source: `docs/06-use-case-retrieval.md`

# 06. Use Case Retrieval

## Mục lục
- Mục tiêu
- Input / output
- Luồng xử lý
- Metadata filtering
- top_k behavior
- Error cases
- Definition of done
- Acceptance criteria
- Test cases mức use case

## Mục tiêu use case retrieval

Nhận truy vấn người dùng, thực hiện truy hồi các chunk liên quan nhất từ chỉ mục theo embedding similarity và bộ lọc metadata.

## Input / output

### Input

`RetrievalRequest`

### Output

`RetrievalResponse`

## Luồng xử lý chi tiết

1. Validate `query`, `top_k`, `index_name`, `filters`.
2. Chuẩn hóa query:
   - trim khoảng trắng
   - loại bỏ trường hợp rỗng
3. Gọi service `Retriever`.
4. Bên trong `Retriever`:
   - gọi `EmbeddingProvider` để embed query
   - gọi `VectorStore` để truy hồi theo vector + filter
   - map kết quả sang `RetrievedChunk`
5. Sắp xếp kết quả theo score giảm dần nếu adapter chưa đảm bảo.
6. Trả về `RetrievalResponse`.

## Metadata filtering

MVP hỗ trợ bộ lọc đơn giản theo phép so sánh bằng:

| Trường filter | Kiểu | Ghi chú |
|---|---|---|
| `document_id` | string | Giới hạn theo tài liệu |
| `source_type` | string | Ví dụ `pdf`, `text` |
| `language` | string | Ví dụ `vi`, `en` |
| `tags` | list[string] | Semantics chính thức của MVP là `contains-any` |

Nguyên tắc:

- Chỉ chấp nhận whitelist field đã định nghĩa.
- Filter không hợp lệ phải bị từ chối ở orchestration/capability layer.
- Nếu vector store không hỗ trợ native filter tương ứng, adapter phải fail rõ ràng hoặc degrade có kiểm soát; không được âm thầm bỏ filter.
- `tags` trong MVP dùng semantics `contains-any` và phải được giữ nhất quán giữa fake adapter, adapter thật và test contract.

## top_k behavior

- `top_k` phải > 0.
- `top_k` mặc định do API quy định, ví dụ `5`.
- `top_k` tối đa bị chặn bởi cấu hình hệ thống, ví dụ `20`.
- Nếu số chunk khả dụng nhỏ hơn `top_k`, trả về số thực có sẵn.
- Kết quả phải theo thứ tự score giảm dần.
- `top_k` phải được khóa bằng spec với giá trị mặc định/min/max, nhưng vẫn cho phép override qua config runtime.
- Không áp dụng ngưỡng score cứng ở domain nếu chưa có số liệu hiệu chỉnh cho MVP; việc cắt theo score nên để mở cho phase sau.

## Error cases

| Mã lỗi gợi ý | Tình huống |
|---|---|
| `INVALID_INPUT` | Query rỗng, top_k không hợp lệ, filter sai schema |
| `EMBEDDING_ERROR` | Embed query thất bại |
| `RETRIEVAL_ERROR` | Vector store query lỗi |
| `UNSUPPORTED_FILTER` | Filter không được hỗ trợ |

## Definition of done

- Query hợp lệ được embed và truy hồi thành công.
- Kết quả trả về đúng logical index.
- Áp dụng đúng filter và `top_k`.
- Mọi chunk trả về đều có `chunk_id`, `document_id`, `text`, `score`, `metadata`.

## Acceptance criteria

- Với query hợp lệ, hệ thống trả tối đa `top_k` chunk.
- Nếu có filter `document_id`, chỉ trả chunk thuộc tài liệu đó.
- Nếu không có kết quả, hệ thống trả `chunks = []`, không coi là lỗi hệ thống.
- Nếu filter không hợp lệ, request bị từ chối trước khi gọi adapter.
- Nếu vector store lỗi, hệ thống trả lỗi chuẩn hóa.

## Test cases mức use case

| ID | Kịch bản | Input chính | Kỳ vọng |
|---|---|---|---|
| RET-01 | Retrieval cơ bản | Query hợp lệ, `top_k=3` | Trả tối đa 3 chunk, đúng schema |
| RET-02 | Query rỗng | `"   "` | Lỗi `INVALID_INPUT` |
| RET-03 | `top_k = 0` | Query hợp lệ | Lỗi `INVALID_INPUT` |
| RET-04 | Có filter `document_id` | Query + filter | Chỉ trả chunk thuộc tài liệu chỉ định |
| RET-05 | Filter không whitelist | `filters = {"foo":"bar"}` | Lỗi `UNSUPPORTED_FILTER` hoặc `INVALID_INPUT` |
| RET-06 | Không có kết quả | Query không liên quan | `chunks = []` |
| RET-07 | Embedding provider lỗi | Provider timeout | Lỗi `EMBEDDING_ERROR` |
| RET-08 | Vector store lỗi | Query backend lỗi | Lỗi `RETRIEVAL_ERROR` |


---

## Source: `docs/07-use-case-generation.md`

# 07. Use Case Generation

## Mục lục
- Mục tiêu
- Input / output
- Luồng xử lý
- Quy tắc build prompt
- Quy tắc grounding
- Quy tắc citations
- Hành vi khi context không đủ
- Error cases
- Definition of done
- Acceptance criteria
- Test cases mức use case

## Mục tiêu use case generation

Sinh câu trả lời cho người dùng dựa trên retrieved context, có grounding rõ ràng và citation theo `chunk_id`.

## Input / output

### Input

`GenerationRequest`

### Output

`GeneratedAnswer`

## Luồng xử lý chi tiết

1. Validate `question`.
2. Xác định nguồn context:
   - nếu có `retrieved_chunks`, dùng trực tiếp
   - nếu chưa có, gọi retrieval qua `retrieval_request`
3. Kiểm tra danh sách context sau cùng.
4. Nếu danh sách context rỗng, trả trực tiếp `GeneratedAnswer` với `insufficient_context = true`, `grounded = false`, `citations = []`, `used_chunks = []` theo policy MVP.
5. Nếu có context, chọn tối đa `max_context_chunks` để build prompt.
6. Gọi service `Generator`.
7. Bên trong `Generator`:
   - build prompt theo template nội bộ
   - chèn context theo format ổn định, có `chunk_id`
   - gọi `LLMProvider`
   - hậu xử lý kết quả thành `GeneratedAnswer`
8. Trả về answer cùng citations.

## Quy tắc build prompt

Prompt phải chứa tối thiểu:

- Vai trò hệ thống: trả lời dựa trên context được cung cấp.
- Câu hỏi người dùng.
- Danh sách context đã đánh số hoặc gắn rõ `chunk_id`.
- Chỉ dẫn hành vi khi thiếu dữ liệu.
- Yêu cầu citation theo `chunk_id`.

Nguyên tắc:

- Không đưa dữ liệu ngoài retrieved context vào prompt như một sự thật hệ thống.
- Không để prompt phụ thuộc format riêng của LlamaIndex.
- Prompt phải deterministic ở cấu trúc, để dễ test.

## Quy tắc grounding

- Chỉ trả lời dựa trên retrieved context.
- Không được bịa giá, chính sách, SLA, cam kết, thời hạn, hoặc thông tin không xuất hiện trong context.
- Nếu câu hỏi vượt quá dữ liệu có sẵn, phải nói rõ là không đủ dữ liệu.
- Không suy diễn thành sự thật chắc chắn khi context chỉ gợi ý một phần.

## Quy tắc citations

- Citations phải tham chiếu bằng `chunk_id`.
- Mỗi citation trong output phải tồn tại trong `used_chunks`.
- Không phát sinh citation giả không có trong context.
- Nếu câu trả lời có nhiều ý độc lập, output nên viện dẫn tất cả chunk liên quan đã dùng.

## Hành vi khi context không đủ

- Nếu retrieval trả về rỗng:
  - `insufficient_context = true`
  - `grounded = false`
  - answer phải nói rõ không đủ dữ liệu để trả lời chắc chắn
  - orchestration/capability layer phải trả lời theo template nội bộ cố định hoặc format tương đương mà không gọi LLM
- Nếu retrieval có chunk nhưng không đủ để trả lời đầy đủ:
  - answer phải nêu phần nào có căn cứ, phần nào chưa đủ dữ liệu
  - không được bịa phần thiếu

## Error cases

| Mã lỗi gợi ý | Tình huống |
|---|---|
| `INVALID_INPUT` | Câu hỏi rỗng hoặc thiếu cả retrieval request lẫn retrieved chunks |
| `RETRIEVAL_ERROR` | Cần retrieval nhưng retrieval thất bại |
| `PROMPT_BUILD_ERROR` | Không build được prompt hợp lệ |
| `GENERATION_ERROR` | LLM provider lỗi |
| `INVALID_GENERATION_OUTPUT` | Output không map được về contract nội bộ |

## Definition of done

- Hệ thống sinh được `GeneratedAnswer` đúng schema.
- Answer có grounding theo context.
- Citation hợp lệ theo `chunk_id`.
- Khi thiếu dữ liệu, câu trả lời nêu rõ giới hạn.
- Không phụ thuộc object LlamaIndex trong output.

## Acceptance criteria

- Nếu có context đủ mạnh, câu trả lời phải chỉ dựa trên context đó.
- Nếu không đủ dữ liệu, câu trả lời phải nói rõ không đủ dữ liệu.
- `citations` chỉ chứa `chunk_id` thuộc `used_chunks`.
- Khi `retrieved_chunks` đã được truyền vào, use case không được tự ý gọi retrieval lại.
- Khi `retrieved_chunks` được truyền vào nhưng rỗng, hệ thống vẫn xử lý hợp lệ theo nhánh `insufficient_context`.
- Chỉ khi thiếu cả `retrieval_request` lẫn `retrieved_chunks` thì request mới bị từ chối.
- Khi không có context khả dụng, use case phải hoàn tất mà không gọi `LLMProvider`.

## Test cases mức use case

| ID | Kịch bản | Input chính | Kỳ vọng |
|---|---|---|---|
| GEN-01 | Generation với retrieved chunks có sẵn | Question + 2 chunk | Trả answer grounded, citations hợp lệ |
| GEN-02 | Generation tự gọi retrieval | Question + retrieval request | Gọi retrieval rồi sinh answer |
| GEN-03 | Thiếu toàn bộ context input | Chỉ có question | Lỗi `INVALID_INPUT` |
| GEN-04 | Retrieved chunks rỗng | Question + `[]` | Answer nêu không đủ dữ liệu, `insufficient_context = true` |
| GEN-05 | LLM provider lỗi | Context hợp lệ | Lỗi `GENERATION_ERROR` |
| GEN-06 | Output viện dẫn chunk không tồn tại | LLM trả citation sai | Lỗi `INVALID_GENERATION_OUTPUT` hoặc hậu xử lý loại bỏ citation sai theo policy |
| GEN-07 | Câu hỏi yêu cầu thông tin không có trong context | Context không chứa giá/chính sách | Answer từ chối suy đoán, nêu không đủ dữ liệu |


---

## Source: `docs/08-api-contract.md`

# 08. API Contract

## Mục lục
- Danh sách endpoint MVP
- Request/response schema
- Validation rules
- Error response
- Ví dụ request/response

## Danh sách endpoint MVP

| Method | Endpoint | Mục đích |
|---|---|---|
| `POST` | `/documents/index` | Ingestion và index tài liệu |
| `POST` | `/retrieve` | Truy hồi context |
| `POST` | `/generate` | Sinh câu trả lời grounded |

## Nguyên tắc chung

- Content-Type: `application/json`
- Tất cả response thành công trả JSON.
- Lỗi nghiệp vụ và lỗi hạ tầng được chuẩn hóa cùng một envelope.
- `chunk_id` là định danh citation chuẩn xuyên suốt API.
- Các giới hạn input được khóa trong spec với default + min/max cho MVP, nhưng cho phép override bằng config runtime.
- Config runtime được nạp khi khởi động ứng dụng và áp dụng thống nhất cho mọi request trong cùng một phiên bản deploy.

## POST /documents/index

### Request schema

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | ID tài liệu |
| `title` | string | Không | Tiêu đề |
| `content` | string | Có | Nội dung văn bản đã chuẩn hóa cho public API MVP |
| `source_type` | string | Có | Loại nguồn |
| `source_uri` | string | Không | URI nguồn |
| `metadata` | object | Không | Metadata tài liệu |
| `index_name` | string | Có | Logical index |

### Response schema

| Trường | Kiểu | Mô tả |
|---|---|---|
| `document_id` | string | ID tài liệu |
| `index_name` | string | Logical index |
| `chunk_count` | int | Số chunk đã tạo |
| `indexed_count` | int | Số chunk đã index |
| `status` | string | `indexed`, `partial`, `failed` |
| `errors` | list[string] | Danh sách lỗi |
| `replaced_document` | bool | Có thay thế dữ liệu cũ của cùng `document_id` trong `index_name` hay không |

### Validation rules

- `document_id`, `content`, `source_type`, `index_name` là bắt buộc.
- `content` không được rỗng sau trim.
- `metadata` phải là JSON object hợp lệ.
- `source_type` phải thuộc tập giá trị cho phép của MVP.
- `document_id`: mặc định `1..128` ký tự.
- `index_name`: mặc định `1..64` ký tự.
- `content`: mặc định `1..100000` ký tự.

### Ví dụ request

```json
{
  "document_id": "doc-001",
  "title": "Chính sách hoàn tiền",
  "content": "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày...",
  "source_type": "text",
  "source_uri": "internal://policy/refund",
  "metadata": {
    "language": "vi",
    "tags": ["policy", "refund"]
  },
  "index_name": "enterprise-kb"
}
```

### Ví dụ response

```json
{
  "document_id": "doc-001",
  "index_name": "enterprise-kb",
  "chunk_count": 3,
  "indexed_count": 3,
  "status": "indexed",
  "errors": [],
  "replaced_document": false
}
```

## POST /retrieve

### Request schema

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Có | Truy vấn người dùng |
| `top_k` | int | Không | Mặc định `5` |
| `filters` | object | Không | Bộ lọc metadata |
| `index_name` | string | Có | Logical index |

### Response schema

| Trường | Kiểu | Mô tả |
|---|---|---|
| `query` | string | Truy vấn gốc |
| `top_k` | int | Giá trị đã áp dụng |
| `index_name` | string | Logical index |
| `applied_filters` | object | Filter đã áp dụng |
| `chunks` | array | Danh sách chunk truy hồi |

Schema cho từng phần tử `chunks`:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `chunk_id` | string | ID chunk |
| `document_id` | string | ID tài liệu |
| `text` | string | Nội dung chunk |
| `score` | float | Điểm liên quan |
| `metadata` | object | Metadata chunk |

### Validation rules

- `query` không được rỗng sau trim.
- `query`: mặc định `1..2000` ký tự.
- `top_k`: mặc định `5`, min `1`, max `20`.
- `filters` chỉ nhận các khóa whitelist:
  - `document_id`
  - `source_type`
  - `language`
  - `tags`
- `filters.tags` dùng semantics `contains-any`.

### Ví dụ request

```json
{
  "query": "Khách hàng được hoàn tiền trong bao lâu?",
  "top_k": 3,
  "filters": {
    "language": "vi",
    "tags": ["refund"]
  },
  "index_name": "enterprise-kb"
}
```

### Ví dụ response

```json
{
  "query": "Khách hàng được hoàn tiền trong bao lâu?",
  "top_k": 3,
  "index_name": "enterprise-kb",
  "applied_filters": {
    "language": "vi",
    "tags": ["refund"]
  },
  "chunks": [
    {
      "chunk_id": "chunk-doc-001-0001",
      "document_id": "doc-001",
      "text": "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán.",
      "score": 0.92,
      "metadata": {
        "document_id": "doc-001",
        "chunk_id": "chunk-doc-001-0001",
        "title": "Chính sách hoàn tiền",
        "source_type": "text",
        "source_uri": "internal://policy/refund",
        "sequence_no": 1,
        "language": "vi",
        "tags": ["policy", "refund"]
      }
    }
  ]
}
```

## POST /generate

### Request schema

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `question` | string | Có | Câu hỏi người dùng |
| `index_name` | string | Không | Dùng khi cần retrieval nội bộ |
| `retrieval_request` | object | Không | Cấu hình retrieval nếu hệ thống tự retrieval |
| `retrieved_chunks` | array | Không | Context có sẵn |
| `max_context_chunks` | int | Không | Giới hạn chunk đưa vào prompt |

Quy tắc:

- Phải có ít nhất một trong hai:
  - `retrieval_request`
  - `retrieved_chunks`

Schema cho `retrieval_request`:

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Không | Nếu bỏ trống thì mặc định dùng `question` làm query retrieval |
| `top_k` | int | Không | Mặc định `5` |
| `filters` | object | Không | Filter metadata |
| `index_name` | string | Không | Cho phép override nếu muốn chỉ rõ logical index ở nhánh retrieval |

Quy tắc mapping sang domain:

- Ở orchestration/capability layer, `retrieval_request` của API phải được map thành `RetrievalRequest`.
- Nếu `retrieval_request.query` bị bỏ trống thì orchestration phải gán `query = question` trước khi gọi use case retrieval.

Schema cho từng phần tử `retrieved_chunks` giống response của `/retrieve`.

### Response schema

| Trường | Kiểu | Mô tả |
|---|---|---|
| `answer` | string | Câu trả lời cuối cùng |
| `citations` | list[string] | Danh sách `chunk_id` |
| `grounded` | bool | Có bám context hay không |
| `insufficient_context` | bool | Có thiếu dữ liệu hay không |
| `used_chunks` | array | Danh sách chunk đã dùng |

Quy tắc response:

- `citations` phải là tập con của `used_chunks[].chunk_id`.
- Nếu `used_chunks` rỗng thì `citations` phải rỗng.
- Khi `insufficient_context = true`, `grounded` phải là `false`.
- Khi `insufficient_context = true`, `answer` dùng literal mặc định của MVP:
  - `Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn.`
- Literal trên có thể override bằng config runtime, nhưng phải giữ nguyên semantics và schema response.

### Validation rules

- `question` không được rỗng.
- `question`: mặc định `1..2000` ký tự.
- `max_context_chunks`: mặc định `5`, min `1`, max `10`.
- Nếu có `retrieved_chunks`, mỗi chunk phải đủ:
  - `chunk_id`
  - `document_id`
  - `text`
  - `metadata`
- Nếu có `retrieval_request`, `index_name` phải xác định được từ `retrieval_request.index_name` hoặc từ field `index_name` ở request ngoài.
- Nếu `retrieved_chunks` là mảng rỗng, request vẫn hợp lệ và hệ thống phải trả lời theo nhánh `insufficient_context`.
- Public API MVP chưa khóa contract upload file; ingestion qua HTTP hiện dùng JSON text đơn giản.

### Ví dụ request

```json
{
  "question": "Khách hàng được hoàn tiền trong bao lâu?",
  "index_name": "enterprise-kb",
  "retrieval_request": {
    "top_k": 3,
    "filters": {
      "language": "vi"
    }
  },
  "max_context_chunks": 3
}
```

### Ví dụ response

```json
{
  "answer": "Theo tài liệu hiện có, khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán. [chunk-doc-001-0001]",
  "citations": ["chunk-doc-001-0001"],
  "grounded": true,
  "insufficient_context": false,
  "used_chunks": [
    {
      "chunk_id": "chunk-doc-001-0001",
      "document_id": "doc-001",
      "text": "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán.",
      "score": 0.92,
      "metadata": {
        "document_id": "doc-001",
        "chunk_id": "chunk-doc-001-0001",
        "title": "Chính sách hoàn tiền",
        "source_type": "text",
        "source_uri": "internal://policy/refund",
        "sequence_no": 1,
        "language": "vi",
        "tags": ["policy", "refund"]
      }
    }
  ]
}
```

## Error response

Schema lỗi chuẩn:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `error_code` | string | Mã lỗi chuẩn hóa |
| `message` | string | Mô tả ngắn |
| `details` | object | Chi tiết có kiểm soát |

### HTTP error mapping MVP

| `error_code` | HTTP status | Ghi chú |
|---|---|---|
| `INVALID_INPUT` | `400` | Lỗi validate request hoặc rule đầu vào |
| `UNSUPPORTED_FILTER` | `400` | Filter ngoài whitelist hoặc adapter không hỗ trợ theo spec |
| `DOCUMENT_PARSE_ERROR` | `422` | Input parse thất bại |
| `EMPTY_DOCUMENT` | `422` | Nội dung rỗng sau chuẩn hóa |
| `CHUNKING_ERROR` | `422` | Không tạo được chunk hợp lệ |
| `EMBEDDING_ERROR` | `502` | Provider embedding lỗi hoặc timeout |
| `INDEX_WRITE_ERROR` | `502` | Vector store ghi thất bại |
| `RETRIEVAL_ERROR` | `502` | Vector store query thất bại |
| `RETRIEVAL_REQUIRED_INDEX_MISSING` | `400` | Thiếu `index_name` để tự retrieval |
| `PROMPT_BUILD_ERROR` | `500` | Lỗi nội bộ khi build prompt |
| `GENERATION_ERROR` | `502` | LLM provider lỗi hoặc timeout |
| `INVALID_GENERATION_OUTPUT` | `502` | Provider trả output không map được về contract |

Ví dụ:

```json
{
  "error_code": "INVALID_INPUT",
  "message": "query không được để trống",
  "details": {
    "field": "query"
  }
}
```

## Runtime defaults MVP

| Cấu hình | Default | Min | Max | Ghi chú |
|---|---|---|---|---|
| `retrieval.top_k` | `5` | `1` | `20` | Áp dụng cho `/retrieve` và `retrieval_request` |
| `generation.max_context_chunks` | `5` | `1` | `10` | Giới hạn chunk đưa vào prompt |
| `ingestion.chunk_size_chars` | `1000` | `300` | `2000` | Dùng theo ký tự, không theo token |
| `ingestion.chunk_overlap_chars` | `150` | `0` | `300` | Phải nhỏ hơn `chunk_size_chars` |
| `limits.content_length` | `100000` | `1` | `100000` | Public API MVP |
| `limits.query_length` | `2000` | `1` | `2000` | Public API MVP |
| `limits.question_length` | `2000` | `1` | `2000` | Public API MVP |

Nguyên tắc override:

- Config runtime chỉ được siết chặt hoặc nới trong biên đã khóa của spec.
- Mọi thay đổi config runtime phải được phản ánh ở test cấu hình tương ứng.


---

## Source: `docs/09-test-strategy.md`

# 09. Test Strategy

## Mục lục
- Chiến lược TDD
- Phân tầng kiểm thử
- Nên mock gì và không nên mock gì
- Test pyramid đề xuất
- Test data strategy
- Acceptance criteria theo giai đoạn

## Chiến lược TDD cho dự án

Nguyên tắc:

- Viết spec trước, sau đó viết test trước code triển khai.
- Ưu tiên test từ domain rule và use case behavior.
- Chỉ viết đủ code để qua test hiện tại.
- Mỗi port mới cần có contract test tối thiểu.

Thứ tự TDD đề xuất:

1. Domain model validation và invariant.
2. Use case ingestion.
3. Use case retrieval.
4. Use case generation.
5. API contract test.
6. Integration test với adapter thật hoặc sandbox thật tối thiểu.

## Unit test vs use case test vs integration test vs API test

| Loại test | Phạm vi | Mục tiêu | Công cụ gợi ý |
|---|---|---|---|
| Unit test | Hàm, validator, mapper, prompt builder | Xác nhận logic nhỏ, deterministic | `pytest` |
| Use case test | Application service + fake port | Xác nhận behavior nghiệp vụ | `pytest` |
| Integration test | Adapter với dịch vụ thật hoặc local stub | Xác nhận tích hợp kỹ thuật | `pytest` |
| API test | FastAPI endpoint + dependency wiring | Xác nhận contract HTTP | `pytest`, `httpx` |

## Những phần nào nên mock

- `EmbeddingProvider` trong unit test và use case test.
- `LLMProvider` trong unit test và use case test.
- `VectorStore` trong unit test và use case test.
- `DocumentParser` khi đang test riêng `Chunker` hoặc use case khác.
- Clock, UUID generator nếu cần tính ổn định.
- Config runtime khi cần kiểm tra behavior override min/max mà không đổi spec mặc định.

## Những phần nào không nên mock

- Domain model và rule nội bộ.
- Mapper giữa domain model và API schema.
- Prompt builder.
- Logic validation của use case.
- Ở integration test:
  - không mock adapter đang được kiểm tra
  - không mock serialization/deserialization HTTP

## Test pyramid đề xuất

Tỷ trọng đề xuất cho MVP:

- 60% unit test
- 25% use case test
- 10% API test
- 5% integration test

Lý do:

- Phần lớn logic quan trọng nằm ở mapping, validation, orchestration.
- Adapter với dịch vụ thật nên ít nhưng đủ để chặn sai lệch contract.

## Test data strategy

Nguyên tắc:

- Dùng fixture nhỏ, đọc nhanh, có ý nghĩa nghiệp vụ.
- Có bộ tài liệu mẫu tiếng Việt cho:
  - chính sách
  - FAQ
  - hướng dẫn nội bộ
- Có bộ case thiếu dữ liệu để test grounding an toàn.
- Dữ liệu test phải deterministic, tránh ngẫu nhiên.

Danh mục dữ liệu test tối thiểu:

| Nhóm | Mục đích |
|---|---|
| `doc_valid_short` | Index tài liệu hợp lệ ngắn |
| `doc_empty` | Tài liệu rỗng |
| `doc_multi_chunk` | Tài liệu đủ dài để sinh nhiều chunk |
| `retrieval_no_match` | Query không có kết quả |
| `generation_insufficient_context` | Context thiếu dữ liệu |
| `generation_with_citation` | Context đủ để trả lời có citation |
| `doc_idempotent_reindex` | Gửi lại cùng tài liệu để kiểm tra semantics re-index/idempotency |

## Acceptance criteria theo từng giai đoạn

### Giai đoạn 1: Domain và ingestion

- Tất cả invariant chính có unit test.
- Use case ingestion có test xanh cho luồng thành công và lỗi chính.
- Có test cho `chunk_size` và `chunk_overlap` theo default/min/max đã khóa.
- Có test cho re-index/idempotency ở mức nghiệp vụ.
- API `/documents/index` có test contract cơ bản.
- `DOCUMENT_PARSE_ERROR` và `PARTIAL_INDEXED` không bắt buộc ở public MVP hiện tại; nếu chưa có ingestion path nội bộ thì chúng không phải blocker để khóa MVP HTTP.

### Giai đoạn 2: Retrieval

- Use case retrieval qua fake adapter hoạt động đúng với filter và `top_k`.
- Có test xác nhận `tags` dùng semantics `contains-any`.
- API `/retrieve` validate đúng schema và lỗi.
- Có integration test tối thiểu cho vector store adapter.

### Giai đoạn 3: Generation

- Prompt builder có unit test.
- Use case generation chứng minh:
  - grounded answer
  - insufficient context
  - citation hợp lệ
- Có test chứng minh nhánh `insufficient_context` có thể hoàn tất mà không cần gọi `LLMProvider`.
- Có test xác nhận literal/format mặc định của response `insufficient_context`.
- API `/generate` có test cho cả mode tự retrieval và mode context có sẵn.

### Giai đoạn 4: End-to-end MVP

- Có ít nhất 1 luồng:
  - index tài liệu
  - retrieve
  - generate
- Chạy qua môi trường test với provider giả hoặc sandbox ổn định.
- Không có mâu thuẫn giữa domain model, use case và API contract.
- Có kiểm tra log tối thiểu chứa `request_id`, `use_case`, `error_code` khi lỗi và `latency_ms` cơ bản.
- Public MVP chỉ yêu cầu luồng JSON text qua HTTP; parser file là hướng nội bộ hoặc phase sau.


---

## Source: `docs/11-glossary.md`

# 11. Glossary

## Mục lục
- Thuật ngữ chính

## Thuật ngữ chính

| Thuật ngữ | Giải thích |
|---|---|
| RAG | Mô hình sinh có tăng cường truy hồi. Hệ thống truy tìm ngữ cảnh trước rồi mới sinh câu trả lời. |
| chunk | Đoạn văn bản nhỏ được cắt ra từ tài liệu để làm đơn vị embedding và retrieval. |
| embedding | Biểu diễn vector của văn bản để đo độ tương đồng ngữ nghĩa. |
| retrieval | Bước truy hồi các chunk liên quan từ chỉ mục dựa trên truy vấn. |
| reranker | Thành phần xếp hạng lại kết quả retrieval bằng mô hình chuyên biệt. Không thuộc MVP hiện tại. |
| grounding | Nguyên tắc buộc câu trả lời bám vào ngữ cảnh đã truy hồi. |
| citation | Tham chiếu nguồn trong câu trả lời. Trong dự án này citation chuẩn là `chunk_id`. |
| service nội bộ gần capability | Service điều phối nhiều port lõi để thực hiện một luồng nghiệp vụ. Trong MVP này gồm `Indexer`, `Retriever`, `Generator`. |
| hot path | Luồng xử lý trực tiếp ảnh hưởng độ trễ người dùng, ví dụ `/retrieve`, `/generate`. |
| adapter | Thành phần triển khai một port để tích hợp với công nghệ cụ thể. |
| port | Interface ở ranh giới orchestration/capability với hạ tầng. |
| config runtime | Tập cấu hình được nạp khi ứng dụng khởi động để override các giá trị mặc định trong biên spec. |
| vector store | Hệ lưu trữ vector và metadata, hỗ trợ truy vấn tương đồng. |
| ingestion | Luồng tiếp nhận tài liệu, parse, chunk, embed và index. |
| generation | Luồng sinh câu trả lời từ context. |
| metadata filter | Điều kiện lọc trên metadata để giới hạn phạm vi retrieval. |
| top_k | Số lượng chunk tối đa được trả về ở retrieval. |
| chunk_size | Kích thước chunk mục tiêu trong ingestion. MVP hiện dùng theo số ký tự thay vì token. |
| chunk_overlap | Phần chồng lặp giữa hai chunk liên tiếp để giảm mất ngữ cảnh khi cắt tài liệu. |
| logical index | Tên chỉ mục logic do ứng dụng quản lý, độc lập với engine cụ thể. |
| re-index | Hành vi index lại một tài liệu đã tồn tại. MVP dùng policy `replace-by-document_id-within-index_name`. |
| idempotency | Kỳ vọng nghiệp vụ rằng cùng một request lặp lại không làm sai semantics hệ thống ngoài các thay đổi kỹ thuật được chấp nhận. |
| source document | Tài liệu nguồn sau khi parse và chuẩn hóa. |
| indexed chunk | Chunk đã có embedding và được ghi vào chỉ mục. |
| retrieved chunk | Chunk được lấy ra từ retrieval để dùng làm context. |
| insufficient context | Trạng thái không đủ ngữ cảnh để trả lời chắc chắn. |
| observability tối thiểu | Mức log/trace tối thiểu để debug MVP, ví dụ `request_id`, `use_case`, `error_code`, `latency_ms`, nhưng không lộ dữ liệu nhạy cảm. |
| ports/adapters | Kiến trúc tách orchestration/domain khỏi công nghệ hạ tầng bằng interface và adapter. |


---

## Source: `docs/14-decision-log.md`

# 14. Decision Log

## Mục lục
- Mục đích
- Cách dùng
- Trạng thái quyết định
- Quyết định đã chốt cho MVP
- Mẫu ghi quyết định mới

## Mục đích

Tài liệu này dùng để khóa các quyết định triển khai có khả năng làm lệch behavior, contract hoặc boundary của hệ thống trong lúc code.

Decision log không thay thế các tài liệu spec chính. Nó chỉ ghi lại:

- quyết định nào đã được chốt
- vì sao chốt như vậy
- quyết định đó ảnh hưởng đến đâu
- khi nào cần cập nhật test hoặc docs liên quan

## Cách dùng

- Mỗi khi phát sinh một quyết định có thể làm thay đổi behavior hoặc cách implement, phải ghi vào đây trước hoặc cùng lúc với code.
- Chỉ ghi các quyết định đủ cụ thể để team khác đọc vào có thể implement giống nhau.
- Nếu một quyết định làm thay đổi API contract, domain semantics, config bounds hoặc adapter boundary, phải cập nhật thêm tài liệu gốc liên quan.
- Không dùng file này để ghi todo mơ hồ hoặc ý tưởng chưa chốt.

## Trạng thái quyết định

| Trạng thái | Ý nghĩa |
|---|---|
| `proposed` | Đang cân nhắc, chưa được coi là spec |
| `accepted` | Đã chốt, team phải bám theo |
| `superseded` | Đã bị thay bởi quyết định mới |

## Quyết định đã chốt cho MVP

| ID | Trạng thái | Quyết định | Lý do | Ảnh hưởng |
|---|---|---|---|---|
| `DL-001` | `accepted` | Re-index policy là `replace-by-document_id-within-index_name` | Giữ semantics đơn giản và deterministic cho MVP | `ingestion`, `VectorStore`, API `/documents/index`, test idempotency |
| `DL-002` | `accepted` | `Indexer`, `Retriever`, `Generator` là service nội bộ gần với capability, không phải port lõi | Tránh over-engineer abstraction quá sớm | capability packages, `docs/04-ports-va-adapters.md` |
| `DL-003` | `accepted` | `tags` dùng semantics `contains-any` | Đủ cho MVP và dễ map sang adapter thật hoặc fake | `retrieval`, filter validation, adapter contract test |
| `DL-004` | `accepted` | Khi không có context phù hợp thì application trả `insufficient_context` trực tiếp và không gọi `LLMProvider` | Giữ behavior kiểm soát được, tránh hallucination không cần thiết | `generation`, test nhánh không gọi LLM, API `/generate` |
| `DL-005` | `accepted` | Citation chuẩn tham chiếu theo `chunk_id` và chỉ lấy từ tập `retrieved_chunks` thực tế đã dùng | Giữ traceability rõ và tránh citation bịa | generation output, response schema, test grounding |
| `DL-006` | `accepted` | Chunking MVP dùng cấu hình theo ký tự với `chunk_size = 1000`, `chunk_overlap = 150` trong biên spec | Tránh coupling vào tokenizer hoặc model cụ thể quá sớm | `config`, `chunking`, use case ingestion, tests |
| `DL-007` | `accepted` | Config runtime được nạp một lần khi ứng dụng khởi động và chỉ override trong biên spec | Giữ deploy behavior nhất quán trong từng phiên bản chạy | `config.py`, dependency wiring, runtime validation |
| `DL-008` | `accepted` | Public API MVP chỉ khóa ingestion mode JSON text chuẩn hóa; parser file chỉ là hướng nội bộ hoặc phase sau | Tránh parser file trở thành blocker của sprint đầu | API `/documents/index`, adapter scope, sprint planning |
| `DL-009` | `accepted` | Không log raw content ngoài mức tối thiểu cần cho debug | Giảm rủi ro lộ dữ liệu nhạy cảm | logging, observability, adapter/provider integration |
| `DL-010` | `accepted` | `PARTIAL_INDEXED` không thuộc public MVP hiện tại; adapter MVP mặc định fail toàn phần khi vector store ghi lỗi | Giữ contract HTTP đơn giản, tránh mở rộng orchestration ngoài phạm vi MVP | ingestion, API `/documents/index`, checklist, tests |
| `DL-011` | `accepted` | Invariant có thể được khóa bằng unit test ở domain model và model nội bộ, không bắt buộc phải có layer domain behavior riêng | Codebase hiện dùng dataclass + use case orchestration, nên cần chứng minh invariant bằng test đúng chỗ thay vì ép thêm abstraction | `docs/03`, `docs/09`, checklist, tests |
| `DL-012` | `accepted` | Public MVP được coi là đã đóng scope khi hoàn tất 3 endpoint HTTP, behavior cốt lõi, test contract/use case/integration tối thiểu và logging cơ bản; parser nội bộ, `PARTIAL_INDEXED`, adapter thật là phase sau | Tránh kéo dài vô hạn phạm vi MVP và giúp team chuyển sang phase kế tiếp với ranh giới rõ | sprint plan, checklist, review docs, phase planning |
| `DL-013` | `accepted` | Thứ tự ưu tiên sau MVP là `stabilize -> operational_hardening -> quality_evaluation -> feature_expansion` | Giữ team tập trung vào độ ổn định, khả năng vận hành và baseline đánh giá trước khi mở rộng tính năng | planning sau MVP, checklist, phase specs |
| `DL-014` | `accepted` | Feature mới sau MVP không mặc định là blocker; chỉ được ưu tiên sớm khi có yêu cầu nghiệp vụ hoặc dữ liệu benchmark rõ ràng | Tránh scope creep và tránh dùng feature mới để che vấn đề vận hành/chất lượng chưa được giải quyết | planning sau MVP, spec feature mới, review phạm vi |
| `DL-015` | `accepted` | Phase 1 `stabilize` được tách thành 3 workstream: `dev_setup_and_commands`, `ci_baseline`, `runbook_config_and_release_baseline` | Giúp chia việc và review implementation sau MVP theo đơn vị nhỏ, kiểm chứng được | docs post-MVP, phase 1 implementation planning, checklist |
| `DL-016` | `accepted` | Phase 2 `operational_hardening` được tách thành 3 workstream: `persistence_and_runtime_wiring`, `integration_resilience_and_error_mapping`, `observability_and_smoke_test` | Giúp Phase 2 bám đúng hardening scope, giao việc rõ và tránh trộn persistence, resilience, observability thành một khối mơ hồ | docs post-MVP, phase 2 planning, checklist |
| `DL-017` | `accepted` | Phase 3 `quality_evaluation` được tách thành 3 workstream: `fixtures_and_golden_cases`, `benchmark_and_baseline_metrics`, `regression_suite_and_result_storage` | Giúp Phase 3 khóa rõ dữ liệu, benchmark và regression thay vì gom chung thành một phase đánh giá mơ hồ | docs post-MVP, phase 3 planning, checklist |
| `DL-018` | `superseded` | Sau post-MVP, full migration cấu trúc `src/tuesday_rag` được **trì hoãn**; chỉ cho phép migration tăng dần khi có trigger kỹ thuật hoặc roadmap rõ ràng | Tránh refactor lớn theo cảm giác khi chưa có bằng chứng lợi ích lớn hơn chi phí delivery | feature expansion planning, architecture migration review, benchmark/regression recheck |
| `DL-019` | `accepted` | Sau Phase 3, repo **chấp nhận full migration** cấu trúc `src/tuesday_rag` theo hướng capability-oriented để scale ownership và mở rộng feature dễ hơn; migration này phải đi trước hoặc cùng lúc với feature expansion đầu tiên, nhưng phải bám boundary thực tế của codebase thay vì ép tách cơ học mọi concern thành module độc lập | Team đã có baseline vận hành, hardening và benchmark đủ để đo regress, nên chi phí migration lớn nay được chấp nhận để đổi lấy khả năng scale cấu trúc dài hạn mà vẫn giữ refactor trong biên an toàn của contract và coupling hiện có | feature expansion planning, architecture migration, benchmark/regression recheck, docs post-MVP |
| `DL-020` | `accepted` | Feature đầu tiên của Phase 4 là `internal file ingestion` qua entrypoint nội bộ, triển khai cùng nhịp hoàn tất migration capability-oriented hiện tại; không mở endpoint HTTP công khai mới trong nhịp này | Đây là hướng mở rộng có giá trị cao nhất nhưng vẫn bám ưu tiên mặc định sau MVP, tận dụng boundary `DocumentParser` đã có và mở rộng ingestion mà không làm lệch contract công khai của MVP | phase 4 planning, ingestion capability, migration verification, runbook và test |
| `DL-021` | `accepted` | Sau khi `internal file ingestion v1` ổn định với `.txt` và `.md`, nhịp mở rộng nhỏ kế tiếp của cùng capability là hỗ trợ `.html` bằng parser hạ tầng tối giản; vẫn không mở endpoint HTTP mới và không thêm dependency parsing nặng | Mở rộng parser theo từng loại file nhỏ giúp tăng giá trị ingestion nội bộ mà vẫn giữ boundary, tránh nhảy sang batching/async hay upload HTTP quá sớm | phase 4 planning, file parser adapters, runbook, tests |
| `DL-022` | `accepted` | Nhịp mở rộng nhỏ kế tiếp sau parser `.html` là batch ingestion nội bộ cho local directory qua script riêng, chỉ xử lý các extension đã hỗ trợ và tiếp tục qua từng file lỗi thay vì fail toàn batch ngay lập tức | Cách này tăng tính hữu dụng vận hành cho ingestion nội bộ mà không kéo scope sang queue, async orchestration hay endpoint công khai mới | phase 4 planning, scripts, runbook, CLI tests |
| `DL-023` | `accepted` | Batch ingestion nội bộ hỗ trợ `--recursive` theo kiểu opt-in; mặc định vẫn chỉ quét level hiện tại để giữ behavior cũ ổn định | Cho phép mở rộng utility theo local directory tree mà không làm đổi semantics command hiện có hoặc làm người dùng bất ngờ khi bật batch trên thư mục lớn | phase 4 planning, scripts, recursive CLI tests, runbook |
| `DL-024` | `accepted` | Parser `.pdf` cho internal ingestion dùng `pdftotext` của hệ thống qua subprocess adapter; nếu tool thiếu hoặc parse thất bại thì map về `DOCUMENT_PARSE_ERROR` | Tận dụng dependency hệ thống có sẵn để thêm giá trị ingestion thực tế mà không kéo thêm thư viện Python hoặc parser layout phức tạp vào repo | phase 4 planning, file parser adapters, runbook, tests |
| `DL-025` | `accepted` | Batch ingestion nội bộ hỗ trợ `--output` để lưu summary JSON ra file; command vẫn tiếp tục in summary ra `stdout` để giữ backward compatibility | Giữ trải nghiệm CLI cũ ổn định nhưng bổ sung artifact hữu ích cho review batch run, debugging và lưu kết quả thủ công | phase 4 planning, scripts, runbook, CLI tests |
| `DL-026` | `accepted` | Batch ingestion nội bộ hỗ trợ `--include` và `--exclude` theo glob pattern trên relative path; filter `exclude` thắng cuối cùng | Giúp người vận hành khoanh đúng tập file cần index mà không phải đổi cấu trúc thư mục hay tạo script ad-hoc, đồng thời giữ batch utility ở mức đơn giản | phase 4 planning, scripts, runbook, CLI tests |
| `DL-027` | `accepted` | Batch ingestion nội bộ hỗ trợ `--dry-run` để preview candidate files và `document_id` mà không ghi vào vector store | Giúp người vận hành kiểm tra trước phạm vi batch, pattern filter và document id mapping với chi phí thấp, không tạo side effect | phase 4 planning, scripts, runbook, CLI tests |
| `DL-028` | `accepted` | Chương `post-mvp` được coi là đã hoàn tất sau khi đủ 4 phase nền và nhịp đầu tiên của `feature_expansion`; các spec tiếp theo phải chuyển sang một track tài liệu mới thay vì tiếp tục mở rộng `docs/post-mvp/` | Giữ ranh giới roadmap rõ, tránh kéo dài vô hạn chương post-MVP và buộc các nhịp tiếp theo phải có mục tiêu mới tập trung hơn vào phần lõi của hệ thống | planning, decision log, closeout docs, track `core` |
| `DL-029` | `accepted` | Thứ tự ưu tiên đầu tiên của track `core` là: provider thật + env-based selection, vector store thật, container lifecycle qua lifespan, context-sufficiency policy rõ hơn, rồi mới đến retrieval hardening sâu hơn | Ở trạng thái hiện tại, adapter demo và runtime wiring còn là điểm nghẽn thực dụng hơn việc tối ưu retrieval sớm; cần dựng nền production-like trước khi benchmark và tối ưu lõi ở lớp cao hơn | track `core`, runtime, infrastructure adapters, generation policy, README |
| `DL-030` | `accepted` | Các journey docs (sprint plan MVP, review pre-code, checklist pre-code, closeout post-MVP, toàn bộ `post-mvp/`) được di chuyển sang `docs/history/`; `docs/` root từ nay chỉ chứa spec hành vi hiện hành, `docs/core/` chứa track đang mở, `docs/history/` là archive không áp dụng cho behavior hiện tại | Bộ docs ban đầu phản ánh quá trình triển khai chứ không phản ánh tổng quan dự án hiện tại; tách archive khỏi spec giúp người đọc mới và agent không phải phân loại doc nào còn áp dụng | docs layout, `docs/00-core-brief.md`, README, spec navigation |
| `DL-031` | `accepted` | Nhịp đầu tiên của track `core` — `provider_integration_and_runtime_lifecycle` theo spec 57/60 — được coi là đã hoàn tất ngày `2026-04-23`: container nhận `RuntimeConfig` tường minh, runtime factory `build_runtime_from_env` phục vụ cả HTTP app (qua FastAPI `lifespan`) lẫn internal scripts, adapter thật cho `OpenAI`, `Gemini`, `Azure OpenAI` đã có mặt cùng resilience wrapper, và startup check `pdftotext` có 3 mode `off/warn/strict`. Nhịp kế tiếp của track `core` chuyển sang `real_vector_store_adapter` (spec 58), sau đó là `generation_context_policy` (spec 59), rồi `retrieval_core_hardening` (spec 56) | Trạng thái spec và overview cần phản ánh đúng thực tế codebase để người đọc mới (và agent) không tiếp tục coi provider/lifecycle là điểm nghẽn; đồng thời chốt rõ nhịp đang mở để tránh mở nhiều workstream song song ngoài biên của track `core` | `docs/core/55-core-track-overview.md`, `docs/core/README.md`, spec 57, spec 60, `docs/00-core-brief.md` |
| `DL-032` | `accepted` | Nhịp `real_vector_store_adapter` (spec 58) chọn `Qdrant` làm backend v1 và cho phép **selective adoption** của LlamaIndex chỉ trong `infrastructure/` với vai trò adapter/helper hạ tầng; không dùng LlamaIndex orchestration objects (`Settings`, `IngestionPipeline`, `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer`) và không để `Node`, `Document`, `NodeWithScore`, `Response` chảy ra ngoài `infrastructure/` | Cần tận dụng integration có sẵn để giảm lượng code adapter phải tự viết, nhưng vẫn giữ nguyên boundary, domain model, public HTTP contract và các semantics đã khóa (`replace-by-document_id-within-index_name`, `tags = contains-any`, citation theo `chunk_id`, không gọi `LLMProvider` khi thiếu context). `Qdrant` phù hợp hơn `pgvector` cho v1 vì semantics filter map tự nhiên hơn và đường đi integration test gọn hơn | spec 58, `docs/00-core-brief.md`, `docs/04-ports-va-adapters.md`, `docs/core/55-core-track-overview.md`, `docs/core/README.md` |
| `DL-033` | `accepted` | Nhịp `generation_context_policy` (spec 59) dùng deterministic context-sufficiency policy ở application layer trước khi gọi `LLMProvider`. V1 giữ rule nền: `used_chunks=[]` thì `insufficient_context=true`; nếu overlap giữa meaningful question tokens và context tokens thấp hơn ngưỡng policy thì cũng trả `insufficient_context`; với câu hỏi dạng chi tiết định lượng/thời gian (`bao lau`, `bao nhieu`, `khi nao`, `muc phi`, `gia bao nhieu`), context còn phải chứa signal hỗ trợ tương ứng (ví dụ số hoặc đơn vị thời gian). Khi policy kết luận context chưa đủ, `used_chunks` vẫn được trả về để giữ traceability | Cần thay heuristic inline `_has_sufficient_context` bằng rule được nêu rõ, kiểm chứng được và không phụ thuộc provider cụ thể trong v1. Cách này giữ nguyên public contract `/generate`, tiếp tục không gọi `LLMProvider` khi context không đủ, và bảo toàn semantics `citations ⊆ used_chunks` cùng `insufficient_context=true -> grounded=false` | spec 59, `src/tuesday/rag/generation/`, tests generation/regression, `docs/00-core-brief.md`, `docs/core/55-core-track-overview.md`, `docs/core/README.md` |
| `DL-034` | `accepted` | Nhịp `retrieval_core_hardening` (spec 56) dùng deterministic post-retrieval ranking policy trong `RetrieverService`: rerank candidate theo lexical coverage của query trên `chunk.text`; nếu đã có candidate overlap meaningful tokens với query thì loại candidate overlap bằng `0`; thứ tự ưu tiên là `overlap_count`, `overlap_ratio`, rồi mới đến `raw vector score` | Cần một hardening nhỏ nhưng áp dụng được cho mọi backend hiện có (`memory`, `file`, `qdrant`) mà không đổi public API và không kéo thêm hybrid retrieval hay model reranker quá sớm. Policy này giảm rủi ro chunk "score dương nhưng không thực sự bám query", đồng thời vẫn giữ vector store là nguồn recall ban đầu | spec 56, `src/tuesday/rag/retrieval/`, regression retrieval, `docs/00-core-brief.md`, `docs/core/55-core-track-overview.md`, `docs/core/README.md` |

## Mẫu ghi quyết định mới

Khi có quyết định mới, ghi theo mẫu:

```md
| `DL-010` | `accepted` | Regex `document_id` là `^[a-zA-Z0-9._-]{1,128}$` | Giảm nhập liệu mơ hồ và dễ dùng làm key kỹ thuật | validator, API contract, tests |
```

Gợi ý những quyết định có thể cần ghi tiếp trong lúc triển khai:

- regex hợp lệ cho `document_id`
- regex hợp lệ cho `index_name`
- source_type whitelist cụ thể cho MVP
- strategy kỹ thuật để adapter vector store thực thi replace policy
- literal mặc định cho response `insufficient_context`


---

## Source: `docs/15-golden-cases-va-fixtures.md`

# 15. Golden Cases Và Fixtures

## Mục lục
- Mục đích
- Nguyên tắc dùng fixture
- Bộ dữ liệu vàng cho MVP
- Golden cases theo endpoint
- Quy tắc cập nhật

## Mục đích

Tài liệu này khóa bộ dữ liệu mẫu và các hành vi chuẩn để team dùng chung khi:

- review spec
- viết unit test và API contract test
- kiểm tra regression khi thay adapter
- demo luồng MVP

Mục tiêu là mọi người cùng bám vào một tập case nhỏ nhưng đủ đại diện, thay vì mỗi người tự nghĩ dữ liệu test khác nhau.

## Nguyên tắc dùng fixture

- Fixture phải deterministic và không phụ thuộc dịch vụ ngoài để khẳng định behavior ở orchestration/capability layer.
- Nội dung mẫu không chứa dữ liệu thật hoặc thông tin nhạy cảm.
- Ngôn ngữ của fixture không bị khóa bởi language rule của source code, nhưng baseline mặc định của repo ưu tiên tiếng Việt để khớp bộ docs và luồng đánh giá chất lượng.
- Dùng lại cùng một bộ fixture cho unit test, API contract test và tài liệu ví dụ khi có thể.
- Nếu adapter thật sinh kết quả không hoàn toàn deterministic, golden cases chỉ khóa các phần behavior cần ổn định ở orchestration/API contract.

## Bộ dữ liệu vàng cho MVP

### Fixture A: tài liệu tiếng Việt ngắn, một câu trả lời rõ

- `document_id`: `doc-refund-001`
- `index_name`: `enterprise-kb`
- `source_type`: `text`
- `title`: `Chính sách hoàn tiền`
- `metadata.language`: `vi`
- `metadata.tags`: `["policy", "refund"]`
- Nội dung cốt lõi: khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán.

Mục đích:

- test ingestion thành công
- test retrieval tiếng Việt
- test generation có grounding và citation

### Fixture B: tài liệu dài đủ để sinh nhiều chunk

- `document_id`: `doc-onboarding-001`
- `index_name`: `enterprise-kb`
- `source_type`: `text`
- `title`: `Hướng dẫn onboarding nhân sự`
- `metadata.language`: `vi`
- `metadata.tags`: `["hr", "onboarding"]`
- Nội dung dài hơn `chunk_size` để buộc tạo nhiều chunk

Mục đích:

- test chunking
- test metadata cho nhiều chunk
- test retrieval với `top_k > 1`

### Fixture C: tài liệu rỗng hoặc chỉ chứa khoảng trắng

- `document_id`: `doc-empty-001`
- `index_name`: `enterprise-kb`
- `source_type`: `text`
- `content`: rỗng sau trim

Mục đích:

- test validation error của `/documents/index`

### Fixture D: query không match

- Query mẫu: `Công ty có chính sách cấp xe công cho toàn bộ thực tập sinh không?`
- `index_name`: `enterprise-kb`
- Filters: không có hoặc filter hợp lệ nhưng không match

Mục đích:

- test `/retrieve` trả `chunks = []`
- test `/generate` trả `insufficient_context`

## Golden cases theo endpoint

### POST /documents/index

Case 1: index tài liệu hợp lệ

- Input: Fixture A
- Kỳ vọng:
  - HTTP thành công
  - `chunk_count >= 1`
  - `indexed_count = chunk_count`
  - `status = "indexed"`
  - `errors = []`
  - `replaced_document = false` ở lần đầu

Case 2: index lại cùng `document_id` và `index_name`

- Input: Fixture A lặp lại
- Kỳ vọng:
  - semantics replace được áp dụng
  - request vẫn thành công
  - `replaced_document = true`

Case 3: content rỗng sau trim

- Input: Fixture C
- Kỳ vọng:
  - HTTP validation error hoặc domain error map đúng contract
  - không gọi chunking/embedding/index thật

### POST /retrieve

Case 4: query match đúng tài liệu chính sách hoàn tiền

- Input:
  - query: `Khách hàng được hoàn tiền trong bao lâu?`
  - `index_name = "enterprise-kb"`
  - `filters.language = "vi"`
  - `filters.tags = ["refund"]`
- Kỳ vọng:
  - HTTP thành công
  - `chunks` không rỗng
  - ít nhất 1 chunk có `document_id = "doc-refund-001"`
  - `applied_filters` phản ánh đúng filter hợp lệ đã nhận

Case 5: query không match dữ liệu nào

- Input: Fixture D
- Kỳ vọng:
  - HTTP thành công
  - `chunks = []`
  - không coi đây là lỗi hệ thống

Case 6: filter sai whitelist

- Input: filter có khóa ngoài spec
- Kỳ vọng:
  - validation error
  - không gọi vector store

### POST /generate

Case 7: generation dùng `retrieved_chunks` có sẵn

- Input:
  - `question = "Khách hàng được hoàn tiền trong bao lâu?"`
  - `retrieved_chunks` lấy từ Case 4
- Kỳ vọng:
  - HTTP thành công
  - `insufficient_context = false`
  - `grounded = true`
  - `answer` bám vào nội dung 7 ngày
  - `citations` chỉ chứa `chunk_id` thuộc tập `retrieved_chunks`

Case 8: generation tự retrieval bằng `retrieval_request`

- Input:
  - `question = "Khách hàng được hoàn tiền trong bao lâu?"`
  - `retrieval_request.index_name = "enterprise-kb"`
  - `retrieval_request.filters.tags = ["refund"]`
- Kỳ vọng:
  - retrieval nội bộ hoạt động
  - `retrieval_request.query` mặc định lấy từ `question` nếu bị bỏ trống
  - response grounded và có citation hợp lệ

Case 9: generation với context không đủ

- Input:
  - `question` lấy từ Fixture D
  - `retrieval_request.index_name = "enterprise-kb"`
- Kỳ vọng:
  - HTTP thành công
  - `insufficient_context = true`
  - `grounded = false`
  - `citations = []`
  - `LLMProvider` không bị gọi

## Quy tắc cập nhật

- Mỗi khi thay đổi spec hoặc config bounds có thể làm đổi expected behavior, phải cập nhật tài liệu này và test tương ứng.
- Không thêm fixture mới nếu chưa có nhu cầu behavior rõ ràng; ưu tiên giữ bộ fixture nhỏ và dễ hiểu.
- Nếu xuất hiện regression mà không có golden case tương ứng, phải bổ sung golden case trước hoặc cùng lúc với fix.


---

## Source: `docs/16-implementation-guardrails.md`

# 16. Implementation Guardrails

## Mục lục
- Mục tiêu
- Guardrails về scope MVP
- Guardrails về boundary kiến trúc
- Guardrails về behavior
- Guardrails về test và tài liệu
- Dấu hiệu đang lệch khỏi đường ray

## Mục tiêu

Tài liệu này là hàng rào triển khai để giữ team bám đúng spec MVP, tránh hai kiểu lệch phổ biến:

- thêm tính năng ngoài phạm vi khi code
- làm sai boundary khiến việc thay engine hoặc giữ behavior ổn định trở nên khó

Nếu một thay đổi vi phạm guardrail, mặc định phải dừng lại và ghi quyết định mới vào decision log trước khi tiếp tục.

## Guardrails về scope MVP

- Không thêm `reranker` vào sprint đầu.
- Không thêm hybrid retrieval vào sprint đầu.
- Không thêm async ingestion, queue hoặc batch orchestration nếu chưa có nhu cầu thật từ runtime hiện tại.
- Không thêm streaming response cho `/generate` trong MVP.
- Không thêm multi-tenant, RBAC hoặc workflow quản trị người dùng.
- Không biến parser file thành blocker của public API MVP; public contract vẫn là JSON text chuẩn hóa.

## Guardrails về boundary kiến trúc

- Domain và orchestration/capability layer không được phụ thuộc trực tiếp vào object model của LlamaIndex.
- Domain và orchestration/capability layer không được trả hoặc nhận object SDK của vector store, embedding provider hoặc LLM provider.
- Mọi object framework-specific phải được map về model nội bộ trước khi đi vào orchestration/capability layer.
- `Indexer`, `Retriever`, `Generator` phải giữ vai trò service nội bộ gần capability, không bị đẩy xuống thành adapter hoặc kéo lên thành public framework abstraction.
- API layer chỉ làm nhiệm vụ nhận request, map schema, gọi use case, map response và lỗi.
- Business rules, validation nghiệp vụ và semantics của `insufficient_context`, `grounded`, `citations` phải nằm ở orchestration/domain, không nằm rải trong adapter.

## Guardrails về behavior

- Re-index phải bám đúng policy `replace-by-document_id-within-index_name`.
- `tags` phải giữ semantics `contains-any` trừ khi có quyết định mới được ghi rõ.
- Khi không có context phù hợp, orchestration/capability layer phải trả `insufficient_context` và không gọi `LLMProvider`.
- Citation chỉ được tham chiếu theo `chunk_id` và chỉ lấy từ tập `retrieved_chunks` thực tế đã dùng.
- Runtime defaults chỉ được override trong biên spec đã khóa; không để config làm thay đổi public contract ngầm.
- Không log raw content hoặc dữ liệu nhạy cảm ngoài mức tối thiểu cần cho debug.

## Guardrails về test và tài liệu

- Mọi thay đổi behavior đều phải đi cùng test thể hiện behavior đó.
- Mọi thay đổi liên quan contract, config bounds hoặc semantics đều phải cập nhật tài liệu gốc tương ứng.
- Nếu fix bug nhưng bug đó chưa có golden case, phải bổ sung golden case.
- Ưu tiên fake port ở unit/use case test; chỉ dùng integration test cho wiring hoặc adapter-specific behavior.
- Không chấp nhận một thay đổi “tạm thời” làm sai boundary mà không có issue và quyết định rõ ràng.

## Dấu hiệu đang lệch khỏi đường ray

- Code ở orchestration/capability layer bắt đầu dùng trực tiếp object của engine hoặc provider.
- Adapter bắt đầu quyết định output schema, citation format hoặc prompt contract thay cho orchestration.
- Một endpoint mới xuất hiện nhưng không có spec và không nằm trong sprint plan.
- Config được dùng để mở rộng phạm vi behavior thay vì chỉ override trong biên đã khóa.
- Test phải sửa hàng loạt chỉ vì semantics chưa được khóa rõ.
- Team bắt đầu nói “cứ dựng trước cho tương lai” đối với các hạng mục không thuộc MVP.


---

## Source: `docs/core/55-core-track-overview.md`

# 55. Core Track Overview

## Mục lục

- Bối cảnh
- Mục tiêu
- Phạm vi
- Ngoài phạm vi mặc định
- Ưu tiên triển khai hiện tại
- Workstream đề xuất
- Acceptance criteria của track

## Bối cảnh

Sau khi chương `post-mvp` đã hoàn tất, repo không còn ở trạng thái thiếu baseline vận hành, thiếu benchmark hay thiếu utility nội bộ tối thiểu. Vì vậy, giai đoạn kế tiếp nên chuyển trọng tâm sang phần lõi của hệ thống RAG thay vì tiếp tục mở rộng utility xung quanh.

Track `core` được tạo ra để làm đúng việc đó.

## Mục tiêu

- nâng chất lượng retrieval trên benchmark hiện có
- nâng chất lượng grounding và citation của generation
- giảm các quyết định heuristic quá mong manh trong phần lõi
- chuẩn bị đường đi cho backend retrieval/store bền hơn nếu benchmark chứng minh cần thiết

## Phạm vi

Các hạng mục phù hợp với track này gồm:

- ranking, filtering, chunk selection và retrieval policy
- cải thiện prompt grounding hoặc cách chọn context cho generation
- thay hoặc mở rộng adapter storage/retrieval để phục vụ mục tiêu chất lượng hoặc hiệu năng lõi
- benchmark và regression mới gắn trực tiếp với behavior lõi

## Ngoài phạm vi mặc định

Các hạng mục sau không nên là ưu tiên mặc định của track `core`:

- endpoint HTTP công khai mới
- giao diện người dùng
- workflow quản trị
- parser file mới chỉ vì tiện ích vận hành
- utility CLI nhỏ lẻ không tác động trực tiếp đến retrieval hoặc generation quality

## Ưu tiên triển khai hiện tại

Sau khi rà lại codebase hiện tại, track `core` ưu tiên theo thứ tự sau:

1. ~~thêm provider thật cho `EmbeddingProvider` và `LLMProvider`, với chọn adapter theo env trong container~~ — **đã xong** (spec 57/60, `2026-04-23`)
2. ~~thay vector store demo hiện tại bằng adapter thật `Qdrant`, với selective adoption của LlamaIndex chỉ trong `infrastructure/`, đồng thời khóa semantics `filters`, `score ordering` và `replace-by-document_id`~~ — **đã xong** (spec 58, `2026-04-23`)
3. ~~chuyển container vào app lifespan thay vì khởi tạo ở import-time~~ — **đã xong** (spec 57/60, `2026-04-23`)
4. ~~thay heuristic `_has_sufficient_context` bằng logic được đặc tả rõ hoặc delegate sang prompt/LLM khi đã có provider thật~~ — **đã xong** (spec 59, `2026-04-23`)
5. ~~khóa rõ phụ thuộc hệ thống `pdftotext` trong README và cân nhắc startup check tùy chọn cho PDF ingestion~~ — **đã xong** (DL-024 + `TUESDAY_PDF_STARTUP_CHECK_MODE`)

Lý do của thứ tự này là:

- contract và boundary chính của hệ thống đã sẵn sàng cho adapter thật
- tốc độ và tính thực dụng của hệ thống hiện tại bị chặn nhiều hơn bởi adapter demo và wiring runtime, không chỉ bởi heuristic retrieval
- việc nâng retrieval quality sâu hơn sẽ đáng tin hơn sau khi runtime/provider/store đã sát production hơn

## Workstream đề xuất

Track `core` ban đầu được chia thành các workstream sau:

1. ~~`provider_integration_and_runtime_lifecycle`~~ — **đã xong** (`2026-04-23`, spec 57/60 + DL-031)
2. ~~`real_vector_store_adapter`~~ — **đã xong** (`2026-04-23`, spec 58 + DL-032)
3. ~~`generation_context_policy`~~ — **đã xong** (`2026-04-23`, spec 59 + DL-033)
4. ~~`retrieval_core_hardening`~~ — **đã xong** (`2026-04-23`, spec 56 + DL-034)

Hiện tại toàn bộ nhóm spec nền ban đầu của track `core` đã hoàn tất. Nhịp kế tiếp nên bắt đầu từ spec/decision mới thay vì tiếp tục mở rộng ngầm trong track này.

Quyết định đã khóa làm nền cho các nhịp đã hoàn tất:

- backend vector store v1 là `Qdrant`
- context-sufficiency policy là deterministic rule ở application layer trước khi gọi `LLMProvider`
- retrieval hardening v1 là post-retrieval lexical coverage reranking/filter trong `RetrieverService`
- public contract vẫn giữ nguyên; mọi cải tiến retrieval phải chứng minh bằng regression/benchmark thay vì đổi API

## Acceptance criteria của track

Một nhịp trong `core` chỉ được coi là done khi:

- có spec và decision rõ cho behavior mới
- có benchmark hoặc regression thể hiện thay đổi ở phần lõi
- không làm lệch public contract nếu chưa có decision mới
- tài liệu phản ánh đúng implementation thật


---

## Source: `docs/core/56-spec-retrieval-core-hardening-v1.md`

# 56. Spec Retrieval Core Hardening v1

## Trạng thái

`accepted` (`2026-04-23`)

## Mục lục

- Mục tiêu
- Vị trí trong backlog
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Giả thuyết kỹ thuật
- Success criteria
- Verification mong muốn

## Mục tiêu

Xác định nhịp đầu tiên để cải thiện phần lõi retrieval của hệ thống trên baseline hiện tại, trước khi mở thêm capability lớn hoặc thay toàn bộ framework.

## Vị trí trong backlog

Tài liệu này vẫn còn hiệu lực, nhưng **không còn là nhịp implementation đầu tiên của track `core`**.

Theo thứ tự ưu tiên mới, `retrieval_core_hardening` nên đi sau:

1. provider thật + env-based selection
2. vector store thật
3. container lifecycle qua lifespan
4. context-sufficiency policy rõ hơn

Lý do là các bước trên sẽ tạo nền thực tế hơn để đo retrieval quality, thay vì tối ưu retrieval trên adapter demo và runtime wiring tạm thời.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- ingestion nội bộ đã đủ dùng cho việc đưa dữ liệu thật vào hệ thống
- benchmark và regression đã tồn tại để đo tác động của thay đổi
- retrieval hiện vẫn còn khá tối giản, nên đây là nơi có tiềm năng tăng giá trị lớn cho chất lượng đầu ra
- tuy nhiên, việc triển khai provider/store thật hiện được ưu tiên trước để tránh tối ưu sai mặt bằng kỹ thuật

## Phạm vi v1

Nhịp `v1` của `retrieval_core_hardening` khóa một cải tiến nhỏ nhưng đo được ở application layer:

- giữ nguyên vector query ở từng adapter store hiện có
- thêm post-retrieval reranking trong `RetrieverService` theo lexical coverage của query trên `chunk.text`
- nếu có ít nhất một candidate có overlap meaningful tokens với query, loại các candidate overlap bằng `0`
- sắp xếp candidate còn lại theo `overlap_count`, rồi `overlap_ratio`, rồi mới đến `raw vector score`
- thêm unit/regression test để khóa failure mode "score vector dương nhưng chunk không thực sự bám query"

## Ngoài phạm vi v1

- rewrite toàn bộ core sang framework khác
- hybrid retrieval đầy đủ nếu chưa có benchmark chứng minh cần
- reranker phụ thuộc model ngoài nếu chưa có baseline cho vấn đề đang gặp
- thay semantics filter hoặc đổi public API
- thay prompt generation để bù cho retrieval

## Giả thuyết kỹ thuật

Giả thuyết đã được chốt cho v1:

- với backend vector thật hoặc demo, vẫn có thể xuất hiện candidate có `score > 0` nhưng không chứa từ khóa hữu ích của câu hỏi
- một lớp rerank/filter deterministic ở `RetrieverService` là đủ nhỏ để áp dụng thống nhất cho mọi backend hiện có
- lexical coverage là tín hiệu an toàn hơn việc tăng complexity sang hybrid/BM25/reranker model ngay trong nhịp đầu

## Success criteria

- có decision mới khóa hướng retrieval đầu tiên được chọn
- `RetrieverService` áp dụng post-retrieval ranking policy provider-independent
- có unit test chứng minh chunk overlap tốt hơn được ưu tiên hơn chunk chỉ có raw score cao
- có regression test chứng minh candidate zero-overlap bị loại khi đã có candidate bám query
- smoke test hiện có không đổi contract

## Verification mong muốn

- unit test cho ranking policy và integration của `RetrieverService`
- regression test cho failure mode retrieval vừa được nhắm tới
- smoke test hiện có vẫn pass


---

## Source: `docs/core/57-spec-provider-integration-and-runtime-lifecycle-v1.md`

# 57. Spec Provider Integration And Runtime Lifecycle v1

## Migration Note

Tài liệu này mô tả hướng ưu tiên của workstream runtime/provider trước khi migration package hoàn tất ngày `2026-04-23`.

Khi đọc tài liệu này ở trạng thái repo hiện tại, cần quy chiếu như sau:

- app shell hiện tại nằm ở `src/tuesday/api/`
- runtime/config hiện tại nằm ở `src/tuesday/runtime/`
- capability `rag` hiện tại nằm ở `src/tuesday/rag/`
- app entrypoint hiện tại là `python -m uvicorn tuesday.api.app:app --reload`
- env prefix hiện tại là `TUESDAY_`
- `src/tuesday_rag/` đã bị loại bỏ khỏi codebase; mọi nhắc đến path này bên dưới là historical reference

## Trạng thái

`accepted` — đã triển khai ngày `2026-04-23`. Container nhận `RuntimeConfig` tường minh, factory `build_runtime_from_env` dựng runtime cho cả HTTP app (qua `lifespan`) lẫn internal scripts, và adapter thật cho `OpenAI`, `Gemini`, `Azure OpenAI` đã có mặt trong `src/tuesday/rag/infrastructure/providers_vendor.py`. Xem DL-031.

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Quyết định thiết kế cần khóa
- Success criteria
- Verification mong muốn

## Mục tiêu

Thiết lập nền runtime đủ gần production để các nhịp core tiếp theo không tiếp tục dựa trên provider demo và container wiring khởi tạo quá sớm.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- contract `EmbeddingProvider`, `LLMProvider` và boundary adapter đã sẵn sàng
- container hiện là nơi hợp lý để chọn adapter theo env
- app wiring ở import-time làm test và override env dễ bị bẩn ngữ cảnh hơn mức cần thiết

Vì vậy, nhịp đầu tiên của track `core` nên khóa đường đi cho provider thật và app lifecycle rõ ràng.

## Phạm vi v1

Nhịp này nên ưu tiên:

- thêm adapter thật cho `OpenAI`, `Gemini`, `Azure`
- chọn provider theo env-based selection trong container/runtime wiring
- giữ provider demo/fake cho test và local benchmark khi cần
- chuyển container creation vào FastAPI lifespan thay vì khởi tạo tại import-time
- giữ boundary hiện có giữa `api`, `runtime`, `domain` và `infrastructure`
- đảm bảo internal scripts vẫn có entrypoint rõ để tạo runtime/container ngoài HTTP app
- document rõ phụ thuộc hệ thống `pdftotext` trong README
- cân nhắc startup check tùy chọn cho `pdftotext` khi cấu hình ingestion PDF được dùng

## Ngoài phạm vi v1

- đổi public API
- rewrite toàn bộ app bootstrap
- tối ưu retrieval ranking sâu
- thay vector store thật trong cùng nhịp nếu điều đó làm scope implementation quá lớn

## Quyết định thiết kế cần khóa

- env key nào quyết định provider embedding và provider generation
- demo provider còn tồn tại như fallback mặc định hay chỉ cho test
- startup check `pdftotext` là warning, fail-fast, hay opt-in theo env
- internal scripts dùng cùng runtime factory nào với HTTP app

## Success criteria

- có spec implementation cụ thể cho provider selection và app lifespan wiring
- có mapping env rõ cho ít nhất `OpenAI`, `Gemini`, `Azure`
- có test chứng minh app/test không còn phụ thuộc import-time container state
- README nêu rõ dependency `pdftotext` và behavior hiện tại nếu tool thiếu

Implementation detail ban đầu của nhịp này được tiếp tục ở:

- `60-spec-provider-runtime-implementation-v1.md`

## Verification mong muốn

- unit test cho runtime/container selection
- API test chứng minh app wiring qua lifespan vẫn hoạt động
- smoke test hiện có vẫn pass
- kiểm tra manual cho case thiếu `pdftotext` nếu startup check được bật


---

## Source: `docs/core/58-spec-real-vector-store-adapter-v1.md`

# 58. Spec Real Vector Store Adapter v1

## Trạng thái

`accepted` (`2026-04-23`)

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Semantics phải khóa trước khi code
- Success criteria
- Verification mong muốn

## Mục tiêu

Thay adapter vector store demo hiện tại bằng một adapter thật, với semantics được khóa rõ để không làm lệch behavior lõi khi chuyển nền lưu trữ.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- `VectorStore` protocol đã đủ để thêm adapter thật
- bottleneck thực dụng của hệ thống không chỉ nằm ở heuristic mà còn nằm ở adapter demo hiện tại
- việc tiếp tục tối ưu retrieval trên storage demo sẽ làm benchmark khó đại diện cho production hơn

## Phạm vi v1

Nhịp này nên ưu tiên:

- triển khai adapter thật với backend **`Qdrant`**
- cho phép dùng LlamaIndex theo mô hình **selective adoption** chỉ trong `infrastructure/`
- map đầy đủ contract `replace_document` và `query`
- khóa semantics `tags = contains-any`
- khóa semantics filter cho các field metadata còn lại
- khóa quy ước sắp xếp score trả về để tương thích behavior hiện có
- xác định rõ chiến lược `replace-by-document_id-within-index_name` trên backend thật
- thêm integration test cho adapter mới

## Ngoài phạm vi v1

- `pgvector`
- hybrid retrieval
- reranker
- multi-store federation
- tối ưu advanced indexing ngoài nhu cầu contract hiện có
- pivot sang mô hình để LlamaIndex điều phối toàn bộ pipeline

## Quyết định đã khóa cho nhịp này

- Backend v1 là **`Qdrant`**.
- LlamaIndex chỉ được dùng như adapter/helper hạ tầng trong `src/tuesday/rag/infrastructure/`.
- Không dùng `Settings`, `IngestionPipeline`, `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer` hoặc bất kỳ orchestration object nào của LlamaIndex.
- Không để `Document`, `Node`, `NodeWithScore`, `Response` hoặc object framework tương tự chảy ra ngoài `infrastructure/`.
- `domain`, `use_case`, `service`, `api` và public HTTP contract phải giữ nguyên.
- Implementation v1 hiện tại dùng `qdrant-client` trực tiếp; selective adoption của LlamaIndex vẫn được phép về mặt boundary nhưng chưa được dùng trong nhịp này.

## Semantics phải khóa trước khi code

- filter `tags` tiếp tục là `contains-any` tuyệt đối (theo DL-003)
- backend score được tin như nguồn sort chính; adapter vẫn phải trả kết quả theo thứ tự giảm dần của score để khớp `RetrievalResponse`
- chưa introduce thêm tầng normalize score ở application layer trong v1
- `replace_document` giữ semantics `replace-by-document_id-within-index_name`; strategy kỹ thuật v1 là delete theo `document_id + index_name` rồi upsert lại toàn bộ chunk của document trong cùng adapter operation, với integration test chứng minh behavior không lệch contract

## Success criteria

- backend `Qdrant` và boundary selective adoption của LlamaIndex đã được chốt rõ
- có implementation spec đủ chi tiết để code trực tiếp mà không phải quyết định lại kiến trúc
- có integration test chứng minh semantics query và replace không lệch
- benchmark/smoke/regression tối thiểu vẫn pass trên adapter mới hoặc trên fake đủ tương thích

## Verification mong muốn

- contract test cho `VectorStore`
- integration test cho query filters và score ordering
- integration test cho `replace-by-document_id-within-index_name`
- smoke test `index -> retrieve -> generate`
- benchmark so sánh với baseline trước đó nếu có thể

## Gợi ý phạm vi code change

Phạm vi thay đổi nên được giữ ở mức tối thiểu:

- thêm adapter vector store mới trong `src/tuesday/rag/infrastructure/`
- thêm mapper giữa domain model và object hạ tầng của `Qdrant`/LlamaIndex
- mở rộng `runtime/config.py` và `runtime/container.py` để chọn backend mới
- nếu `Qdrant` được ghép với demo embedding backend, dùng demo provider dạng dense fixed-size thay vì hash embedding độ dài biến thiên
- thêm integration test cho adapter mới

Các phần không nên đổi trong nhịp này:

- `src/tuesday/rag/domain/`
- `src/tuesday/rag/ingestion/`
- `src/tuesday/rag/retrieval/`
- `src/tuesday/rag/generation/`
- API contract hiện có


---

## Source: `docs/core/59-spec-generation-context-policy-v1.md`

# 59. Spec Generation Context Policy v1

## Trạng thái

`accepted` (`2026-04-23`)

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Quyết định cần khóa
- Success criteria
- Verification mong muốn

## Mục tiêu

Thay heuristic `_has_sufficient_context` bằng một policy được đặc tả rõ, kiểm chứng được và phù hợp hơn với lúc hệ thống đã có provider thật.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- logic `sufficient_context` đang dựa nhiều vào heuristic token overlap
- heuristic này hữu ích ở giai đoạn đầu nhưng chưa đủ rõ để coi là policy dài hạn
- khi có provider thật, hệ thống có thể cân nhắc delegate một phần quyết định này vào prompt/LLM thay vì tự suy luận bằng heuristic mỏng

## Phạm vi v1

Nhịp này nên ưu tiên:

- mô tả rõ policy `insufficient_context` mong muốn ở level behavior
- quyết định xem policy này là deterministic rule, LLM-assisted rule, hay hybrid
- giữ nguyên public contract của `/generate`
- giữ traceability giữa `used_chunks`, `grounded`, `insufficient_context` và `citations`
- thêm regression cases cho nhánh “context có vẻ liên quan nhưng chưa đủ”

## Ngoài phạm vi v1

- thay đổi response schema công khai
- mở streaming
- prompt redesign toàn diện ngoài phần liên quan context sufficiency

## Quyết định cần khóa

- app dùng **deterministic rule** trước khi gọi LLM; v1 không dùng LLM-assisted check
- nếu `used_chunks` rỗng thì trả `insufficient_context` ngay như semantics hiện có
- nếu question có meaningful-token overlap quá thấp với context thì trả `insufficient_context`
- nếu question là loại hỏi chi tiết định lượng/thời gian (`bao lau`, `bao nhieu`, `khi nao`, `muc phi`, `gia bao nhieu`) nhưng context không có signal hỗ trợ tương ứng thì trả `insufficient_context`
- khi policy trả context không đủ, `used_chunks` vẫn được trả về như hiện tại để giữ traceability
- policy thống nhất toàn cục, không phụ thuộc provider cụ thể trong v1

## Success criteria

- có decision rõ policy `sufficient_context` được chọn
- policy được tách khỏi heuristic inline và mô tả được bằng rule kiểm chứng được
- có regression test cho các nhánh dễ sai nhất
- không làm lệch semantics `citations` và `insufficient_context` đã khóa trước đó

## Verification mong muốn

- regression suite cho generation context policy
- smoke test hiện có vẫn pass
- benchmark trước/sau trên golden cases nhạy với insufficient context


---

## Source: `docs/core/60-spec-provider-runtime-implementation-v1.md`

# 60. Spec Provider Runtime Implementation v1

## Migration Note

Tài liệu này mô tả implementation target trước khi hoàn tất migration package ngày `2026-04-23`.

Khi đọc tài liệu này ở trạng thái repo hiện tại, cần quy chiếu như sau:

- app shell hiện tại nằm ở `src/tuesday/api/`
- runtime/config hiện tại nằm ở `src/tuesday/runtime/`
- capability `rag` hiện tại nằm ở `src/tuesday/rag/`
- lệnh chạy API hiện tại là `python -m uvicorn tuesday.api.app:app --reload`
- env prefix hiện tại là `TUESDAY_`
- `src/tuesday_rag/` đã bị loại bỏ khỏi codebase; mọi nhắc đến path này bên dưới là historical reference

## Trạng thái

`accepted` — đã triển khai ngày `2026-04-23`. Runtime factory + `Container(config)` + app lifespan + backend selectors cho provider embedding/generation đã landed tại `src/tuesday/runtime/` và `src/tuesday/rag/infrastructure/`. Xem DL-031.

## Mục lục

- Mục tiêu
- Bối cảnh hiện tại
- Quyết định implementation cần khóa
- Thiết kế runtime mục tiêu
- Thiết kế config/env mục tiêu
- Thiết kế provider adapter v1
- Thiết kế API/lifespan v1
- Thiết kế script/runtime factory v1
- Kế hoạch rollout nhỏ
- Verification bắt buộc
- Ngoài phạm vi v1

## Mục tiêu

Biến `57-spec-provider-integration-and-runtime-lifecycle-v1.md` thành một implementation spec đủ cụ thể để có thể code trực tiếp mà không còn phải đoán về:

- env names
- cách chọn provider
- cách khởi tạo container
- cách HTTP app và internal scripts dùng chung runtime factory
- mức kiểm tra `pdftotext` trong nhịp đầu

## Bối cảnh hiện tại

Codebase hiện đang có các đặc điểm sau:

- `EmbeddingProvider` và `LLMProvider` protocol đã tồn tại ở `src/tuesday_rag/domain/ports.py`
- `Container` hiện tự đọc `RuntimeConfig.from_env()` trong `__init__`
- module `src/tuesday_rag/runtime/container.py` đang export singleton `container = Container()`
- `src/tuesday_rag/api/app.py` và nhiều script/test đang import trực tiếp singleton này
- provider hiện tại vẫn là adapter demo:
  - `HashEmbeddingProvider`
  - `DeterministicLLMProvider`

Điểm nghẽn implementation hiện tại:

- app wiring xảy ra tại import-time
- test override env và monkeypatch dễ phụ thuộc trạng thái module đã import trước đó
- internal scripts và benchmark cũng đang dính trực tiếp vào singleton

## Quyết định implementation cần khóa

### 1. Runtime không còn export singleton khởi tạo sẵn tại import-time

`src/tuesday_rag/runtime/container.py` không nên tiếp tục là nơi tạo `container = Container()` ngay khi import module.

Thay vào đó, runtime layer nên cung cấp:

- `build_container(config: RuntimeConfig | None = None) -> Container`
- `build_config_from_env() -> RuntimeConfig`
- nếu cần, thêm `build_runtime_from_env() -> Container` như một convenience function

Mục tiêu là:

- HTTP app tự tạo container trong lifespan
- internal scripts tự gọi runtime factory khi chạy
- test có thể tạo runtime riêng theo config/env của từng case

### 2. App nên chuyển từ module-level app singleton sang app factory rõ ràng

`src/tuesday_rag/api/app.py` nên có:

- `create_app() -> FastAPI`
- một `lifespan` function gắn container vào `app.state.container`

Có thể vẫn giữ `app = create_app()` ở cuối module để lệnh `uvicorn tuesday_rag.api.app:app` tiếp tục hoạt động, nhưng container bên trong app phải được tạo ở lifespan, không phải ở import-time.

### 3. Request handlers không dùng global `container`

Các route trong API nên lấy runtime từ:

- `request.app.state.container`

Điều này làm rõ lifetime của dependency và giúp test override app/runtime dễ hơn.

### 4. Internal scripts dùng chung một runtime factory, không import singleton

Các script sau nên dừng import `container` trực tiếp:

- `scripts/index_file.py`
- `scripts/index_directory.py`
- `scripts/benchmark_quality.py`
- `scripts/smoke_test.py` nếu có dependency tương tự trong implementation thực tế

Thay vào đó, mỗi script nên:

- gọi `build_runtime_from_env()`
- giữ runtime trong `main()`
- truyền runtime xuống các helper nếu cần

### 5. Provider demo vẫn được giữ cho test/local fallback trong v1

Nhịp này chưa nên xóa adapter demo.

Adapter demo vẫn cần tồn tại để:

- chạy test unit nhanh
- chạy benchmark/regression nội bộ không cần credential thật
- giữ local setup tối giản khi người dùng chưa cấu hình provider thật

Nhưng provider demo không còn là con đường runtime duy nhất.

## Thiết kế runtime mục tiêu

### RuntimeConfig

`RuntimeConfig` tiếp tục là nơi giữ cấu hình runtime đã validate.

V1 nên mở rộng thêm các field sau:

- `embedding_provider_backend`
- `generation_provider_backend`
- `openai_api_key`
- `openai_base_url` nếu cần
- `openai_embedding_model`
- `openai_generation_model`
- `gemini_api_key`
- `gemini_embedding_model`
- `gemini_generation_model`
- `azure_openai_api_key`
- `azure_openai_endpoint`
- `azure_openai_api_version`
- `azure_openai_embedding_deployment`
- `azure_openai_generation_deployment`
- `pdf_startup_check_mode`

Tên field có thể tinh chỉnh, nhưng logic nên tách rõ:

- backend selector
- credentials
- model/deployment names
- startup check policy

### Container

`Container` vẫn là composition root object, nhưng constructor nên nhận `config` từ bên ngoài:

```python
class Container:
    def __init__(self, config: RuntimeConfig) -> None:
        ...
```

Điều này giúp:

- test inject config trực tiếp
- app lifecycle kiểm soát thời điểm load env
- scripts dùng cùng một đường khởi tạo

## Thiết kế config/env mục tiêu

### Env selectors cần khóa

V1 nên dùng hai selector riêng:

- `TUESDAY_RAG_EMBEDDING_PROVIDER_BACKEND`
- `TUESDAY_RAG_GENERATION_PROVIDER_BACKEND`

Giá trị hợp lệ của mỗi selector:

- `demo`
- `openai`
- `gemini`
- `azure_openai`

Lý do tách đôi:

- embedding và generation có thể dùng backend khác nhau
- tránh phải tạo một matrix config khó mở rộng về sau

### Env keys đề xuất

#### OpenAI

- `TUESDAY_RAG_OPENAI_API_KEY`
- `TUESDAY_RAG_OPENAI_BASE_URL`
- `TUESDAY_RAG_OPENAI_EMBEDDING_MODEL`
- `TUESDAY_RAG_OPENAI_GENERATION_MODEL`

#### Gemini

- `TUESDAY_RAG_GEMINI_API_KEY`
- `TUESDAY_RAG_GEMINI_EMBEDDING_MODEL`
- `TUESDAY_RAG_GEMINI_GENERATION_MODEL`

#### Azure OpenAI

- `TUESDAY_RAG_AZURE_OPENAI_API_KEY`
- `TUESDAY_RAG_AZURE_OPENAI_ENDPOINT`
- `TUESDAY_RAG_AZURE_OPENAI_API_VERSION`
- `TUESDAY_RAG_AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `TUESDAY_RAG_AZURE_OPENAI_GENERATION_DEPLOYMENT`

#### PDF startup check

- `TUESDAY_RAG_PDF_STARTUP_CHECK_MODE`

Giá trị hợp lệ:

- `off`
- `warn`
- `strict`

Mặc định của v1 nên là `off`.

### Validation rules v1

- nếu backend là `demo`, không yêu cầu credential
- nếu backend là `openai`, phải có API key và model tương ứng với capability được chọn
- nếu backend là `gemini`, phải có API key và model tương ứng
- nếu backend là `azure_openai`, phải có endpoint, API key, API version và deployment tương ứng
- `pdf_startup_check_mode` phải nằm trong `off|warn|strict`

Validation failure nên xảy ra khi build runtime/config, không trì hoãn đến request đầu tiên.

## Thiết kế provider adapter v1

### Scope adapter

V1 chỉ cần map vào 2 protocol hiện có:

- `EmbeddingProvider`
- `LLMProvider`

Không cần đưa SDK-specific object vượt qua `infrastructure/`.

### Module layout đề xuất

V1 có thể thêm:

- `src/tuesday_rag/infrastructure/providers_openai.py`
- `src/tuesday_rag/infrastructure/providers_gemini.py`
- `src/tuesday_rag/infrastructure/providers_azure_openai.py`

Hoặc gom vào ít file hơn nếu code ngắn. Điều quan trọng là:

- boundary provider-specific nằm trong `infrastructure/`
- `runtime/container.py` chỉ chọn adapter, không chứa logic HTTP client chi tiết

### Semantics v1

- `embed_texts` và `embed_query` phải trả về `list[list[float]]` và `list[float]` đúng với protocol hiện có
- `generate_text` phải map output về `LLMGenerationResult`
- parsing citations ở v1 có thể vẫn dùng format prompt/output hiện có nếu chưa thay generation policy

## Thiết kế API/lifespan v1

### App state

Trong lifespan:

- build config từ env
- build container từ config
- gắn vào `app.state.container`

Khi shutdown:

- không bắt buộc close resource trong v1 nếu adapter chưa cần cleanup
- nhưng nên giữ chỗ cho cleanup hook khi vector DB/client thật xuất hiện

### Health endpoint

`GET /health` vẫn giữ contract hiện tại.

V1 không cần thêm readiness detail vào response nếu chưa có decision mới.

### Startup check cho `pdftotext`

Nếu `pdf_startup_check_mode = warn`:

- app startup vẫn thành công
- log warning nếu không tìm thấy `pdftotext`

Nếu `pdf_startup_check_mode = strict`:

- build app/runtime phải fail fast nếu thiếu `pdftotext`

Nếu `off`:

- không kiểm tra khi startup
- PDF parsing chỉ fail tại thời điểm ingestion như hiện tại

## Thiết kế script/runtime factory v1

### Shared factory

Runtime layer nên có một entrypoint rõ dùng chung cho app và script, ví dụ:

```python
def build_runtime_from_env() -> Container:
    return build_container(build_config_from_env())
```

### Script changes v1

Các script hiện có nên chuyển sang pattern:

```python
def main() -> int:
    container = build_runtime_from_env()
    ...
```

Không nên giữ module-level singleton trong script vì điều đó làm env override trong test trở nên khó kiểm soát.

### Test changes v1

`tests/conftest.py` và các test đang import singleton `container` sẽ cần đổi sang một trong hai hướng:

- dùng app/runtime fixture tạo mới theo từng test
- hoặc monkeypatch runtime factory nếu test thật sự cần global path

Hướng ưu tiên là fixture-based.

## Kế hoạch rollout nhỏ

Để tránh scope nở quá nhanh, nhịp này nên làm theo thứ tự:

1. refactor runtime factory + `Container(config)` + app lifespan
2. cập nhật API tests, script tests và fixtures theo runtime mới
3. thêm config/env selector cho provider backends
4. giữ `demo` backend làm mặc định để không phá local flow hiện tại
5. thêm adapter thật đầu tiên với ít nhất một backend chạy được end-to-end
6. sau đó mới mở rộng thêm các backend còn lại

Khuyến nghị thực dụng:

- ở nhịp code đầu tiên, có thể implement runtime/lifespan + selector framework trước
- adapter thật có thể vào theo thứ tự `OpenAI` trước, rồi `Gemini`, rồi `Azure OpenAI`

Spec này vẫn giữ chỗ cho cả ba backend, nhưng implementation có thể đi theo rollout đó nếu cần giữ scope gọn.

## Verification bắt buộc

- unit test cho `RuntimeConfig` với backend selectors và required env
- unit test cho runtime factory chọn đúng provider adapter
- API test chứng minh app không còn phụ thuộc import-time singleton
- script test chứng minh mỗi script tự build runtime trong `main()`
- regression/smoke test hiện có vẫn pass với `demo` backend mặc định
- kiểm tra manual cho `pdf_startup_check_mode=warn|strict`

## Ngoài phạm vi v1

- streaming generation
- readiness endpoint mới
- pooling/async client tối ưu cho provider SDK
- vector store thật
- generation context policy mới
- thay đổi response contract công khai


---

## Source: `docs/core/README.md`

# Core Track

Track này chứa các spec sau khi chương `post-mvp` đã đóng.

Mục tiêu của `core` là tập trung vào phần lõi của hệ thống RAG:

- retrieval quality
- generation quality và grounding
- context selection và ranking
- storage/retrieval backend phục vụ cải thiện lõi

Tài liệu hiện có:

- `55-core-track-overview.md`
- `56-spec-retrieval-core-hardening-v1.md` — `accepted` (`2026-04-23`)
- `57-spec-provider-integration-and-runtime-lifecycle-v1.md` — `accepted` (`2026-04-23`)
- `58-spec-real-vector-store-adapter-v1.md` — `accepted` (`2026-04-23`)
- `59-spec-generation-context-policy-v1.md` — `accepted` (`2026-04-23`)
- `60-spec-provider-runtime-implementation-v1.md` — `accepted` (`2026-04-23`)

Thứ tự ưu tiên hiện tại của track này là:

1. ~~provider thật và env-based selection trong container~~ — đã xong
2. ~~vector store thật `Qdrant` thay cho adapter demo hiện tại, với selective LlamaIndex adoption trong `infrastructure/`~~ — đã xong
3. ~~chuyển container wiring vào app lifespan~~ — đã xong
4. ~~đặc tả lại logic `sufficient_context`~~ — đã xong
5. ~~khóa rõ phụ thuộc `pdftotext` và startup check tùy chọn~~ — đã xong

`56-spec-retrieval-core-hardening-v1.md`, `58-spec-real-vector-store-adapter-v1.md`, và `59-spec-generation-context-policy-v1.md` đều đã hoàn tất trong track `core` hiện tại.


---

## Source: `docs/history/10-ke-hoach-trien-khai-theo-sprint.md`

# 10. Kế Hoạch Triển Khai Theo Sprint

## Mục lục

- Thứ tự triển khai
- Sprint 1
- Sprint 2
- Sprint 3
- Trạng thái chốt MVP
- Deliverable
- Rủi ro kỹ thuật
- Cách giảm rủi ro

## Thứ tự triển khai

Thứ tự đề xuất:

1. Chốt spec và model nội bộ.
2. Dựng skeleton ports/adapters và dependency wiring.
3. Hoàn thành ingestion trước.
4. Hoàn thành retrieval sau khi dữ liệu index được.
5. Hoàn thành generation sau khi retrieval ổn định.
6. Khóa API contract và bổ sung integration test tối thiểu.

## Sprint 1

Mục tiêu:

- Chốt domain và ingestion foundation.

Phạm vi:

- Khởi tạo cấu trúc thư mục theo ports/adapters.
- Tạo domain model và validator.
- Tạo port interface.
- Triển khai use case ingestion mức cơ bản.
- Tạo fake adapter để chạy test use case.
- Tạo API `POST /documents/index`.
- Giữ public API ingestion ở mode JSON text trước; parser file chỉ giữ ở dạng adapter mở rộng hoặc ingestion path nội bộ.
- Khóa `chunk_size/chunk_overlap` theo ký tự và wiring config runtime cơ bản.

Deliverable:

- Domain model compile được.
- Test ingestion xanh.
- Endpoint index hoạt động với adapter giả hoặc adapter thật tối thiểu.
- Parser file và partial indexing không phải deliverable bắt buộc của public MVP sprint này.

## Sprint 2

Mục tiêu:

- Hoàn thành retrieval foundation.

Phạm vi:

- Triển khai `EmbeddingProvider` adapter.
- Triển khai `VectorStore` adapter.
- Triển khai `Retriever`.
- Tạo API `POST /retrieve`.
- Bổ sung filter whitelist và `top_k` behavior.
- Khóa semantics `tags = contains-any`.

Deliverable:

- Retrieval use case chạy được end-to-end.
- API retrieve có contract test và ít nhất 1 integration test adapter.

## Sprint 3

Mục tiêu:

- Hoàn thành generation và khóa MVP.

Phạm vi:

- Triển khai `LLMProvider` adapter.
- Triển khai `Generator`.
- Tạo prompt builder theo spec grounding.
- Tạo API `POST /generate`.
- Bổ sung test cho citation, insufficient context, error mapping.
- Chốt policy: khi không có context thì application trả kết quả `insufficient_context` có kiểm soát, không bắt buộc gọi LLM.
- Khóa bảng HTTP error mapping MVP.
- Khóa literal mặc định cho response `insufficient_context` và log tối thiểu cho request lifecycle.

Deliverable:

- Luồng index -> retrieve -> generate chạy được.
- Bộ test cốt lõi xanh.
- Tài liệu spec được rà chéo và khóa cho MVP.

## Trạng thái chốt MVP

Trạng thái hiện tại: **public MVP đã được đóng scope**.

Public MVP được coi là hoàn tất khi thỏa các điều kiện sau:

- Có 3 endpoint công khai:
  - `POST /documents/index`
  - `POST /retrieve`
  - `POST /generate`
- Ingestion public chỉ khóa mode JSON text chuẩn hóa.
- Retrieval giữ đúng `top_k`, whitelist filter và semantics `tags = contains-any`.
- Generation giữ đúng nhánh `insufficient_context`, grounding theo context, citation theo `chunk_id`.
- Có test cho contract HTTP, use case cốt lõi, adapter integration tối thiểu và observability cơ bản.

Những phần không còn được coi là blocker của public MVP:

- parser file hoặc ingestion path nội bộ
- `DOCUMENT_PARSE_ERROR` ở HTTP public flow
- `PARTIAL_INDEXED`
- provider hoặc vector store thật thay cho adapter fake/in-memory

## Deliverable mỗi sprint

| Sprint   | Deliverable chính                                   |
| -------- | --------------------------------------------------- |
| Sprint 1 | Domain + ingestion + API index                      |
| Sprint 2 | Retrieval + API retrieve + integration vector store |
| Sprint 3 | Generation + API generate + end-to-end MVP          |

## Rủi ro kỹ thuật

| Rủi ro                                       | Tác động                                        |
| -------------------------------------------- | ----------------------------------------------- |
| Parse đầu vào không ổn định                  | Ingestion thất bại hoặc metadata kém chất lượng |
| Chunking không phù hợp                       | Retrieval kém chính xác                         |
| Embedding model không phù hợp ngôn ngữ       | Chất lượng retrieval thấp                       |
| Vector store filter hỗ trợ hạn chế           | Hành vi filter không nhất quán                  |
| LLM trả citation không ổn định               | Output khó kiểm soát                            |
| LlamaIndex abstraction rò rỉ lên application | Khó thay engine sau này                         |

## Cách giảm rủi ro

- Bắt đầu với input text chuẩn hóa trước, mở rộng parser sau.
- Khóa metadata schema từ đầu.
- Dùng prompt builder deterministic và hậu xử lý citation.
- Viết contract test cho adapter.
- Giữ LlamaIndex trong helper/adapters hạ tầng phía sau application services, không đưa object của nó ra ngoài.
- Chọn 1 bộ dữ liệu mẫu tiếng Việt để đánh giá retrieval sớm ngay từ Sprint 2.
- Giữ chunking strategy đơn giản theo ký tự ở MVP để tránh coupling vào tokenizer/model.


---

## Source: `docs/history/12-review-tong-hop.md`

# 12. Review Tổng Hợp Bộ Tài Liệu

## Tóm tắt chất lượng bộ tài liệu hiện tại

Bộ tài liệu hiện tại có nền tảng tốt cho một MVP RAG core theo hướng ports/adapters, Spec-Driven Development và TDD. Các phần chính đã bao phủ được `ingestion`, `retrieval`, `generation`, API contract và test strategy.

Sau khi rà chéo và chốt các quyết định kiến trúc mở, bộ tài liệu đã nhất quán hơn giữa domain, use case và API contract. Trạng thái hiện tại là:

- Có thể bắt đầu code MVP theo TDD.
- Cần giữ phạm vi sprint đầu đúng spec đã khóa, không nới sang production-grade features.

## Điểm mạnh

- Phân tách lớp rõ giữa API, application, domain và infrastructure.
- Đã giữ được nguyên tắc không làm rò rỉ object của LlamaIndex, vector store hay cloud provider vào domain.
- Domain model bao phủ được các thực thể cốt lõi cho MVP.
- Use case có cấu trúc khá tốt: input, output, validation, error cases, acceptance criteria, test cases.
- API contract đã đủ rõ để bắt đầu viết contract test cho 3 endpoint chính.
- Citation semantics đã được khóa theo `chunk_id` và không cho phép viện dẫn ngoài tập chunk thực tế đã dùng.
- Contract cho nhánh `insufficient_context` đã rõ hơn cả ở behavior lẫn schema phản hồi.
- Test strategy bám đúng tinh thần TDD, ưu tiên use case test và contract test trước integration test.
- Sprint plan hợp lý theo thứ tự `ingestion -> retrieval -> generation`.

## Điểm chưa ổn

- Một số chỗ còn trộn giữa “khả năng hệ thống có thể hỗ trợ” và “public API MVP thực sự khóa gì”.
- Tên contract ở generation trước đó chưa thống nhất giữa domain và API.
- Bộ port/service nội bộ vẫn cần được implement cẩn thận để không trôi boundary khi vào code.
- Các giới hạn input đã được khóa, nhưng vẫn cần map rõ vào config runtime khi triển khai.

## Các mâu thuẫn phát hiện được

- `GenerationRequest` trong domain dùng `retrieval_request`, trong khi API contract trước đó dùng `retrieval`.
  - Đã chỉnh đồng bộ về `retrieval_request`.
- Ingestion use case trước đó nói `content` “có nếu không có file”, nhưng API contract lại chỉ có mode JSON text.
  - Đã chỉnh rõ public API MVP chỉ khóa mode text chuẩn hóa; parser file là hướng nội bộ hoặc phase sau.
- Generation flow trước đó mô tả luôn gọi generator/LLM, trong khi acceptance criteria lại yêu cầu xử lý hợp lệ khi `retrieved_chunks = []`.
  - Đã chỉnh rõ application có thể trả trực tiếp `insufficient_context` mà không cần gọi LLM.
- API `/generate` cho phép bỏ trống `retrieval.query`, trong khi domain `RetrievalRequest.query` là bắt buộc.
  - Đã bổ sung quy tắc mapping: nếu thiếu thì lấy từ `question`.

## Các điểm thiếu

- Thiếu quy tắc validation cụ thể cho một số field:
  - format `document_id`
  - format `index_name`
  - regex ký tự hợp lệ nếu team muốn khóa thêm
- Thiếu quy tắc tách biệt dữ liệu nhạy cảm trong metadata ngoài cảnh báo mức nguyên tắc.
- Thiếu bộ dữ liệu mẫu được khóa thật sự trong repo để dùng chung cho spec review và TDD.

## Các điểm over-engineer

- Bộ port hiện tại có xu hướng dày hơn mức MVP:
  - cần tránh nâng `Indexer`, `Retriever`, `Generator` thành abstraction hạ tầng quá sớm khi chúng đã được chốt là service nội bộ gần capability.
- Parser file đã được nhắc ở nhiều nơi dù public API MVP hiện chỉ khóa JSON text.
- Tài liệu có nói tới nhiều hướng mở rộng hợp lý nhưng cần tránh để đội triển khai “thi công trước cho tương lai”, nhất là:
  - hybrid retrieval
  - reranker
  - queue/batch async
  - evaluation harness đầy đủ

Quyết định đã khóa:

- Giữ các port hạ tầng thật sự cần cho sprint đầu:
  - `EmbeddingProvider`
  - `LLMProvider`
  - `VectorStore`
  - `Chunker`
  - `DocumentParser` nếu có ingestion path nội bộ
- Giữ `Indexer`, `Retriever`, `Generator` như service nội bộ gần capability.
- Re-index policy là `replace-by-document_id-within-index_name`.
- `tags` dùng semantics `contains-any`.
- `version` chỉ để metadata, chưa ảnh hưởng retrieval logic.
- Khi không có context, trả `insufficient_context` trực tiếp và không gọi LLM.
- Chunking của MVP dùng cấu hình theo ký tự: `chunk_size = 1000`, `chunk_overlap = 150`, có min/max và override bằng config runtime.
- Config runtime được nạp khi khởi động ứng dụng và chỉ override trong biên spec.
- Response `insufficient_context` có literal mặc định và không đổi schema.
- Observability tối thiểu của MVP gồm `request_id`, `use_case`, `error_code`, `latency_ms`, không log raw content ngoài mức cần thiết.

## Review theo từng nhóm tiêu chí

### A. Tính nhất quán

- Tên domain model hiện tương đối thống nhất sau khi đã đồng bộ `retrieval_request`.
- Tên thành phần hiện nhất quán hơn sau khi chốt `Indexer`/`Retriever`/`Generator` là service nội bộ gần capability.
- API request/response nhìn chung khớp với use case, trừ một số chỗ đã chỉnh như trên.
- Acceptance criteria và test strategy nhìn chung khớp nhau; phần generation đã tốt hơn sau khi khóa nhánh `insufficient_context`.
- Glossary khớp ở mức thuật ngữ chung, chưa có vấn đề lớn.
- Kiến trúc tổng thể khớp với sprint plan và use case, nhưng ingestion path cho file nên được coi là mở rộng thay vì contract công khai của sprint đầu.

### B. Tính đầy đủ

- 3 use case cốt lõi cho MVP đã có.
- Error cases cơ bản đã đủ để bắt đầu code.
- Validation rules đã đủ để bắt đầu code MVP; phần còn lại chủ yếu là regex/format chi tiết nếu team muốn siết thêm.
- Metadata schema chunk ở mức đủ dùng cho MVP: trace, filter, citation.
- Citation semantics và insufficient-context contract đã đủ rõ để viết test hành vi trước.
- Boundary orchestration và infrastructure đã có; điểm cần giữ là không làm service nội bộ trôi sang vai trò adapter.
- Grounding/citations/insufficient context đã có, và đã rõ hơn sau khi chỉnh nhánh context rỗng.

### C. Mức độ phù hợp với MVP

- Tổng thể phù hợp MVP.
- Phần dễ trượt sang over-engineer là parser file, composite ports, và các hướng mở rộng retrieval.
- Sprint 1 nên bám đúng mode text chuẩn hóa, fake adapters, contract test và use case test.
- Chưa cần tối ưu async ingestion, reranker, hybrid retrieval hay streaming.

### D. Hỗ trợ TDD

- Use case đủ cụ thể để viết test trước ở mức orchestration/capability.
- API contract đủ rõ để viết API test cơ bản.
- Port/interface đủ rõ để fake hoặc mock.
- Acceptance criteria phần lớn đo được.
- Các default/min/max đã được khóa cho `top_k`, `max_context_chunks`, `content`, `query`, `question`, `chunk_size`, `chunk_overlap`.
- Test strategy thực thi được, đặc biệt sau khi chốt nhánh `insufficient_context` không buộc phải gọi LLM.

### E. Coupling với LlamaIndex / provider

- Không thấy business logic bị khóa trực tiếp vào object của LlamaIndex trong domain.
- Domain model chưa bị leak framework type.
- Contract công khai chưa bị phụ thuộc vào provider cloud cụ thể.
- Điểm cần canh là không để adapter LlamaIndex quyết định prompt format, retrieval response format hay citation format ở phía orchestration.

## Các điểm cần làm rõ trước khi code

1. Regex hoặc format hợp lệ cho `document_id` và `index_name` có cần khóa thêm ngay hay không.
2. Adapter vector store thật có hỗ trợ `replace-by-document_id-within-index_name` hiệu quả hay cần chiến lược kỹ thuật riêng.
3. Bộ fixture dữ liệu mẫu nào sẽ là chuẩn chung cho review và TDD.
4. Regex hoặc format hợp lệ cho `document_id` và `index_name` có cần siết thêm ở mức implementation hay không.

## Đề xuất thứ tự review thủ công của con người

1. Review `03-domain-model.md` và `08-api-contract.md` cùng nhau để khóa model công khai và model nội bộ.
2. Review `05/06/07-use-case-*.md` để xác nhận behavior thật sự mong muốn trước khi viết test.
3. Review `04-ports-va-adapters.md` để cắt bớt phần thừa nếu cần, tránh over-engineer.
4. Review `09-test-strategy.md` để khóa bộ test đầu tiên theo sprint.
5. Review `10-ke-hoach-trien-khai-theo-sprint.md` để bảo đảm phạm vi sprint đầu không trượt.

## Kết luận: bộ tài liệu đã sẵn sàng để code hay chưa

Kết luận hiện tại: **đã sẵn sàng để code MVP**.

Đánh giá thực dụng:

- Có thể bắt đầu dựng skeleton dự án, domain model, validator, use case test, API contract test và adapter MVP.
- Các điểm còn lại là tinh chỉnh triển khai, không còn là blocker ở mức spec.

Với các quyết định vừa được khóa, bộ tài liệu này đủ tốt để bắt đầu code theo TDD mà không cần viết lại toàn bộ spec.

## Trạng thái sau triển khai MVP

Trạng thái mới: **public MVP đã được triển khai và có thể đóng scope**.

Phạm vi được coi là đã hoàn tất:

- ingestion qua JSON text
- retrieval qua logical index với filter MVP
- generation grounded với citation theo `chunk_id`
- config runtime trong biên spec
- logging tối thiểu cho request lifecycle
- bộ test cốt lõi cho public contract và behavior chính

Các hạng mục vẫn để phase sau nhưng không còn là blocker của việc đóng MVP:

- parser file cho ingestion path nội bộ
- `PARTIAL_INDEXED`
- adapter thật cho cloud/vector store
- siết thêm regex cho `document_id` và `index_name` nếu team muốn


---

## Source: `docs/history/13-checklist-truoc-khi-code.md`

# 13. Checklist Trước Khi Code

## Checklist kiến trúc

- [x] Đã chốt rõ boundary lõi ban đầu: API, orchestration/application, domain, infrastructure.
- [x] Đã xác nhận domain/application không phụ thuộc trực tiếp vào object của LlamaIndex.
- [x] Đã xác nhận mọi SDK cloud/vector store chỉ xuất hiện trong adapter.
- [x] Đã chốt public API MVP chỉ hỗ trợ mode nào và mode nào để sau.
- [x] `Indexer`, `Retriever`, `Generator` là service nội bộ gần capability, chưa phải port lõi.

## Checklist domain model

- [x] `SourceDocument`, `Chunk`, `IndexedChunk`, `RetrievedChunk` đã được hiểu thống nhất.
- [x] `RetrievalRequest` và `GenerationRequest` đã khớp với mapping từ API.
- [x] Invariant và semantics cho `top_k`, `citations`, `insufficient_context`, `grounded` đã được khóa.
- [x] Metadata schema của chunk đã đủ cho trace, filter, citation.
- [x] Đã chốt policy re-index: `replace-by-document_id-within-index_name`.

## Checklist config/runtime defaults

- [x] Đã chốt default/min/max cho `top_k` và `max_context_chunks`.
- [x] Đã chốt default/min/max cho `chunk_size` và `chunk_overlap`.
- [x] Đã chốt giới hạn input cho `content`, `query`, `question`.
- [x] Đã chốt cách override các giới hạn trên bằng config runtime mà không làm lệch spec.

## Checklist API contract

- [x] `/documents/index` đã khóa rõ request/response JSON cho MVP.
- [x] `/retrieve` đã khóa whitelist filter.
- [x] `/generate` đã thống nhất dùng `retrieval_request`.
- [x] Đã chốt rule mapping từ `question` sang `retrieval_request.query` khi thiếu.
- [x] Đã chốt HTTP status cho từng `error_code`.
- [x] Đã chốt rule khi `retrieved_chunks = []`.

## Checklist re-index semantics

- [x] Đã chốt re-index policy là `replace-by-document_id-within-index_name`.
- [x] Đã xác nhận implementation của `/documents/index` bám đúng policy replace đã chốt.
- [x] Đã chốt behavior idempotency của `/documents/index` cho cùng input lặp lại.

## Checklist citation semantics

- [x] Đã chốt citation chuẩn tham chiếu theo `chunk_id`, không theo `document_id`.
- [x] Đã chốt rule: citation chỉ được lấy từ `retrieved_chunks` thực tế đã dùng.
- [x] Đã chốt hành vi khi không có chunk nào được dùng thì `citations` phải rỗng.

## Checklist insufficient_context contract

- [x] Đã chốt response schema khi `insufficient_context`.
- [x] Đã chốt trạng thái này được biểu diễn bằng `insufficient_context = true` và `grounded = false`.
- [x] Đã chốt nhánh `insufficient_context` không gọi `LLMProvider`.

## Checklist use case

- [x] Ingestion public MVP đã có luồng thành công, lỗi chunking, lỗi embedding, lỗi index.
- [ ] Parser nội bộ và nhánh `DOCUMENT_PARSE_ERROR` chỉ cần khi kích hoạt ingestion path ngoài JSON text.
- [x] Retrieval đã có luồng thành công, không có kết quả, filter sai, lỗi vector store.
- [x] Generation đã có luồng dùng context sẵn, tự retrieval, và nhánh `insufficient_context`.
- [x] Acceptance criteria của từng use case đo được bằng test.
- [x] Không có use case nào phụ thuộc vào framework type.

## Checklist TDD/testability

- [x] Đã có danh sách test đầu tiên cho domain invariant.
- [x] Đã có danh sách use case test cho `ingestion`, `retrieval`, `generation`.
- [x] Đã xác định rõ fake/mock cho `EmbeddingProvider`, `LLMProvider`, `VectorStore`.
- [x] Đã xác định phần nào không mock: validator, mapper, prompt builder.
- [x] Đã có test cho nhánh generation không gọi `LLMProvider` khi thiếu context.
- [x] Đã có tối thiểu 1 API contract test cho mỗi endpoint.

## Checklist adapter boundaries

- [x] Adapter chỉ map vào/ra model nội bộ.
- [x] Không trả object LlamaIndex ra orchestration/capability layer.
- [x] Không trả object SDK của provider ra domain/application.
- [x] Semantics filter `tags` đã chốt là `contains-any`.
- [x] Filter metadata được adapter hỗ trợ đúng semantics đã chốt.
- [x] Adapter có contract test tối thiểu.

## Checklist filter semantics

- [x] Đã chốt semantics cho từng filter được hỗ trợ trong MVP.
- [x] `tags` dùng semantics `contains-any`.
- [x] Đã chốt hành vi khi filter hợp lệ nhưng không match dữ liệu nào: trả `chunks = []`, không coi là lỗi hệ thống.

## Checklist MVP scope

- [x] Không thêm reranker vào sprint đầu.
- [x] Không thêm hybrid retrieval vào sprint đầu.
- [x] Không thêm async ingestion vào sprint đầu nếu chưa cần.
- [x] Không thêm streaming response vào sprint đầu.
- [x] Không thêm multi-tenant/RBAC vào sprint đầu.
- [x] Không biến parser file thành blocker của public API MVP nếu chưa cần.

## Checklist dữ liệu mẫu/test data

- [x] Có ít nhất 1 tài liệu tiếng Việt ngắn cho ingestion thành công.
- [x] Có ít nhất 1 tài liệu đủ dài để tạo nhiều chunk.
- [x] Có case tài liệu rỗng.
- [x] Có case query không match gì.
- [x] Có case context đủ để sinh answer có citation.
- [x] Có case context không đủ để trả `insufficient_context`.
- [x] Dữ liệu mẫu không chứa thông tin nhạy cảm thật.
- [x] Dữ liệu mẫu đủ ổn định để test deterministic.

## Checklist observability tối thiểu

- [x] Đã chốt log tối thiểu cho mỗi request: `request_id`, `use_case`, `error_code`, `latency` cơ bản.
- [x] Đã chốt không log dữ liệu nhạy cảm hoặc raw content ngoài mức cần thiết để debug.

## Kết luận đóng scope

- [x] Public MVP hiện tại có thể đóng scope.
- [x] Các mục deferred đã được ghi rõ là ngoài public MVP.


---

## Source: `docs/history/54-closeout-post-mvp.md`

# 54. Closeout Giai Đoạn Post-MVP

## Mục lục

- Mục tiêu
- Trạng thái đóng
- Tóm tắt những gì đã hoàn tất
- Những gì không còn thuộc `post-mvp`
- Nguyên tắc chuyển sang giai đoạn mới
- Tài liệu tham chiếu chính

## Mục tiêu

Tài liệu này chốt lại rằng chương `post-mvp` đã hoàn thành đủ phạm vi đã định, để team có thể chuyển sang bộ spec mới mà không tiếp tục nhồi thêm công việc mới vào cùng một roadmap cũ.

## Trạng thái đóng

Trạng thái hiện tại của `post-mvp`: **đã hoàn tất và có thể đóng như một chương roadmap**.

Điều này có nghĩa là:

- các phase đã định ban đầu đã đi đến trạng thái done đủ dùng
- các checklist chính đã được khóa
- các deliverable nền tảng đã có implementation thật thay vì chỉ còn trên giấy
- các nhịp tiếp theo không cần tiếp tục được mô tả như phần nối dài của `post-mvp`

`post-mvp` vẫn được giữ lại trong repo như hồ sơ lịch sử quyết định, implementation path và verification baseline.

## Tóm tắt những gì đã hoàn tất

### Phase 1: `stabilize`

- đã chuẩn hóa setup dev, lệnh lint, lệnh test và cách chạy API local
- đã có baseline CI hoặc automation tương đương
- đã có runbook cấu hình và release baseline

### Phase 2: `operational_hardening`

- đã thay trạng thái index chỉ-in-memory bằng lựa chọn bền hơn
- đã thêm timeout, retry và error mapping cho các tích hợp chính
- đã có smoke test cho luồng `index -> retrieve -> generate`
- đã tăng observability cho failure path

### Phase 3: `quality_evaluation`

- đã khóa golden cases và benchmark nhỏ
- đã có baseline cho retrieval quality, grounding, citation correctness và latency
- đã có regression suite cho các case quan trọng

### Phase 4: `feature_expansion` nhịp đầu

- đã hoàn tất migration capability-oriented đủ dùng cho nhịp feature đầu tiên
- đã ship `internal file ingestion` nội bộ
- đã hỗ trợ `.txt`, `.md`, `.html`, `.pdf`
- đã có batch CLI với `--recursive`, `--output`, `--include`, `--exclude`, `--dry-run`
- đã khóa verification bằng unit test, integration test, smoke test và regression suite

## Những gì không còn thuộc `post-mvp`

Kể từ mốc này, các hạng mục sau không nên tiếp tục được viết như một phần mở rộng của `docs/post-mvp/`:

- nâng chất lượng lõi của retrieval
- nâng chất lượng lõi của generation và grounding
- thay vector store hoặc retrieval backend để tăng hiệu năng thật
- capability mới không còn mang tính “mở rộng đầu tiên sau MVP”
- roadmap dài hạn sau khi các phase nền đã hoàn tất

Các công việc trên nên đi vào một track tài liệu mới, với mục tiêu, scope và decision riêng.

## Nguyên tắc chuyển sang giai đoạn mới

- Không xóa hoặc làm mờ giá trị của `docs/post-mvp/`; đây là baseline lịch sử đã hoàn tất.
- Chỉ sửa `docs/post-mvp/` khi cần đính chính sai sót hoặc làm rõ lịch sử implementation.
- Mọi spec mới từ đây nên nằm ở track tài liệu mới, thay vì tiếp tục tăng số phase trong `post-mvp`.
- Track mới nên tập trung vào phần lõi của hệ thống RAG, không quay lại pattern “hardening nền + mở rộng tiện ích nhỏ”.

## Tài liệu tham chiếu chính

- `docs/post-mvp/20-ke-hoach-trien-khai-sau-mvp.md`
- `docs/post-mvp/21-checklist-giai-doan-sau-mvp.md`
- `docs/post-mvp/phase-4/53-phase-4-implementation-summary.md`
- `docs/14-decision-log.md`


---

## Source: `docs/history/README.md`

# History Archive

Thư mục này lưu **hồ sơ quá trình triển khai** — spec, checklist, runbook, implementation summary và journey docs đã hoàn tất nhiệm vụ của chúng. Không phải nguồn sự thật cho hành vi hiện tại của hệ thống.

## Khi nào đọc các file ở đây

- Khi cần biết **vì sao** một quyết định đã được chốt trong quá khứ (bổ sung cho `docs/14-decision-log.md`).
- Khi cần tham chiếu implementation path của một phase đã đóng để so sánh hoặc tái sử dụng.
- Khi cần verification baseline của một deliverable đã ship (checklist, runbook, test coverage lịch sử).

## Khi nào **không** đọc các file ở đây

- Khi muốn biết hệ thống hiện tại hoạt động ra sao — dùng `docs/00-core-brief.md` và `docs/01..09, 11, 15, 16`.
- Khi đang triển khai task hiện tại — nguồn rule hiện hành ở `docs/` root và `docs/core/`.
- Để lấy path/command/env var hiện tại — README và `docs/00-core-brief.md` là canonical.

## Nguyên tắc chỉnh sửa

- Chỉ sửa khi cần đính chính sai sót hoặc làm rõ lịch sử.
- Không dùng nơi này để mở rộng spec mới — spec mới đi vào `docs/core/` hoặc `docs/` root.
- Không đổi path của các file ở đây tuỳ tiện; nhiều decision log entry và commit reference vào đúng tên file.

## Nội dung

### Journey MVP core

- `10-ke-hoach-trien-khai-theo-sprint.md` — kế hoạch sprint 1/2/3 cho MVP
- `12-review-tong-hop.md` — review chéo bộ tài liệu trước khi code
- `13-checklist-truoc-khi-code.md` — checklist tiền triển khai MVP

### Journey post-MVP

- `54-closeout-post-mvp.md` — chốt đóng chương post-MVP
- `post-mvp/17..21` — overview, spec, checklist post-MVP
- `post-mvp/40, 41` — migration structure spec (đã hoàn tất)
- `post-mvp/phase-1/` — stabilize
- `post-mvp/phase-2/` — operational hardening
- `post-mvp/phase-3/` — quality evaluation
- `post-mvp/phase-4/` — feature expansion (internal file ingestion)

## Trỏ về track hiện hành

- Entry point cho session hiện tại: [`../00-core-brief.md`](../00-core-brief.md)
- Decision log (sống chung với spec hiện hành): [`../14-decision-log.md`](../14-decision-log.md)
- Track đang mở: [`../core/`](../core/)


---

## Source: `docs/history/post-mvp/17-tong-quan-giai-doan-sau-mvp.md`

# 17. Tổng Quan Giai Đoạn Sau MVP

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi mặc định
- Giả định kỹ thuật
- Thứ tự ưu tiên
- Nguyên tắc triển khai
- Trạng thái hiện tại

## Mục tiêu

Sau khi public MVP đã đóng scope, mục tiêu của giai đoạn tiếp theo là:

- Ổn định hóa bản hiện tại để team có thể chạy, test, release và demo lặp lại được.
- Tăng mức sẵn sàng vận hành của hệ thống trước khi mở rộng tính năng.
- Thiết lập baseline chất lượng cho retrieval, grounding, citation và độ trễ.
- Chỉ mở rộng feature khi đã có dữ liệu vận hành và benchmark tối thiểu.

## Phạm vi

Giai đoạn sau MVP được chia thành 4 phase:

1. `stabilize`
2. `operational_hardening`
3. `quality_evaluation`
4. `feature_expansion`

Phạm vi của bộ spec này:

- khóa thứ tự ưu tiên giữa các phase
- xác định deliverable, acceptance criteria và verification cho từng phase
- giữ boundary kiến trúc hiện tại trong lúc thay adapter, thêm observability hoặc thêm benchmark
- ngăn việc mở rộng feature quá sớm khi nền vận hành và đánh giá chưa ổn

## Ngoài phạm vi mặc định

Những phần sau không mặc định là blocker ngay sau MVP:

- endpoint HTTP công khai mới
- streaming response cho `/generate`
- async ingestion hoặc queue orchestration
- hybrid retrieval
- reranker
- giao diện chat hoàn chỉnh
- multi-tenant, RBAC, workflow quản trị

Các hạng mục trên chỉ được đưa vào phase thực thi nếu:

- đã hoàn tất `stabilize`
- đã có mức `operational_hardening` tối thiểu
- có lý do nghiệp vụ hoặc dữ liệu benchmark rõ ràng

## Giả định kỹ thuật

- Kiến trúc ports/adapters hiện tại vẫn là ràng buộc chính.
- Public contract của 3 endpoint MVP được giữ ổn định trừ khi có quyết định mới trong decision log.
- Runtime config tiếp tục được nạp một lần khi khởi động ứng dụng.
- Đánh giá chất lượng phase sau MVP ưu tiên dữ liệu tiếng Việt trước.
- Team chấp nhận thêm adapter thật, persistence, CI và metric mà không yêu cầu đổi model nội bộ.

## Thứ tự ưu tiên

Thứ tự ưu tiên được khóa như sau:

1. Làm cho bản hiện tại chạy ổn định trong môi trường dev/staging.
2. Làm cho hệ thống quan sát được và chịu lỗi tốt hơn khi tích hợp hạ tầng thật.
3. Đo được chất lượng retrieval/generation bằng fixture và benchmark nhỏ nhưng ổn định.
4. Chỉ sau đó mới cân nhắc mở rộng tính năng.

## Nguyên tắc triển khai

- Không dùng feature mới để che vấn đề vận hành hoặc chất lượng chưa được đo.
- Mọi thay đổi behavior sau MVP vẫn phải đi kèm test hoặc benchmark thể hiện behavior mới.
- Nếu một thay đổi làm đổi thứ tự ưu tiên giữa các phase, phải ghi decision mới.
- Nếu cần mở rộng feature sớm do yêu cầu nghiệp vụ thật, phải nêu rõ feature đó đang chen vào phase nào và rủi ro gì bị chấp nhận.

## Trạng thái hiện tại

Chương `post-mvp` hiện đã hoàn tất ở mức roadmap đã định và được giữ lại như hồ sơ lịch sử triển khai.

Các spec mới sau mốc này nên chuyển sang track tài liệu riêng, bắt đầu tại:

- `docs/54-closeout-post-mvp.md`
- `docs/core/README.md`


---

## Source: `docs/history/post-mvp/18-spec-stabilize-va-hardening.md`

# 18. Spec Stabilize Và Hardening

## Mục lục
- Phase 1: Stabilize
- Phase 2: Operational hardening
- Guardrails

## Phase 1: Stabilize

### Mục tiêu

Biến bản MVP đã đóng scope thành một baseline nội bộ có thể:

- cài đặt được theo một luồng chuẩn
- chạy test được theo một lệnh chuẩn
- khởi động API được với cấu hình rõ ràng
- release nội bộ được mà không phụ thuộc kiến thức ngầm của một cá nhân

### Phạm vi

- chuẩn hóa local development setup
- chuẩn hóa lệnh lint/test
- bổ sung CI tối thiểu cho `ruff` và `pytest`
- viết runbook ngắn cho local/staging
- rà soát config runtime và logging tối thiểu

### Deliverable

- tài liệu setup/running đủ cho thành viên mới chạy được
- CI hoặc automation tương đương cho lint + test
- danh sách biến môi trường được dùng thật sự
- bản release nội bộ `v0.1` hoặc mốc tương đương

### Acceptance criteria

- Có một quy trình chuẩn để cài dependency dev và chạy test.
- Có một quy trình chuẩn để chạy API local.
- Lint và test được gọi thống nhất trong automation thay vì chỉ chạy thủ công.
- Logging vẫn giữ nguyên guardrail không log raw content.
- Không làm thay đổi public API contract của 3 endpoint hiện tại.

### Verification

- Chạy lint thành công.
- Chạy test suite hoặc ít nhất bộ test cốt lõi thành công.
- Khởi động API bằng cấu hình được tài liệu hóa.
- Rà log request để xác nhận vẫn có `request_id`, `use_case`, `error_code`, `latency_ms`.

## Phase 2: Operational hardening

### Mục tiêu

Tăng mức sẵn sàng vận hành của hệ thống khi thay dần thành phần demo bằng thành phần bền hơn.

### Phạm vi

- thay adapter demo bằng adapter có khả năng persistence hoặc tích hợp hạ tầng thật
- bổ sung timeout, retry và error mapping rõ hơn cho tích hợp ngoài
- tách config theo môi trường chạy
- bổ sung metrics hoặc observability thực dụng hơn cho các luồng chính
- thêm smoke test cho luồng `index -> retrieve -> generate`

### Deliverable

- vector/index storage không còn chỉ sống trong memory của process
- tích hợp ngoài có timeout/error handling tối thiểu
- tài liệu cấu hình theo môi trường
- smoke test hoặc môi trường staging check cho luồng chính

### Acceptance criteria

- Restart tiến trình không làm mất toàn bộ dữ liệu index nếu môi trường đã bật persistence.
- Lỗi từ provider/store được chuẩn hóa về behavior có thể quan sát được.
- Timeout và failure của tích hợp ngoài không làm treo request vô thời hạn.
- Các thay đổi hạ tầng không làm rò rỉ object framework/provider vào application/domain.
- Public API contract vẫn giữ nguyên nếu chưa có quyết định mới.

### Verification

- Chạy integration test cho adapter hoặc sandbox thật tối thiểu.
- Chạy smoke test cho luồng `index -> retrieve -> generate`.
- Review logging/metrics để xác nhận các failure path có thể phân biệt được.
- Kiểm tra lại decision `replace-by-document_id-within-index_name` trên storage thật.

## Guardrails

- Không chen feature expansion vào hai phase này như một cách hợp thức hóa refactor.
- Không đổi semantics `insufficient_context`, `citations`, `tags = contains-any` nếu chưa có quyết định mới.
- Không làm CI hoặc runbook phụ thuộc công cụ cục bộ không được ghi rõ trong repo.
- Không đổi contract HTTP chỉ vì adapter thật có giới hạn kỹ thuật khác với adapter demo; nếu cần đổi phải ghi decision trước.


---

## Source: `docs/history/post-mvp/19-spec-danh-gia-chat-luong-va-mo-rong.md`

# 19. Spec Đánh Giá Chất Lượng Và Mở Rộng

## Mục lục
- Phase 3: Quality evaluation
- Phase 4: Feature expansion
- Điều kiện vào phase

## Phase 3: Quality evaluation

### Mục tiêu

Thiết lập baseline định lượng cho chất lượng RAG để mọi thay đổi tiếp theo được đánh giá bằng dữ liệu thay vì cảm giác.

### Phạm vi

- khóa fixture/golden cases đủ đại diện cho câu hỏi tiếng Việt
- đo retrieval quality ở mức tối thiểu
- đo grounding/citation correctness ở mức ứng dụng
- đo latency cơ bản cho các luồng chính
- nếu có provider thật, đo thêm chi phí mỗi request ở mức gần đúng

### Chỉ số tối thiểu

- retrieval hit rate trên bộ fixture đã khóa
- tỷ lệ `insufficient_context`
- tỷ lệ citation hợp lệ theo rule `citations subset of used_chunks`
- latency `p50` và `p95` cho `index`, `retrieve`, `generate`
- tỷ lệ request lỗi theo nhóm lỗi chính

### Deliverable

- bộ fixture/golden cases sau MVP
- tài liệu benchmark nhỏ nhưng deterministic nhất có thể
- regression suite cho các case quan trọng
- baseline metric được chốt làm mốc so sánh

### Acceptance criteria

- Có ít nhất một bộ dữ liệu nhỏ dùng chung cho review, regression và benchmark.
- Có thể chạy lại benchmark theo cùng một quy trình.
- Mọi thay đổi liên quan chunking, retrieval hoặc generation có thể so sánh với baseline.
- Khi adapter/provider thật tạo ra biến thiên, spec vẫn khóa phần behavior phải ổn định ở application/API.

### Verification

- Chạy benchmark hoặc regression suite trên bộ fixture đã khóa.
- Lưu lại kết quả baseline theo định dạng mà team đọc được.
- Rà các golden case để bảo đảm chúng vẫn phản ánh contract hiện tại.

## Phase 4: Feature expansion

### Mục tiêu

Mở rộng khả năng của hệ thống sau khi đã có nền ổn định và baseline chất lượng đủ để đánh giá trade-off.

### Danh mục ưu tiên mặc định

1. ingestion từ file hoặc nguồn nội bộ thực tế
2. async ingestion hoặc background job nếu tải ingestion tăng
3. cải thiện retrieval quality nếu benchmark chưa đạt
4. streaming response nếu có nhu cầu UX rõ
5. auth/RBAC nếu xuất hiện nhu cầu chia quyền thật

### Điều không mặc định ưu tiên

- mở thêm endpoint công khai mới
- hybrid retrieval
- reranker
- bộ nhớ hội thoại dài hạn
- workflow orchestration phân tán quy mô lớn

### Acceptance criteria

- Mỗi feature mới phải có spec riêng nếu làm đổi behavior, contract hoặc boundary.
- Mỗi feature mới phải chỉ rõ vì sao không thể trì hoãn sau phase hiện tại.
- Feature mới phải có golden case hoặc benchmark tương ứng nếu nó tác động chất lượng retrieval/generation.
- Không dùng feature mới để bù cho thiếu sót của observability hoặc baseline đánh giá.

### Verification

- Review spec riêng của feature trước khi code.
- Có test hoặc benchmark chứng minh giá trị của feature đó.
- Có đánh giá rủi ro về coupling, chi phí vận hành và độ phức tạp triển khai.

## Điều kiện vào phase

- Chỉ vào `quality_evaluation` khi `stabilize` đã xong ở mức đủ chạy lặp lại.
- Chỉ vào `feature_expansion` khi đã có baseline tối thiểu từ `quality_evaluation`, trừ khi có yêu cầu nghiệp vụ khẩn cấp được chấp nhận rõ ràng.

## Ghi chú kiến trúc sau post-MVP

- Full migration cấu trúc `src/tuesday_rag` được chấp nhận như một phần của bước vào `feature_expansion`.
- Migration này ưu tiên layout capability-oriented nhưng phải bám boundary thực tế của codebase hiện tại, không ép tách cơ học mọi concern thành module độc lập.
- Migration này phải bám theo decision và guardrail trong `40-spec-quyet-dinh-migration-cau-truc-src.md`.


---

## Source: `docs/history/post-mvp/20-ke-hoach-trien-khai-sau-mvp.md`

# 20. Kế Hoạch Triển Khai Sau MVP

## Mục lục

- Thứ tự triển khai
- Phase 1
- Phase 2
- Phase 3
- Phase 4
- Deliverable theo phase
- Rủi ro
- Cách giảm rủi ro

## Thứ tự triển khai

Thứ tự đề xuất:

1. Khóa baseline vận hành và test của bản MVP hiện tại.
2. Tăng độ bền vận hành trước khi tăng độ rộng tính năng.
3. Thiết lập baseline chất lượng retrieval/generation.
4. Chỉ sau đó mới mở rộng feature theo nhu cầu thật.

## Phase 1

Mục tiêu:

- hoàn tất `stabilize`

Phạm vi:

- chuẩn hóa setup dev
- chuẩn hóa lint/test/run commands
- thêm CI tối thiểu
- viết runbook local/staging
- kiểm tra lại logging và runtime config

Deliverable:

- baseline nội bộ chạy được lặp lại
- CI xanh cho lint và test cốt lõi
- tài liệu setup/running ngắn gọn

## Phase 2

Mục tiêu:

- hoàn tất `operational_hardening`

Phạm vi:

- thay dần adapter demo bằng thành phần bền hơn
- bổ sung persistence
- thêm timeout/retry/error handling
- tăng observability cho failure path
- thêm smoke test cho luồng chính

Workstreams:

1. `persistence_and_runtime_wiring`
2. `integration_resilience_and_error_mapping`
3. `observability_and_smoke_test`

Deliverable:

- hệ thống không còn phụ thuộc hoàn toàn vào in-memory state
- có smoke test `index -> retrieve -> generate`
- có tài liệu cấu hình theo môi trường

## Phase 3

Mục tiêu:

- hoàn tất `quality_evaluation`

Phạm vi:

- khóa fixture/golden cases sau MVP
- tạo benchmark nhỏ
- đo retrieval quality, grounding, citation correctness
- đo latency cơ bản

Deliverable:

- baseline metric đầu tiên
- regression suite cho behavior nhạy cảm
- tài liệu benchmark và kết quả gốc

## Phase 4

Mục tiêu:

- mở rộng feature theo nhu cầu thật trên layout đã migrate

Phạm vi:

- hoàn tất migration theo `40-spec-quyet-dinh-migration-cau-truc-src.md` và `41-spec-target-layout-migration-phase-4.md` ở mức đủ làm nền cho nhịp feature đầu tiên
- triển khai feature đầu tiên đã được ưu tiên: `internal file ingestion` qua entrypoint nội bộ
- giữ nguyên 3 endpoint HTTP hiện tại và không mở thêm public contract mới trong nhịp này
- viết verification cho migration và feature mới mà không phá baseline hiện có

Deliverable:

- feature `internal file ingestion` đầu tiên sau MVP được ship có kiểm soát
- benchmark hoặc test chứng minh feature không làm regress behavior lõi
- layout `src/tuesday_rag` mới đủ ổn để feature đầu tiên có thể phát triển tiếp trên đó mà vẫn bám guardrail và boundary thực tế của codebase

Trạng thái hiện tại:

- Phase 4 nhịp đầu đã hoàn tất với `internal file ingestion` nội bộ cho `.txt`, `.md`, `.html`, `.pdf`
- batch CLI nội bộ đã có `--recursive`, `--output`, `--include`, `--exclude`, `--dry-run`
- verification đã được khóa bằng unit test, integration test, smoke test và regression suite

## Deliverable theo phase

| Phase | Deliverable chính                                   |
| ----- | --------------------------------------------------- |
| 1     | Baseline dev/test/release nội bộ ổn định            |
| 2     | Persistence + hardening + smoke test vận hành       |
| 3     | Baseline chất lượng và regression suite             |
| 4     | Feature mở rộng đầu tiên có spec và benchmark riêng |

## Rủi ro

| Rủi ro                                      | Tác động                                                  |
| ------------------------------------------- | --------------------------------------------------------- |
| Mở rộng feature quá sớm                     | đội mất tập trung, khó xác định lỗi do nền hay do feature |
| Thay adapter thật nhưng không có smoke test | lỗi tích hợp lọt qua review                               |
| Không có baseline benchmark                 | tuning theo cảm giác, dễ regress retrieval/generation     |
| Logging/metrics yếu                         | khó phân biệt lỗi dữ liệu, lỗi provider, lỗi ứng dụng     |
| Persistence mới làm lệch semantics cũ       | vi phạm contract hoặc policy re-index                     |

## Cách giảm rủi ro

- Khóa rõ thứ tự phase và chỉ lệch khi có decision mới.
- Mọi thay đổi adapter phải có integration test hoặc smoke test tương ứng.
- Thiết lập benchmark nhỏ sớm thay vì chờ đủ dữ liệu lớn.
- Giữ nguyên semantics cốt lõi của MVP trừ khi có quyết định mới.
- Review riêng các thay đổi liên quan persistence, retry, timeout và error mapping.


---

## Source: `docs/history/post-mvp/21-checklist-giai-doan-sau-mvp.md`

# 21. Checklist Giai Đoạn Sau MVP

## Checklist phase ordering

- [x] Đã chốt thứ tự `stabilize -> operational_hardening -> quality_evaluation -> feature_expansion`.
- [x] Đã xác nhận feature mới không mặc định chen vào trước `stabilize`.
- [x] Đã xác nhận phase sau MVP không tự động mở thêm endpoint công khai.

## Checklist stabilize

- [x] Có quy trình cài dependency dev rõ ràng.
- [x] Có lệnh chuẩn để chạy lint.
- [x] Có lệnh chuẩn để chạy test.
- [x] Có lệnh chuẩn để chạy API local.
- [x] Có CI hoặc automation tương đương cho lint + test.
- [x] Có runbook local/staging ngắn gọn.
- [x] Bộ spec chi tiết của Phase 1 đã đủ để giao việc theo workstream.

## Checklist operational hardening

- [x] Bộ spec chi tiết của Phase 2 đã đủ để giao việc theo workstream.
- [x] Dữ liệu index không còn phụ thuộc hoàn toàn vào memory của process.
- [x] Tích hợp ngoài có timeout tối thiểu.
- [x] Tích hợp ngoài có retry ở nơi phù hợp.
- [x] Error mapping cho failure path đã được rà lại.
- [x] Có smoke test cho luồng `index -> retrieve -> generate`.
- [x] Logging/metrics đủ để phân biệt nhóm lỗi chính.

## Checklist quality evaluation

- [x] Bộ spec chi tiết của Phase 3 đã đủ để giao việc theo workstream.
- [x] Có bộ fixture/golden cases sau MVP.
- [x] Có baseline retrieval quality.
- [x] Có baseline cho grounding/citation correctness.
- [x] Có baseline latency `p50/p95`.
- [x] Có regression suite cho case quan trọng.
- [x] Có nơi lưu kết quả benchmark ban đầu.

## Checklist feature expansion

- [x] Có decision rõ về việc thực hiện full migration cấu trúc `src/tuesday_rag` theo guardrail và boundary hiện có.
- [x] Feature đầu tiên sau MVP đã có spec riêng.
- [x] Feature đầu tiên sau MVP đã nêu rõ lý do ưu tiên.
- [x] Feature đầu tiên sau MVP có test hoặc benchmark chứng minh giá trị.
- [x] Feature đầu tiên sau MVP không phá contract hiện tại nếu chưa có decision mới.
- [x] Phase 4 nhịp đầu đã có implementation summary và runbook đủ để đóng phase.

## Checklist boundary và guardrails

- [x] Không có object provider/store/framework rò rỉ lên application/domain.
- [x] Không đổi semantics `insufficient_context`.
- [x] Không đổi semantics `citations`.
- [x] Không đổi semantics `tags = contains-any`.
- [x] Không log raw content ngoài mức tối thiểu cần thiết.

## Kết luận vào phase mở rộng

- [x] `stabilize` đã đạt mức done.
- [x] `operational_hardening` đã đạt mức done tối thiểu.
- [x] `quality_evaluation` đã có baseline đủ dùng.
- [x] Có quyết định rõ feature nào được làm tiếp theo.
- [x] Nhịp đầu của `feature_expansion` đã hoàn tất và có thể chuyển sang nhịp ưu tiên tiếp theo bằng decision/spec mới.


---

## Source: `docs/history/post-mvp/40-spec-quyet-dinh-migration-cau-truc-src.md`

# 40. Spec Quyết Định Migration Cấu Trúc `src`

## Migration Note

Đây là decision/spec historical cho quyết định migration, được viết khi target chính còn là `src/tuesday_rag`.

Kết quả implementation đã hoàn tất nhịp package migration ngày `2026-04-23` theo hướng:

- app shell ở `src/tuesday/api/`
- runtime ở `src/tuesday/runtime/`
- capability `rag` ở `src/tuesday/rag/`
- `src/tuesday_rag/` đã được loại bỏ sau giai đoạn chuyển tiếp

Vì vậy, các nhắc đến `src/tuesday_rag` bên dưới nên được đọc như bối cảnh lịch sử của quyết định, không phải layout source-of-truth hiện tại.

## Mục lục
- Mục tiêu
- Quyết định hiện tại
- Lý do chấp nhận full migration
- Phạm vi migration
- Lộ trình migration
- Guardrails
- Verification

## Mục tiêu

Khóa rõ quyết định kiến trúc sau post-MVP về việc migrate cấu trúc `src/tuesday_rag` theo hướng capability-oriented, để team có một hướng refactor thống nhất trước khi mở rộng feature sâu hơn.

## Quyết định hiện tại

Tại thời điểm sau Phase 3:

- **thực hiện full migration** cấu trúc `src/tuesday_rag`
- migration này được coi là một phần của bước vào `feature_expansion`
- feature expansion đầu tiên phải bám theo layout mới hoặc được thực hiện cùng nhịp migration
- mọi bước migrate phải bám theo guardrail và verification trong tài liệu này

Quyết định này áp dụng cho giai đoạn chuyển từ `quality_evaluation` sang `feature_expansion`.

## Lý do chấp nhận full migration

Ở thời điểm hiện tại repo đã có:

- baseline vận hành ổn định
- hardening tối thiểu
- benchmark và regression baseline đầu tiên

Team chấp nhận rằng ở mốc này full migration cấu trúc đem lại giá trị dài hạn lớn hơn chi phí refactor, vì roadmap tiếp theo cần một layout scale tốt hơn cho capability ownership và feature growth.

Lợi ích mong đợi của full migration:

- giảm việc một capability bị rải ra quá nhiều layer kỹ thuật
- chuẩn bị sẵn chỗ cho retrieval/index/generation phát triển mạnh hơn
- giảm ma sát khi thêm adapter, strategy và orchestration về sau
- giúp feature đầu tiên sau post-MVP không phải tiếp tục chồng lên layout chuyển tiếp hiện tại

Rủi ro đã được chấp nhận:

- chi phí delivery ngắn hạn tăng lên trong một nhịp
- nhiều file bị ảnh hưởng cùng lúc ở code, test và docs
- nguy cơ regress contract hoặc semantics nếu migration không có guardrail đủ chặt

## Phạm vi migration

Migration này bao gồm:

- thay đổi layout bên trong `src/tuesday_rag`
- gom code theo capability nhiều hơn thay vì chỉ theo layer kỹ thuật
- cập nhật import graph, dependency wiring, test path và docs liên quan
- giữ nguyên public API contract và semantics lõi trong suốt migration

Mục tiêu capability tối thiểu phải có trong layout mới:

- `ingestion`
- `retrieval`
- `generation`

Phần có thể vẫn tạm hoãn, gộp tạm vào capability khác, hoặc chỉ tạo placeholder nếu chưa có implementation thật hay boundary đủ rõ:

- `index` như một module độc lập
- `observability` như một module độc lập
- thêm `tenant` như một module độc lập
- thêm `pipeline` như một orchestration layer độc lập

Ở trạng thái codebase hiện tại:

- `index` vẫn chủ yếu là phần nội bộ của luồng `ingestion`, chưa phải một capability công khai hay use case độc lập
- `observability` vẫn chủ yếu là concern của API transport, runtime wiring và error classification, chưa phải một capability domain/application độc lập
- migration không nên ép tách hai phần này thành boundary riêng nếu chưa có use case hoặc contract mới thật sự cần

## Lộ trình migration

Migration phải đi theo trình tự:

1. khóa target layout mới ở mức package và boundary
2. migrate composition root và wiring mà không đổi contract HTTP
3. migrate capability theo thứ tự ưu tiên
4. sửa test, smoke test, benchmark và regression để chạy trên layout mới
5. chỉ bắt đầu feature expansion đầu tiên sau khi baseline verification của migration pass

Lộ trình gợi ý:

1. `retrieval`
2. `generation`
3. `ingestion`
4. phần nội bộ `index` đi cùng hoặc ngay sau `ingestion`
5. `observability`

Nguyên tắc ưu tiên:

- migrate theo cụm coupling thực tế thay vì tách cơ học theo tên capability
- `generation` đi sau hoặc cùng nhịp với `retrieval` vì đang phụ thuộc trực tiếp vào retrieval flow
- `ingestion` và phần nội bộ `index` nên đi cùng nhau vì chunking, embedding và replace/write semantics hiện vẫn nằm trong cùng một luồng nghiệp vụ
- `observability` chỉ nên tách thành module riêng nếu sau migration vẫn chứng minh được boundary rõ và không làm phình scope của nhịp refactor cấu trúc

`tenant` và `pipeline` chỉ nên được hiện thực đầy đủ sau khi có use case thật hoặc feature spec riêng.

## Guardrails

- Không dùng migration cấu trúc như cái cớ để lén đổi behavior nghiệp vụ.
- Không mở thêm public endpoint chỉ vì layout mới thuận hơn.
- Không đổi public API contract hoặc semantics lõi chỉ vì layout mới thuận tay hơn.
- Mọi bước migration phải có benchmark/regression chạy lại.
- Nếu trong lúc migrate phát sinh thay đổi boundary lớn ngoài spec này, phải ghi decision mới trước hoặc cùng lúc với code.

## Verification

- Review target layout mới trước khi move file hàng loạt.
- Chạy smoke test, regression suite và benchmark baseline sau các mốc migrate chính.
- Xác nhận import graph mới không làm rò object framework/provider vào application/domain.
- Chỉ coi migration hoàn tất khi feature expansion đầu tiên có thể phát triển trên layout mới mà không cần rollback cấu trúc.


---

## Source: `docs/history/post-mvp/41-spec-target-layout-migration-phase-4.md`

# 41. Spec Target Layout Migration Phase 4

## Migration Note

Tài liệu này là target-layout spec ở thời điểm trước khi team chốt app shell trung lập và capability nesting đầy đủ.

Sau migration package ngày `2026-04-23`, layout source-of-truth hiện tại là:

```text
src/tuesday/
  api/
  runtime/
  shared/
  rag/
    api/
    domain/
    ingestion/
    retrieval/
    generation/
    infrastructure/
    evaluation/
```

`src/tuesday_rag/` đã bị loại bỏ khỏi codebase. Vì vậy target layout bên dưới nên được đọc như mốc trung gian lịch sử của kế hoạch migration.

## Mục tiêu

Khóa target layout tối thiểu cho nhịp migration đầu của Phase 4, để team có một package map đủ rõ trước khi move file theo capability.

## Success Criteria

- Có package trung lập cho composition root và runtime wiring, không neo trực tiếp vào `api/`.
- Có đích package rõ cho các capability sẽ được migrate trước: `retrieval`, `generation`, `ingestion`.
- Trong suốt migration, public HTTP contract và semantics hiện tại không đổi.
- Các import tương thích tạm thời được giữ đủ ngắn để smoke/regression vẫn pass trong từng nhịp nhỏ.

## Target Layout

```text
src/tuesday_rag/
  api/
  runtime/
  shared/
  ingestion/
  retrieval/
  generation/
  domain/
  infrastructure/
  evaluation/
  config.py
```

## Boundary Notes

- `runtime/` chứa composition root, runtime wiring và bootstrap concern dùng chung.
- `shared/` chứa helper dùng chung mức nhỏ, không mang orchestration riêng của capability.
- `api/` chỉ giữ HTTP transport, schema, error mapping và request-level observability.
- `retrieval/` và `generation/` là hai capability ưu tiên migrate trước vì đang có coupling trực tiếp.
- `ingestion/` được migrate sau, đi cùng phần nội bộ `index` thay vì tách `index` thành capability riêng ngay từ đầu.
- `domain/` và `infrastructure/` được giữ ổn định trong nhịp đầu để tránh tăng scope refactor.

## Migration Order

1. Tách composition root khỏi `api/` sang `runtime/`.
2. Migrate cụm `retrieval + generation`.
3. Migrate cụm `ingestion + index` nội bộ.
4. Chỉ tách thêm concern khác khi có use case hoặc boundary rõ hơn.

## Compatibility Rule

- Trong giai đoạn chuyển tiếp, `api.dependencies` có thể tồn tại như compatibility shim trỏ sang runtime container mới.
- Không giữ shim lâu hơn cần thiết sau khi import graph chính đã được chuyển xong.


---

## Source: `docs/history/post-mvp/phase-1/22-phase-1-overview.md`

# 22. Phase 1 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa baseline phát triển nội bộ cho bản MVP hiện tại để team có thể:

- setup môi trường theo một cách thống nhất
- chạy lint/test bằng lệnh chuẩn
- khởi động API local mà không phải đoán config
- review và release nội bộ trên cùng một baseline

## Phạm vi

Phase 1 bao gồm 3 workstream:

1. `dev_setup_and_commands`
2. `ci_baseline`
3. `runbook_config_and_release_baseline`

## Ngoài phạm vi

- thay adapter demo bằng adapter thật
- thêm persistence
- thêm metrics mới ngoài observability tối thiểu đã có
- thêm endpoint mới
- tuning retrieval/generation quality
- feature expansion dưới bất kỳ hình thức nào

## Workstreams

### 1. Dev setup and commands

Chuẩn hóa cách cài dependency dev, cách chạy lint/test và cách chạy API local.

### 2. CI baseline

Đảm bảo lint và test không chỉ là quy ước miệng mà đã có automation lặp lại được.

### 3. Runbook, config and release baseline

Khóa tài liệu vận hành tối thiểu cho local/staging, liệt kê env vars đang dùng thật sự và xác định mốc release nội bộ cho bản stabilize.

## Tiêu chí thành công

- Thành viên mới trong team có thể vào repo và làm theo tài liệu để chạy được project.
- Kết quả lint/test không phụ thuộc vào thao tác thủ công không được ghi lại.
- Khi có lỗi cấu hình cơ bản, người vận hành có thể biết phải kiểm tra biến nào và command nào.
- Public contract và semantics lõi của MVP không thay đổi.


---

## Source: `docs/history/post-mvp/phase-1/23-spec-dev-setup-va-commands.md`

# 23. Spec Dev Setup Và Commands

## Migration Note

Tài liệu này ghi lại command baseline của Phase 1 trước migration package ngày `2026-04-23`.

Ở trạng thái repo hiện tại:

- command chạy API chuẩn là `python -m uvicorn tuesday.api.app:app --reload`
- package source-of-truth là `src/tuesday/`, không còn là `src/tuesday_rag/`
- nếu gặp command hoặc path cũ trong phần nội dung bên dưới, hiểu đó là historical reference

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Commands chuẩn cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Chuẩn hóa luồng phát triển cục bộ để mọi thành viên trong team dùng cùng một tập lệnh và cùng một cách setup cơ bản.

## Phạm vi

- hướng dẫn tạo hoặc dùng virtual environment
- hướng dẫn cài dependency dev
- khóa các lệnh chuẩn cho `lint`, `test`, `test target`, `run api`
- bảo đảm command phản ánh đúng cấu hình hiện có của repo

## Deliverable

- tài liệu hoặc `README` nêu rõ các command chuẩn
- command lint chuẩn cho repo
- command test chuẩn cho repo
- command chạy API local chuẩn cho repo

## Commands chuẩn cần có

Các command sau phải được coi là nguồn sự thật cho Phase 1:

- cài dependency dev:
  - `pip install -e '.[dev]'`
- chạy lint:
  - `ruff check .`
- chạy test toàn bộ:
  - `pytest`
- chạy test mục tiêu:
  - `pytest tests/unit`
  - `pytest tests/api/test_health.py`
- chạy API local:
  - `python -m uvicorn tuesday_rag.api.app:app --reload`

Nếu team muốn dùng wrapper như `make`, `just` hoặc script shell, wrapper đó phải gọi đúng các command nguồn sự thật ở trên hoặc thay thế chúng một cách rõ ràng trong spec.

## Acceptance criteria

- Có một cách setup môi trường dev được mô tả rõ ràng.
- Có một lệnh lint chuẩn và một lệnh test chuẩn được thống nhất.
- Có ví dụ chạy test mục tiêu khi cần iterate nhanh.
- Có một lệnh chuẩn để chạy API local.
- Không yêu cầu công cụ cục bộ ngoài Python/pip trừ khi repo cung cấp hoặc tài liệu hóa rõ.

## Verification

- Thực hiện luồng setup từ đầu trên môi trường sạch.
- Chạy `ruff check .` thành công hoặc ghi rõ failure hiện có cần xử lý.
- Chạy `pytest` thành công hoặc ghi rõ failure hiện có cần xử lý.
- Chạy `python -m uvicorn tuesday_rag.api.app:app --reload` và xác nhận app khởi động được.

## Guardrails

- Không thêm command song song gây mơ hồ kiểu nhiều cách chạy lint/test mà không có command chuẩn.
- Không làm command chuẩn phụ thuộc shell alias cá nhân.
- Không đổi package structure hay public contract chỉ để tiện local setup.


---

## Source: `docs/history/post-mvp/phase-1/24-spec-ci-baseline.md`

# 24. Spec CI Baseline

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Pipeline tối thiểu
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Thiết lập automation tối thiểu để lint và test được chạy lặp lại theo cùng một baseline, giảm lệ thuộc vào kiểm tra thủ công trước merge hoặc release nội bộ.

## Phạm vi

- chọn một cơ chế automation phù hợp với repo
- chạy lint trên codebase
- chạy test trên codebase
- bảo đảm automation dùng cùng command đã khóa ở workstream dev setup

## Deliverable

- một pipeline CI hoặc automation tương đương trong repo
- job lint
- job test
- tài liệu ngắn giải thích khi nào pipeline được coi là pass/fail

## Pipeline tối thiểu

Pipeline tối thiểu của Phase 1 phải gồm:

1. checkout source
2. setup Python phiên bản phù hợp với `pyproject.toml`
3. cài dependency dev
4. chạy `ruff check .`
5. chạy `pytest`

Có thể tách `lint` và `test` thành hai job riêng nếu phù hợp với nền CI được chọn.

## Acceptance criteria

- Automation chạy được từ repo mà không cần thao tác tay không được tài liệu hóa.
- Automation dùng đúng command chuẩn của repo.
- Lint và test được tách bạch đủ để biết lỗi đang nằm ở đâu.
- Kết quả pass/fail đủ rõ để dùng làm baseline review nội bộ.

## Verification

- Chạy pipeline trên một branch hoặc môi trường test.
- Xác nhận lỗi lint làm fail pipeline.
- Xác nhận lỗi test làm fail pipeline.
- Xác nhận khi code ổn thì pipeline pass trọn vẹn.

## Guardrails

- Không nhét thêm kiểm tra ngoài phạm vi Phase 1 như benchmark, deploy production hay e2e phức tạp.
- Không để CI chạy command khác với command local đã khóa mà không có lý do rõ ràng.
- Không coi cảnh báo không fail là đủ cho baseline lint/test của Phase 1.


---

## Source: `docs/history/post-mvp/phase-1/25-spec-runbook-config-va-release-baseline.md`

# 25. Spec Runbook, Config Và Release Baseline

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Nội dung runbook tối thiểu
- Cấu hình runtime cần khóa
- Release baseline
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Làm rõ cách chạy hệ thống ở local/staging và khóa baseline release nội bộ cho bản stabilize.

## Phạm vi

- viết runbook local/staging ngắn gọn
- liệt kê biến môi trường và config runtime đang dùng thật sự
- xác nhận logging hiện tại vẫn đúng guardrail
- xác định mốc release nội bộ cho phase 1

## Deliverable

- runbook local/staging
- danh sách env vars đang được ứng dụng đọc
- mô tả hành vi config mặc định và cách override
- ghi chú release baseline cho bản stabilize

## Nội dung runbook tối thiểu

Runbook tối thiểu phải trả lời được:

- cần cài gì trước khi chạy repo
- command nào để cài dependency dev
- command nào để chạy API local
- command nào để chạy lint/test
- endpoint nào dùng để health check
- nếu app không lên thì kiểm tra ở đâu trước

## Cấu hình runtime cần khóa

Phase 1 phải liệt kê tối thiểu:

- biến môi trường nào được `RuntimeConfig.from_env()` đọc
- giá trị mặc định đang được dùng khi env không tồn tại
- những biến nào là an toàn để override trong local/staging
- những override nào không được làm lệch public contract

## Release baseline

Release baseline của Phase 1 không yêu cầu:

- production deployment hoàn chỉnh
- versioning automation phức tạp
- changelog generator

Nhưng phải có:

- một mốc nội bộ được gọi tên rõ ràng, ví dụ `v0.1-internal-stabilize`
- danh sách ngắn các điều kiện để mốc đó được coi là hoàn tất

## Acceptance criteria

- Có tài liệu ngắn cho local/staging mà người khác đọc vào có thể làm theo.
- Có danh sách rõ các env vars và runtime config hiện đang có hiệu lực.
- Logging tối thiểu vẫn giữ các field `request_id`, `use_case`, `error_code`, `latency_ms`.
- Không log raw content hoặc dữ liệu nhạy cảm ngoài mức cần thiết.
- Có định nghĩa rõ thế nào là hoàn tất release baseline Phase 1.

## Verification

- Đối chiếu runbook với command thật trong repo.
- Đối chiếu env vars liệt kê với `RuntimeConfig`.
- Chạy app và gửi request mẫu để rà field logging tối thiểu.
- Review lại các điều kiện release baseline với checklist Phase 1.

## Guardrails

- Không thêm config mới chỉ để “chuẩn bị cho tương lai” nếu chưa phục vụ trực tiếp cho Phase 1.
- Không mở rộng runbook thành tài liệu production ops đầy đủ ở phase này.
- Không dùng release baseline như lý do để đổi contract hoặc semantics của MVP.


---

## Source: `docs/history/post-mvp/phase-1/26-checklist-phase-1-stabilize.md`

# 26. Checklist Phase 1 Stabilize

## Checklist tổng

- [x] Đã chia Phase 1 thành các workstream nhỏ có thể giao việc.
- [x] Đã xác định command chuẩn cho local development.
- [x] Đã xác định automation tối thiểu cho lint/test.
- [x] Đã xác định runbook/config/release baseline là một workstream riêng.

## Checklist dev setup and commands

- [x] Có hướng dẫn tạo hoặc dùng virtual environment.
- [x] Có hướng dẫn cài `pip install -e '.[dev]'`.
- [x] Có command chuẩn `ruff check .`.
- [x] Có command chuẩn `pytest`.
- [x] Có ví dụ test target để iterate nhanh.
- [x] Có command chuẩn chạy API local bằng `uvicorn`.

## Checklist CI baseline

- [x] Có pipeline lint.
- [x] Có pipeline test.
- [x] Pipeline dùng cùng command chuẩn với local.
- [x] Kết quả fail của lint được phân biệt với fail của test.

## Checklist runbook/config/release baseline

- [x] Có runbook local/staging ngắn gọn.
- [x] Có danh sách env vars đang được app đọc.
- [x] Có mô tả default config và override hợp lệ.
- [x] Có rà soát logging tối thiểu.
- [x] Có định nghĩa mốc release nội bộ cho Phase 1.

## Checklist guardrails

- [x] Không có feature mới chen vào Phase 1.
- [x] Không đổi public API contract.
- [x] Không đổi semantics `insufficient_context`.
- [x] Không đổi semantics `citations`.
- [x] Không đổi semantics `tags = contains-any`.


---

## Source: `docs/history/post-mvp/phase-1/27-runbook-config-va-release-baseline-implementation.md`

# 27. Runbook, Config Và Release Baseline Implementation

## Migration Note

Runbook này phản ánh baseline Phase 1 trước migration package ngày `2026-04-23`.

Áp dụng vào repo hiện tại cần đổi như sau:

- app entrypoint hiện tại là `python -m uvicorn tuesday.api.app:app --reload`
- runtime config hiện tại ưu tiên env prefix `TUESDAY_`
- default file persistence path hiện tại là `.tuesday/vector_store.json`

## Mục tiêu

Khóa baseline vận hành tối thiểu của Phase 1 cho local và môi trường staging-like, đồng thời chốt mốc release nội bộ cho bản stabilize.

## Runbook local

Điều kiện trước khi chạy:

- Cài Python `3.12+`.
- Có `pip`.
- Tạo hoặc dùng sẵn virtual environment.

Luồng chạy chuẩn:

1. Tạo virtual environment:
   `python -m venv .venv`
2. Kích hoạt virtual environment:
   `source .venv/bin/activate`
3. Cài dependency dev:
   `pip install -e '.[dev]'`
4. Chạy lint:
   `ruff check .`
5. Chạy test:
   `pytest`
6. Chạy API local:
   `python -m uvicorn tuesday_rag.api.app:app --reload`

Health check:

- Endpoint: `GET /health`
- Kết quả mong đợi: `{"status":"ok"}`

Nếu app không lên, kiểm tra theo thứ tự:

1. Có đang dùng Python `3.12+` không.
2. Virtual environment đã được kích hoạt chưa.
3. Dependency dev đã được cài bằng `pip install -e '.[dev]'` chưa.
4. `ruff check .` và `pytest` có đang fail không.
5. Có env override nào làm `RuntimeConfig.from_env()` fail validation không.

## Runbook staging-like

Phase 1 chưa định nghĩa production deployment hoàn chỉnh. Với môi trường staging-like, baseline tối thiểu là:

1. Checkout đúng revision cần kiểm tra.
2. Cài dependency bằng cùng command chuẩn:
   `pip install -e '.[dev]'`
3. Chạy `ruff check .` và `pytest` trước khi coi revision là hợp lệ.
4. Chạy API bằng:
   `python -m uvicorn tuesday_rag.api.app:app`
5. Gọi `GET /health` để xác nhận app lên thành công.

Guardrail của staging-like:

- Chỉ dùng các env override đã liệt kê bên dưới.
- Không đổi public API contract.
- Không đổi semantics `insufficient_context`, `citations`, `tags = contains-any`.

## Runtime config đang được đọc

`RuntimeConfig.from_env()` hiện đọc mọi field của `RuntimeConfig` qua prefix `TUESDAY_RAG_`.

| Env var | Default | Override local/staging | Ghi chú |
| --- | --- | --- | --- |
| `TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT` | `5` | Có | Phải nằm trong `1..20`. |
| `TUESDAY_RAG_RETRIEVAL_TOP_K_MIN` | `1` | Không khuyến khích | Thay đổi bound nội bộ, không cần cho baseline Phase 1. |
| `TUESDAY_RAG_RETRIEVAL_TOP_K_MAX` | `20` | Không khuyến khích | Thay đổi bound nội bộ, không cần cho baseline Phase 1. |
| `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_DEFAULT` | `5` | Có | Phải nằm trong `1..10`. |
| `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_MIN` | `1` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_MAX` | `10` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_DEFAULT` | `1000` | Có | Phải nằm trong `300..2000`. |
| `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_MIN` | `300` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_MAX` | `2000` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_DEFAULT` | `150` | Có | Phải nằm trong `0..300` và nhỏ hơn chunk size. |
| `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_MIN` | `0` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_MAX` | `300` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_COUNT_MAX` | `200` | Có, thận trọng | Giới hạn cứng tổng số chunk sinh ra từ một document. |
| `TUESDAY_RAG_CONTENT_LENGTH_MIN` | `1` | Không khuyến khích | Thay đổi validation boundary. |
| `TUESDAY_RAG_CONTENT_LENGTH_MAX` | `100000` | Có, thận trọng | Không được làm lệch contract request body hiện tại. |
| `TUESDAY_RAG_QUERY_LENGTH_MIN` | `1` | Không khuyến khích | Thay đổi validation boundary. |
| `TUESDAY_RAG_QUERY_LENGTH_MAX` | `2000` | Có, thận trọng | Không được làm lệch expectation của API hiện tại. |
| `TUESDAY_RAG_QUESTION_LENGTH_MIN` | `1` | Không khuyến khích | Thay đổi validation boundary. |
| `TUESDAY_RAG_QUESTION_LENGTH_MAX` | `2000` | Có, thận trọng | Không được làm lệch expectation của API hiện tại. |
| `TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER` | `Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn.` | Có | Chỉ đổi message fallback, không đổi semantics `insufficient_context=true`. |

## Default config và override hợp lệ

Default hiện tại là baseline chuẩn của repo. Override chỉ được coi là hợp lệ trong Phase 1 nếu:

- không làm `RuntimeConfig.validate()` fail
- không đổi public API contract
- không đổi semantics `insufficient_context`
- không đổi semantics `citations`
- không đổi semantics `tags = contains-any`

Override nên ưu tiên cho tuning cục bộ hoặc staging-like:

- `TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT`
- `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_DEFAULT`
- `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_DEFAULT`
- `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_DEFAULT`
- `TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER`

## Logging baseline

Logging tối thiểu của Phase 1 đã có trong API middleware và error handler.

Field phải có:

- `request_id`
- `use_case`
- `error_code`
- `latency_ms`

Guardrail logging:

- Không log raw content của tài liệu hoặc câu hỏi.
- Không log dữ liệu nhạy cảm ngoài mức tối thiểu cần để phân loại lỗi request.

## Release baseline

Mốc release nội bộ của Phase 1:

- `v0.1-internal-stabilize`

Điều kiện hoàn tất mốc này:

1. Repo có hướng dẫn setup dev và command chuẩn.
2. Repo có CI baseline chạy `ruff check .` và `pytest`.
3. Runbook local/staging-like và baseline config đã được ghi lại.
4. Logging tối thiểu giữ đủ `request_id`, `use_case`, `error_code`, `latency_ms`.
5. Không có thay đổi public API contract hoặc semantics lõi của MVP.

## CI pass/fail baseline

Pipeline CI Phase 1 được coi là `pass` khi:

- job `lint` pass với command `ruff check .`
- job `test` pass với command `pytest`

Pipeline CI Phase 1 được coi là `fail` khi:

- job `lint` fail
- job `test` fail
- dependency không cài được bằng `pip install -e '.[dev]'`
- repo không setup được Python `3.12` như yêu cầu của `pyproject.toml`

Ý nghĩa baseline này:

- Nếu `lint` fail, lỗi nằm ở chuẩn code hoặc import/order theo cấu hình hiện tại của repo.
- Nếu `test` fail, lỗi nằm ở hành vi hoặc wiring đang được test.
- Không coi trạng thái warning-only là pass cho baseline review nội bộ của Phase 1.


---

## Source: `docs/history/post-mvp/phase-1/README.md`

# Phase 1: Stabilize

## Mục lục
- Mục tiêu phase
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 1 nhằm biến bản MVP đã đóng scope thành một baseline nội bộ có thể cài đặt, chạy test, chạy API và release lặp lại được mà không phụ thuộc kiến thức ngầm của cá nhân triển khai.

Phase này không thêm feature mới. Nó chuẩn hóa nền phát triển và vận hành tối thiểu để Phase 2 trở đi có thể triển khai trên một baseline ổn định.

## Danh sách spec con

- `22-phase-1-overview.md`
- `23-spec-dev-setup-va-commands.md`
- `24-spec-ci-baseline.md`
- `25-spec-runbook-config-va-release-baseline.md`
- `26-checklist-phase-1-stabilize.md`

## Artefact triển khai

- `../../../README.md`
- `27-runbook-config-va-release-baseline-implementation.md`
- `../../../.github/workflows/ci.yml`

## Thứ tự đọc

1. `22-phase-1-overview.md`
2. `23-spec-dev-setup-va-commands.md`
3. `24-spec-ci-baseline.md`
4. `25-spec-runbook-config-va-release-baseline.md`
5. `26-checklist-phase-1-stabilize.md`

## Điều kiện done

- Có luồng chuẩn để cài dependency dev, chạy lint, chạy test và chạy API local.
- Có automation tối thiểu cho lint và test.
- Có runbook ngắn cho local/staging.
- Có danh sách cấu hình runtime và biến môi trường đang dùng thật sự.
- Không đổi public API contract và không nới scope sang feature mới.


---

## Source: `docs/history/post-mvp/phase-2/28-phase-2-overview.md`

# 28. Phase 2 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa baseline vận hành sau MVP ở mức:

- dữ liệu index không bị mất hoàn toàn chỉ vì restart process
- failure của provider/store không treo request vô thời hạn
- lỗi tích hợp được quan sát và phân loại rõ hơn
- team có một luồng smoke test ngắn cho hành trình chính

## Phạm vi

Phase 2 bao gồm 3 workstream:

1. `persistence_and_runtime_wiring`
2. `integration_resilience_and_error_mapping`
3. `observability_and_smoke_test`

## Ngoài phạm vi

- đổi public API contract hiện tại
- thêm endpoint công khai mới
- thêm feature retrieval mới như hybrid retrieval hoặc reranker
- production deployment hoàn chỉnh
- autoscaling, distributed orchestration hoặc workflow queue đầy đủ
- benchmark chất lượng retrieval/generation theo baseline định lượng

## Workstreams

### 1. Persistence and runtime wiring

Đưa index/storage ra khỏi trạng thái chỉ sống trong memory của process và khóa cách chọn adapter theo môi trường chạy.

### 2. Integration resilience and error mapping

Đảm bảo tích hợp ngoài có timeout tối thiểu, retry ở nơi hợp lý và failure path được map thành behavior quan sát được.

### 3. Observability and smoke test

Bổ sung quan sát tối thiểu cho các luồng chính và khóa một smoke test ngắn cho chuỗi `index -> retrieve -> generate`.

Workstream này là hardening concern ở mức vận hành và verification; nó không tự động hàm ý `observability` phải trở thành một capability hoặc module kiến trúc độc lập ở các phase sau.

## Tiêu chí thành công

- Team có thể khởi động repo ở chế độ dùng adapter persistence-backed hoặc thành phần bền hơn mà không đổi contract HTTP.
- Khi provider/store lỗi hoặc chậm, request không treo vô thời hạn và log/metric cho biết nhóm lỗi chính.
- Có một smoke test ngắn đủ để phát hiện lỗi wiring giữa ingestion, retrieval và generation.
- Application/domain vẫn chỉ phụ thuộc protocol nội bộ, không bị lộ object framework/provider cụ thể.


---

## Source: `docs/history/post-mvp/phase-2/29-spec-persistence-va-runtime-wiring.md`

# 29. Spec Persistence Và Runtime Wiring

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Baseline cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Loại bỏ phụ thuộc tuyệt đối vào `InMemoryVectorStore` trong môi trường vận hành và khóa cách wiring adapter theo runtime config.

## Phạm vi

- thêm ít nhất một storage/index adapter có persistence
- giữ nguyên protocol `VectorStore` ở application/domain
- xác định cách chọn adapter theo runtime config hoặc environment
- khóa hành vi tối thiểu của storage mới đối với policy `replace-by-document_id-within-index_name`
- tài liệu hóa rõ local/staging dùng adapter nào và cách bật persistence

## Deliverable

- adapter persistence-backed hoặc storage thật đủ dùng cho phase này
- runtime wiring chọn được giữa adapter demo và adapter bền hơn
- tài liệu config theo môi trường cho storage
- integration test chứng minh policy re-index vẫn đúng trên storage mới

## Baseline cần có

Phase 2 không bắt buộc chốt vendor ngay trong spec. Tuy nhiên implementation phải khóa rõ:

- adapter nào là mặc định cho local development
- adapter nào được dùng cho staging-like khi cần persistence
- env hoặc config nào quyết định lựa chọn adapter
- vị trí dữ liệu được persist trong local/staging-like
- hành vi khi storage chưa sẵn sàng hoặc config storage không hợp lệ

Storage mới tối thiểu phải giữ được:

- tách biệt theo `index_name`
- policy `replace-by-document_id-within-index_name`
- retrieval filter semantics hiện tại, đặc biệt `tags = contains-any`
- kết quả query không làm lệch public contract hiện tại

## Acceptance criteria

- Khi bật persistence, restart process không làm mất toàn bộ index đã được ghi trước đó.
- Runtime wiring không yêu cầu sửa code để đổi giữa adapter demo và adapter bền hơn.
- Lỗi cấu hình hoặc lỗi khởi tạo storage được fail fast ở startup hoặc được log rõ ràng.
- Storage mới không làm rò rỉ object framework/provider vào application/domain.
- Quyết định storage không làm đổi semantics re-index đã chốt trong decision log.

## Verification

- Chạy integration test cho adapter persistence-backed hoặc storage thật tối thiểu.
- Chạy scenario ghi document, restart process, rồi retrieve lại trên cùng `index_name`.
- Kiểm tra policy `replace-by-document_id-within-index_name` vẫn đúng trên storage mới.
- Đối chiếu runtime wiring với runbook/config theo môi trường.

## Guardrails

- Không dùng persistence như lý do để đổi contract HTTP hoặc response schema.
- Không thêm abstraction mới ở application/domain nếu protocol hiện tại đã đủ.
- Không hard-code adapter thật vào use case hoặc service layer.
- Không coi “có file dữ liệu trên disk” là đủ nếu chưa chứng minh được retrieval sau restart.


---

## Source: `docs/history/post-mvp/phase-2/30-spec-integration-resilience-va-error-mapping.md`

# 30. Spec Integration Resilience Và Error Mapping

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Failure handling baseline
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Khóa baseline chịu lỗi tối thiểu cho các tích hợp ngoài để request không treo vô thời hạn và failure path được phân loại nhất quán.

## Phạm vi

- thêm timeout tối thiểu cho provider/store có I/O ngoài process
- thêm retry ở nơi phù hợp, có giới hạn rõ ràng
- chuẩn hóa error mapping giữa lỗi hạ tầng và domain/API behavior hiện có
- tài liệu hóa điều kiện nào nên retry và điều kiện nào phải fail ngay

## Deliverable

- config timeout cho provider hoặc storage tích hợp ngoài
- chính sách retry tối thiểu cho failure tạm thời
- bảng hoặc tài liệu ngắn mô tả mapping lỗi hạ tầng sang nhóm lỗi quan sát được
- test hoặc integration check cho ít nhất một failure path quan trọng

## Failure handling baseline

Spec này khóa các nguyên tắc sau:

- timeout phải hữu hạn và được cấu hình rõ
- retry chỉ áp dụng cho lỗi tạm thời hoặc timeout có khả năng hồi phục
- retry phải có số lần giới hạn; không retry vô hạn
- lỗi không thể hồi phục do input/config phải fail ngay, không retry
- khi hết retry hoặc timeout, log phải cho biết request đang fail ở provider nào hoặc storage nào

Nếu phase này vẫn còn adapter demo trong một số môi trường, spec phải chỉ rõ:

- behavior resilience nào chỉ áp dụng khi có tích hợp ngoài thật
- behavior nào vẫn phải được kiểm thử bằng fake/integration test

## Acceptance criteria

- Không có request nào phụ thuộc provider/store ngoài process mà có thể treo vô thời hạn vì thiếu timeout.
- Retry policy được giới hạn và có lý do rõ cho từng loại lỗi.
- Error mapping giúp phân biệt tối thiểu lỗi ứng dụng, lỗi storage và lỗi provider.
- Public API contract không bị nới rộng chỉ để lộ lỗi hạ tầng nội bộ.
- Failure path chính có log hoặc metric đủ để điều tra mà không log raw content.

## Verification

- Tạo ít nhất một test hoặc sandbox check mô phỏng timeout/failure của provider hoặc storage.
- Xác nhận timeout dẫn đến kết quả fail có thể quan sát được thay vì treo request.
- Xác nhận retry không áp dụng cho lỗi input hoặc config sai.
- Review lại error mapping ở API để chắc lỗi hạ tầng được phân loại rõ hơn.

## Guardrails

- Không thêm retry mù cho mọi exception.
- Không dùng resilience layer để che lỗi contract hoặc lỗi validation.
- Không thêm field mới vào public response chỉ để lộ chi tiết hạ tầng nội bộ.
- Không làm coupling application/domain với SDK client cụ thể.


---

## Source: `docs/history/post-mvp/phase-2/31-spec-observability-va-smoke-test.md`

# 31. Spec Observability Và Smoke Test

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Observability baseline
- Smoke test baseline
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Đảm bảo luồng chính của hệ thống có thể được kiểm tra nhanh sau thay đổi hạ tầng và failure path đủ tín hiệu để chẩn đoán.

## Phạm vi

- rà logging hiện có và bổ sung field/metric tối thiểu nếu còn thiếu
- định nghĩa nhóm lỗi chính cần phân biệt
- viết hoặc tài liệu hóa smoke test cho `index -> retrieve -> generate`
- khóa command hoặc script chạy smoke test trong local/staging-like

Spec này khóa một workstream hardening ở mức vận hành; nó không mặc định yêu cầu tạo `observability` như một capability hoặc module kiến trúc độc lập.

## Deliverable

- baseline observability cho các request chính
- định nghĩa tối thiểu các nhóm lỗi cần phân biệt
- smoke test ngắn cho luồng `index -> retrieve -> generate`
- runbook ngắn chỉ ra khi smoke test fail thì kiểm tra gì trước

## Observability baseline

Logging hoặc metrics của Phase 2 tối thiểu phải giúp phân biệt:

- lỗi ứng dụng hoặc validation
- lỗi storage hoặc persistence
- lỗi embedding provider
- lỗi generation provider
- timeout hoặc retry exhausted

Phase 1 đã khóa các field:

- `request_id`
- `use_case`
- `error_code`
- `latency_ms`

Phase 2 có thể bổ sung field hoặc metric nội bộ, nhưng không được bỏ các field trên.

## Smoke test baseline

Smoke test tối thiểu phải kiểm chứng được chuỗi:

1. index một document hợp lệ
2. retrieve được chunk liên quan từ cùng `index_name`
3. generate trả lời grounded dựa trên chunk đã retrieve

Smoke test nên đủ ngắn để dùng:

- sau khi thay adapter persistence
- sau khi đổi config timeout/retry
- trước khi coi bản build staging-like là hợp lệ

## Acceptance criteria

- Team có một command hoặc script smoke test rõ ràng cho luồng chính.
- Khi smoke test fail, log/metric đủ để biết đang fail ở ingest, retrieve hay generate.
- Logging/metric mới không log raw content ngoài mức tối thiểu cần thiết.
- Smoke test không phụ thuộc dữ liệu tay không được tài liệu hóa.
- Kết quả smoke test có thể dùng làm check nhanh sau thay đổi hạ tầng.

## Verification

- Chạy smoke test trên local hoặc staging-like với adapter Phase 2.
- Cố tình tạo ít nhất một failure path để xác nhận tín hiệu observability đủ dùng.
- Review log hoặc metric của smoke test thành công và thất bại.
- Đối chiếu lại với checklist Phase 2 trước khi coi hardening là done.

## Guardrails

- Không biến smoke test thành benchmark latency hoặc quality đầy đủ của Phase 3.
- Không dùng observability như lý do để log nội dung nhạy cảm.
- Không tạo smoke test chỉ pass với adapter demo nhưng không phản ánh wiring Phase 2.


---

## Source: `docs/history/post-mvp/phase-2/32-checklist-phase-2-operational-hardening.md`

# 32. Checklist Phase 2 Operational Hardening

## Checklist tổng

- [x] Đã chia Phase 2 thành các workstream nhỏ có thể giao việc.
- [x] Đã khóa boundary Phase 2 không mở rộng public API contract.
- [x] Đã xác định persistence/runtime wiring là một workstream riêng.
- [x] Đã xác định resilience/error mapping là một workstream riêng.
- [x] Đã xác định observability/smoke test là một workstream riêng.

## Checklist persistence and runtime wiring

- [x] Có storage/index adapter không còn phụ thuộc hoàn toàn vào memory của process.
- [x] Có runtime wiring rõ ràng để chọn adapter theo môi trường.
- [x] Có tài liệu config local/staging cho adapter persistence-backed.
- [x] Có integration test cho storage mới.
- [x] Có kiểm chứng `replace-by-document_id-within-index_name` trên storage mới.

## Checklist integration resilience and error mapping

- [x] Có timeout tối thiểu cho tích hợp ngoài.
- [x] Có retry ở nơi phù hợp với failure tạm thời.
- [x] Có giới hạn retry rõ ràng.
- [x] Có rà soát error mapping cho failure path chính.
- [x] Có test hoặc sandbox check cho ít nhất một failure path timeout hoặc retry.

## Checklist observability and smoke test

- [x] Có định nghĩa nhóm lỗi chính cần phân biệt.
- [x] Có logging hoặc metrics đủ để phân biệt lỗi ứng dụng, storage, provider.
- [x] Có smoke test `index -> retrieve -> generate`.
- [x] Có command hoặc script rõ ràng để chạy smoke test.
- [x] Có runbook ngắn cho việc đọc tín hiệu khi smoke test fail.

## Checklist guardrails

- [x] Không có feature mới chen vào Phase 2.
- [x] Không đổi public API contract.
- [x] Không đổi semantics `insufficient_context`.
- [x] Không đổi semantics `citations`.
- [x] Không đổi semantics `tags = contains-any`.
- [x] Không log raw content ngoài mức tối thiểu cần thiết.


---

## Source: `docs/history/post-mvp/phase-2/33-runbook-persistence-resilience-va-smoke.md`

# 33. Runbook Persistence, Resilience Và Smoke Test

## Migration Note

Runbook này mô tả trạng thái Phase 2 trước migration package ngày `2026-04-23`.

Trong repo hiện tại, khi áp dụng hướng dẫn bên dưới cần quy đổi:

- `TUESDAY_RAG_*` thành `TUESDAY_*` cho env mới
- `.tuesday-rag/vector_store.json` thành `.tuesday/vector_store.json`
- `python -m uvicorn tuesday_rag.api.app:app --reload` thành `python -m uvicorn tuesday.api.app:app --reload`

## Mục tiêu

Ghi lại baseline triển khai thực tế của Phase 2 để local và staging-like có thể bật persistence, chạy smoke test và đọc tín hiệu lỗi chính mà không cần suy đoán.

## Runtime wiring

Phase 2 hiện hỗ trợ 2 chế độ vector store:

- `memory`
- `file`

Env điều khiển:

- `TUESDAY_RAG_VECTOR_STORE_BACKEND`
- `TUESDAY_RAG_VECTOR_STORE_FILE_PATH`

Giá trị mặc định:

- `TUESDAY_RAG_VECTOR_STORE_BACKEND=memory`
- `TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/vector_store.json`

Khuyến nghị theo môi trường:

- local development mặc định: `memory`
- local cần kiểm tra persistence: `file`
- staging-like: `file` hoặc adapter bền hơn tương đương, nhưng phải giữ cùng semantics hiện tại

Ví dụ bật persistence ở local hoặc staging-like:

```bash
export TUESDAY_RAG_VECTOR_STORE_BACKEND=file
export TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/vector_store.json
python -m uvicorn tuesday_rag.api.app:app --reload
```

## Resilience config

Phase 2 khóa timeout và retry tối thiểu qua env:

- `TUESDAY_RAG_EMBEDDING_TIMEOUT_MS`
- `TUESDAY_RAG_EMBEDDING_MAX_RETRIES`
- `TUESDAY_RAG_GENERATION_TIMEOUT_MS`
- `TUESDAY_RAG_GENERATION_MAX_RETRIES`
- `TUESDAY_RAG_VECTOR_STORE_TIMEOUT_MS`
- `TUESDAY_RAG_VECTOR_STORE_MAX_RETRIES`

Giá trị mặc định:

- timeout: `1000ms`
- retry: `0`

Nguyên tắc vận hành:

- timeout luôn hữu hạn
- retry chỉ là bounded retry
- không retry lỗi input hoặc config sai
- public API contract không đổi khi failure hạ tầng xảy ra

## Observability baseline

Logging của Phase 2 giữ các field từ Phase 1:

- `request_id`
- `use_case`
- `error_code`
- `latency_ms`

Và bổ sung:

- `failure_group`
- `failure_component`
- `failure_mode`
- `retry_count`
- `timeout_ms`

Các nhóm lỗi chính hiện được phân biệt:

- `application`
- `provider`
- `storage`

## Smoke test

Command smoke test in-process:

```bash
python scripts/smoke_test.py
```

Command smoke test với API đang chạy:

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

Smoke test kiểm chứng chuỗi:

1. `POST /documents/index`
2. `POST /retrieve`
3. `POST /generate`

## Khi smoke test fail

Kiểm tra theo thứ tự:

1. API có đang dùng config backend đúng như mong đợi không.
2. Nếu dùng `file`, đường dẫn trong `TUESDAY_RAG_VECTOR_STORE_FILE_PATH` có ghi được không.
3. Timeout/retry env có đang quá thấp hoặc sai so với môi trường hiện tại không.
4. Log `request.failed` đang báo `failure_group` nào.
5. `failure_component` là `embedding_provider`, `generation_provider`, `vector_store` hay `request_validation`.

## Checklist done của implementation Phase 2

- Có file-backed vector store để giữ dữ liệu qua restart process.
- Có runtime wiring chọn `memory` hoặc `file` qua env.
- Có timeout/retry wrapper cho embedding provider, generation provider và vector store.
- Có smoke test command rõ ràng.
- Có logging đủ để phân biệt nhóm lỗi chính mà không log raw content.


---

## Source: `docs/history/post-mvp/phase-2/README.md`

# Phase 2: Operational Hardening

## Mục lục
- Mục tiêu phase
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 2 nhằm đưa baseline Phase 1 sang mức vận hành cứng cáp hơn trước khi bắt đầu đo benchmark chất lượng hoặc mở rộng feature.

Phase này tập trung vào độ bền vận hành, khả năng quan sát và failure handling khi thay thành phần demo bằng thành phần bền hơn. Phase này không mở rộng public API contract.

## Danh sách spec con

- `28-phase-2-overview.md`
- `29-spec-persistence-va-runtime-wiring.md`
- `30-spec-integration-resilience-va-error-mapping.md`
- `31-spec-observability-va-smoke-test.md`
- `32-checklist-phase-2-operational-hardening.md`

## Artefact triển khai

- `33-runbook-persistence-resilience-va-smoke.md`
- `../../../scripts/smoke_test.py`

## Thứ tự đọc

1. `28-phase-2-overview.md`
2. `29-spec-persistence-va-runtime-wiring.md`
3. `30-spec-integration-resilience-va-error-mapping.md`
4. `31-spec-observability-va-smoke-test.md`
5. `32-checklist-phase-2-operational-hardening.md`

## Điều kiện done

- Có storage/index adapter không còn phụ thuộc hoàn toàn vào memory của process.
- Có runtime wiring rõ ràng để bật persistence hoặc adapter bền hơn theo môi trường.
- Tích hợp ngoài có timeout tối thiểu, retry ở nơi phù hợp và error mapping có thể quan sát được.
- Có smoke test cho luồng `index -> retrieve -> generate`.
- Logging hoặc metrics đủ để phân biệt tối thiểu nhóm lỗi ứng dụng, provider và storage.
- Không đổi public API contract hoặc semantics lõi của MVP nếu chưa có decision mới.


---

## Source: `docs/history/post-mvp/phase-3/34-phase-3-overview.md`

# 34. Phase 3 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa baseline đánh giá chất lượng sau hardening ở mức:

- team có bộ dữ liệu chung để review, regression và benchmark
- retrieval/generation được đo bằng một bộ chỉ số tối thiểu
- các thay đổi về chunking, retrieval hoặc generation có thể so sánh với mốc ban đầu
- kết quả benchmark đầu tiên được lưu và đọc lại được

## Phạm vi

Phase 3 bao gồm 3 workstream:

1. `fixtures_and_golden_cases`
2. `benchmark_and_baseline_metrics`
3. `regression_suite_and_result_storage`

## Ngoài phạm vi

- tuning production quy mô lớn
- benchmark tải cao hoặc benchmark chi phí chi tiết theo production traffic
- mở rộng feature retrieval mới như hybrid hoặc reranker
- thay đổi contract HTTP để phục vụ benchmarking
- dashboard observability hoàn chỉnh kiểu production BI

## Workstreams

### 1. Fixtures and golden cases

Khóa bộ dữ liệu và kỳ vọng chuẩn để team dùng chung khi review, regression và benchmark.

### 2. Benchmark and baseline metrics

Định nghĩa benchmark nhỏ, deterministic nhất có thể và các chỉ số tối thiểu phải đo.

### 3. Regression suite and result storage

Biến các case quan trọng thành regression suite có thể chạy lại và xác định nơi lưu baseline đầu tiên.

## Tiêu chí thành công

- Một người mới vào repo có thể chạy fixture, benchmark và đọc baseline theo một quy trình rõ.
- Thay đổi về retrieval/generation không còn được đánh giá chỉ bằng demo cảm tính.
- Kết quả benchmark đầu tiên đủ để làm mốc so sánh khi bước sang feature expansion.
- Application/API contract vẫn được giữ ổn định trong suốt Phase 3.


---

## Source: `docs/history/post-mvp/phase-3/35-spec-fixtures-va-golden-cases.md`

# 35. Spec Fixtures Và Golden Cases

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Baseline cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Khóa bộ fixture và golden cases sau MVP để mọi benchmark, regression và review đều dựa trên cùng một tập dữ liệu nhỏ nhưng đủ đại diện.

## Phạm vi

- rà bộ fixture hiện có của repo
- chốt bộ golden cases sau MVP cho retrieval và generation
- bổ sung case còn thiếu nếu có regression quan trọng chưa được phủ
- giữ fixture deterministic và ưu tiên tiếng Việt

## Deliverable

- danh sách fixture/golden cases được khóa cho Phase 3
- tài liệu mô tả input, kỳ vọng và lý do giữ từng case
- mapping giữa golden case và endpoint hoặc behavior cần bảo vệ

## Baseline cần có

Phase 3 tối thiểu phải khóa:

- ít nhất một fixture retrieval match tốt
- ít nhất một fixture retrieval no-match
- ít nhất một fixture generation grounded có citation hợp lệ
- ít nhất một fixture generation `insufficient_context`
- ít nhất một fixture liên quan chunking hoặc nhiều chunk để tránh benchmark chỉ xoay quanh happy path quá ngắn

Golden cases phải chỉ rõ:

- phần behavior nào phải ổn định tuyệt đối
- phần nào có thể biến thiên nếu provider thật được bật sau này
- phần nào là contract/API invariant chứ không chỉ là output text mẫu

## Acceptance criteria

- Có một bộ fixture nhỏ dùng chung cho benchmark và regression.
- Golden case bám đúng contract hiện tại của `/documents/index`, `/retrieve`, `/generate`.
- Nếu có case mới, lý do thêm case được mô tả rõ thay vì thêm dữ liệu tràn lan.
- Bộ fixture đủ đại diện cho câu hỏi tiếng Việt và semantics lõi hiện tại.

## Verification

- Đối chiếu fixture/golden cases với docs hiện có và test hiện có.
- Rà từng golden case để chắc expected behavior không mâu thuẫn contract hiện tại.
- Kiểm tra mỗi case đều có mục đích rõ và không trùng lặp vô nghĩa.

## Guardrails

- Không biến fixture Phase 3 thành bộ dữ liệu lớn khó review.
- Không khóa expected text quá chi tiết nếu implementation/provider thật có biến thiên hợp lý.
- Không thêm case chỉ để phục vụ feature chưa thuộc scope.


---

## Source: `docs/history/post-mvp/phase-3/36-spec-benchmark-va-baseline-metrics.md`

# 36. Spec Benchmark Và Baseline Metrics

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Chỉ số tối thiểu
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Định nghĩa benchmark nhỏ nhưng lặp lại được để đo retrieval quality, grounding/citation correctness và latency cơ bản.

## Phạm vi

- chọn command hoặc script benchmark chuẩn cho repo
- xác định cách chạy benchmark trên bộ fixture đã khóa
- đo các chỉ số tối thiểu của Phase 3
- chốt format kết quả baseline đầu tiên

## Deliverable

- command hoặc script benchmark chuẩn
- mô tả cách benchmark dùng fixture nào và chạy trong điều kiện nào
- kết quả baseline đầu tiên theo format đọc được
- ghi chú cách diễn giải kết quả và giới hạn của benchmark

## Chỉ số tối thiểu

Phase 3 tối thiểu phải đo:

- retrieval hit rate trên bộ fixture đã khóa
- tỷ lệ `insufficient_context`
- tỷ lệ citation hợp lệ theo rule `citations subset of used_chunks`
- latency `p50` và `p95` cho `index`, `retrieve`, `generate`
- nếu có lỗi, phân nhóm lỗi ở mức đủ đọc được

Nếu provider thật tạo biến thiên, benchmark phải phân biệt:

- chỉ số deterministic ở application/API
- chỉ số có thể biến thiên do provider hoặc timing môi trường

## Acceptance criteria

- Có thể chạy lại benchmark bằng cùng command hoặc script.
- Benchmark cho kết quả đủ ổn định để so sánh các thay đổi quan trọng.
- Kết quả baseline đầu tiên được đọc được mà không cần suy luận từ log thô.
- Benchmark không đòi hỏi hạ tầng production để chạy.

## Verification

- Chạy benchmark ít nhất một lần trên bộ fixture đã khóa.
- Lưu kết quả theo format mà team có thể review.
- Đối chiếu chỉ số benchmark với semantics và contract hiện tại.

## Guardrails

- Không biến benchmark Phase 3 thành load test quy mô lớn.
- Không đánh đồng latency của môi trường local với SLA production.
- Không dùng benchmark quá ngẫu nhiên khiến baseline không thể so sánh.


---

## Source: `docs/history/post-mvp/phase-3/37-spec-regression-suite-va-luu-ket-qua.md`

# 37. Spec Regression Suite Và Lưu Kết Quả

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Baseline cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Biến các behavior nhạy cảm nhất thành regression suite có thể chạy lại và xác định cách lưu baseline benchmark ban đầu.

## Phạm vi

- chọn các case nhạy cảm cần khóa thành regression suite
- xác định command hoặc target test cho regression suite
- chọn nơi lưu baseline benchmark đầu tiên trong repo
- mô tả cách cập nhật baseline khi behavior thay đổi có chủ đích

## Deliverable

- regression suite hoặc target test rõ ràng
- danh sách các behavior nhạy cảm đang được khóa
- thư mục hoặc file chứa baseline benchmark ban đầu
- quy tắc cập nhật baseline khi có decision mới

## Baseline cần có

Regression suite tối thiểu nên khóa:

- semantics `insufficient_context`
- citation subset correctness
- semantics `tags = contains-any`
- replace policy theo `document_id` trong cùng `index_name`
- ít nhất một case retrieval/generation tiếng Việt quan trọng

Nơi lưu baseline phải rõ:

- nằm trong repo hoặc đường dẫn được tài liệu hóa rõ
- có format dễ diff và review
- đủ metadata để biết benchmark chạy với config nào

## Acceptance criteria

- Có target regression suite đủ ngắn để chạy trước các thay đổi quan trọng.
- Baseline benchmark ban đầu có nơi lưu và cách đọc rõ ràng.
- Khi behavior thay đổi có chủ đích, team biết phải cập nhật những file nào.
- Regression suite không trùng lặp vô nghĩa với toàn bộ test suite hiện có.

## Verification

- Chạy regression suite và xác nhận các behavior nhạy cảm vẫn ổn.
- Kiểm tra nơi lưu baseline đã tồn tại và format đủ đọc được.
- Review lại quy tắc cập nhật baseline với decision log và docs Phase 3.

## Guardrails

- Không biến regression suite thành bản sao toàn bộ test suite.
- Không cập nhật baseline benchmark lặng lẽ khi chưa có lý do hoặc decision rõ.
- Không lưu kết quả baseline theo format khó diff hoặc phụ thuộc công cụ riêng của cá nhân.


---

## Source: `docs/history/post-mvp/phase-3/38-checklist-phase-3-quality-evaluation.md`

# 38. Checklist Phase 3 Quality Evaluation

## Checklist tổng

- [x] Đã chia Phase 3 thành các workstream nhỏ có thể giao việc.
- [x] Đã khóa Phase 3 là baseline đánh giá chất lượng, không phải feature expansion.
- [x] Đã xác định fixture/golden cases là một workstream riêng.
- [x] Đã xác định benchmark/baseline metrics là một workstream riêng.
- [x] Đã xác định regression suite/result storage là một workstream riêng.

## Checklist fixtures and golden cases

- [x] Có bộ fixture/golden cases sau MVP được khóa.
- [x] Có mapping giữa golden case và behavior cần bảo vệ.
- [x] Có ít nhất một case retrieval match và một case no-match.
- [x] Có ít nhất một case grounded generation và một case `insufficient_context`.

## Checklist benchmark and baseline metrics

- [x] Có command hoặc script benchmark rõ ràng.
- [x] Có baseline retrieval quality.
- [x] Có baseline grounding/citation correctness.
- [x] Có baseline latency `p50/p95`.
- [x] Có ghi chú cách đọc và giới hạn của benchmark.

## Checklist regression suite and result storage

- [x] Có regression suite cho case quan trọng.
- [x] Có nơi lưu baseline benchmark ban đầu.
- [x] Có quy tắc cập nhật baseline khi behavior đổi có chủ đích.
- [x] Có target đủ ngắn để chạy lại trước thay đổi retrieval/generation quan trọng.

## Checklist guardrails

- [x] Không có feature mới chen vào Phase 3.
- [x] Không đổi public API contract.
- [x] Không đổi semantics `insufficient_context`.
- [x] Không đổi semantics `citations`.
- [x] Không đổi semantics `tags = contains-any`.
- [x] Không dùng benchmark ngẫu nhiên khiến baseline không thể so sánh.


---

## Source: `docs/history/post-mvp/phase-3/39-runbook-benchmark-va-regression-baseline.md`

# 39. Runbook Benchmark Và Regression Baseline

## Migration Note

Tài liệu này vẫn đúng về intent benchmark/regression, nhưng một số path bên dưới thuộc trạng thái trước migration package ngày `2026-04-23`.

Ở repo hiện tại:

- golden cases source-of-truth nằm ở `src/tuesday/rag/evaluation/golden_cases.py`
- `src/tuesday_rag/evaluation/golden_cases.py` không còn tồn tại; mọi nhắc đến path này bên dưới là historical reference

## Mục tiêu

Ghi lại cách chạy benchmark Phase 3, cách chạy regression suite, và nơi lưu baseline benchmark đầu tiên.

## Golden cases dùng chung

Phase 3 dùng chung:

- fixture từ `tests/fixtures.py`
- golden cases từ `src/tuesday_rag/evaluation/golden_cases.py`

Các behavior chính đang được khóa:

- retrieval match
- retrieval no-match
- grounded generation với citation hợp lệ
- `insufficient_context`
- semantics re-index
- semantics `tags = contains-any`

## Benchmark command

Command chuẩn:

```bash
python scripts/benchmark_quality.py
```

Command có thể đổi số vòng và output:

```bash
python scripts/benchmark_quality.py --iterations 5 --output benchmarks/phase-3/initial-baseline.json
```

Chỉ số benchmark hiện tại phải có:

- `retrieval_hit_rate`
- `insufficient_context_rate`
- `citation_valid_rate`
- latency `p50/p95` cho `index`, `retrieve`, `generate`

## Regression suite command

Target regression suite:

```bash
pytest tests/regression
```

Regression suite này đủ ngắn để chạy lại trước các thay đổi retrieval/generation quan trọng.

## Nơi lưu baseline

Baseline benchmark đầu tiên được lưu tại:

`benchmarks/phase-3/initial-baseline.json`

Format lưu phải:

- dễ diff
- dễ đọc bằng mắt
- có snapshot config tối thiểu
- có metadata về số iteration và số case

## Khi cập nhật baseline

Chỉ cập nhật baseline khi:

- benchmark script thay đổi có chủ đích
- fixture/golden case thay đổi có chủ đích
- semantics thay đổi đã được chốt bằng decision mới

Không cập nhật baseline lặng lẽ chỉ vì muốn “cho xanh”.


---

## Source: `docs/history/post-mvp/phase-3/README.md`

# Phase 3: Quality Evaluation

## Migration Note

Artefact path trong tài liệu này phản ánh layout trước migration package ngày `2026-04-23`.

Khi đọc ở trạng thái repo hiện tại, path chuẩn cần ưu tiên là:

- `../../../src/tuesday/rag/evaluation/golden_cases.py`
- `../../../scripts/benchmark_quality.py`
- `../../../tests/regression/test_quality_regression.py`

## Mục lục
- Mục tiêu phase
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 3 nhằm khóa baseline định lượng cho chất lượng RAG của bản sau hardening, để mọi thay đổi tiếp theo được so sánh bằng dữ liệu thay vì cảm giác.

Phase này tập trung vào fixture chung, benchmark nhỏ nhưng lặp lại được, regression suite cho các behavior nhạy cảm, và nơi lưu kết quả baseline ban đầu. Phase này không mở rộng public API contract.

## Danh sách spec con

- `34-phase-3-overview.md`
- `35-spec-fixtures-va-golden-cases.md`
- `36-spec-benchmark-va-baseline-metrics.md`
- `37-spec-regression-suite-va-luu-ket-qua.md`
- `38-checklist-phase-3-quality-evaluation.md`

## Artefact triển khai

- `39-runbook-benchmark-va-regression-baseline.md`
- `../../../scripts/benchmark_quality.py`
- `../../../src/tuesday_rag/evaluation/golden_cases.py`
- `../../../tests/regression/test_quality_regression.py`
- `../../../benchmarks/phase-3/initial-baseline.json`

## Thứ tự đọc

1. `34-phase-3-overview.md`
2. `35-spec-fixtures-va-golden-cases.md`
3. `36-spec-benchmark-va-baseline-metrics.md`
4. `37-spec-regression-suite-va-luu-ket-qua.md`
5. `38-checklist-phase-3-quality-evaluation.md`

## Điều kiện done

- Có bộ fixture/golden cases sau MVP được khóa và dùng chung.
- Có benchmark nhỏ nhưng chạy lặp lại được trên cùng quy trình.
- Có baseline tối thiểu cho retrieval quality, grounding/citation correctness và latency.
- Có regression suite cho các case nhạy cảm trước khi bước sang feature expansion.
- Có nơi lưu baseline benchmark ban đầu để so sánh về sau.
- Không đổi public API contract hoặc semantics lõi của MVP nếu chưa có decision mới.


---

## Source: `docs/history/post-mvp/phase-4/42-phase-4-overview.md`

# 42. Phase 4 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa nhịp mở rộng đầu tiên sau Phase 3 theo hướng thực dụng:

- dùng layout capability-oriented hiện tại làm nền chính thức cho thay đổi tiếp theo
- bổ sung giá trị thực cho ingestion mà không mở thêm public endpoint
- giữ nguyên baseline contract, regression và benchmark đã có

## Phạm vi

Phase 4 hiện tại bao gồm 3 workstream:

1. `migration_completion_and_compatibility_cleanup`
2. `internal_file_ingestion_v1`
3. `verification_and_rollout_readiness`

Phạm vi đã hoàn tất trong nhịp này:

- internal file ingestion qua entrypoint nội bộ cho `.txt`, `.md`, `.html`, `.pdf`
- batch ingestion nội bộ cho local directory
- hardening cho batch CLI gồm `--recursive`, `--output`, `--include`, `--exclude`, `--dry-run`
- example assets và runbook đủ để team chạy lại trong local

## Ngoài phạm vi

- endpoint HTTP công khai mới cho upload file
- async ingestion, queue hoặc background orchestration
- recursive sync từ nguồn ngoài hệ thống
- OCR hoặc parse layout phức tạp
- hybrid retrieval, reranker, streaming response, auth/RBAC

## Workstreams

### 1. Migration completion and compatibility cleanup

Rà lại các shim chuyển tiếp còn tồn tại, đặc biệt ở composition root và import graph, để bảo đảm feature mới phát triển trên layout đã migrate thay vì tiếp tục kéo dài trạng thái chuyển tiếp.

### 2. Internal file ingestion v1

Thêm đường vào nội bộ để index file cục bộ hoặc nguồn nội bộ tương đương thông qua `DocumentParser`, giữ public API `/documents/index` ở mode JSON text như hiện tại.

Nhịp thực thi hiện tại đã mở rộng từ scope nhỏ ban đầu sang một bộ ingestion nội bộ thực dụng hơn:

- parser `.txt` và `.md`
- parser `.html` tối giản
- parser `.pdf` qua tool hệ thống
- batch local directory với lọc pattern và dry-run
- normalize metadata ở mức đủ dùng cho retrieval/citation hiện tại
- tái sử dụng semantics `replace-by-document_id-within-index_name` đang có

### 3. Verification and rollout readiness

Bổ sung kiểm chứng đủ để chứng minh nhịp migration + feature đầu tiên không làm regress baseline hiện có, đồng thời đủ tài liệu để team chạy lại trong local/staging.

## Tiêu chí thành công

- Team có một feature expansion đầu tiên đủ nhỏ để ship nhưng đủ thực tế để chứng minh layout mới dùng được.
- `internal file ingestion` chạy qua entrypoint nội bộ mà không làm thay đổi contract của 3 endpoint hiện tại.
- Regression, smoke test và benchmark quan trọng vẫn pass sau nhịp migration + feature này.
- Sau nhịp này, các mở rộng tiếp theo có thể bám trên layout mới mà không cần kéo dài compatibility shim ngoài mức cần thiết.
- Trạng thái hiện tại: các tiêu chí trên đã đạt ở mức đủ để coi nhịp Phase 4 đầu tiên là hoàn tất.


---

## Source: `docs/history/post-mvp/phase-4/43-spec-internal-file-ingestion-v1.md`

# 43. Spec Internal File Ingestion V1

## Mục lục
- Mục tiêu
- Lý do ưu tiên
- Giả định đã khóa
- Phạm vi
- Ngoài phạm vi
- Thiết kế và boundary
- Luồng xử lý
- Acceptance criteria
- Verification
- Rủi ro và cách giảm rủi ro

## Mục tiêu

Bổ sung khả năng index file cục bộ hoặc nguồn nội bộ tương đương cho team vận hành mà không làm thay đổi public API contract của MVP.

Feature này phải đồng thời xác nhận rằng layout capability-oriented hiện tại đã đủ ổn để nhận feature mới đầu tiên mà không cần quay lại cấu trúc cũ.

## Lý do ưu tiên

`internal file ingestion` là bước mở rộng hợp lý nhất ở thời điểm hiện tại vì:

- nó nằm trong danh mục ưu tiên mặc định của Phase 4
- nó tăng giá trị ingestion trực tiếp mà không kéo theo endpoint công khai mới
- nó tận dụng boundary `DocumentParser` đã được thiết kế sẵn nhưng chưa dùng thật
- nó kiểm tra được chất lượng migration tốt hơn một refactor thuần cấu trúc không có feature thật đi kèm

## Giả định đã khóa

- `POST /documents/index` vẫn giữ contract JSON text chuẩn hóa như hiện tại.
- `IngestionUseCase` hiện tại tiếp tục là luồng cho dữ liệu text đã chuẩn hóa.
- `DocumentParser` vẫn là port hạ tầng; object parser/framework-specific không được rò lên application/domain.
- Semantics `replace-by-document_id-within-index_name`, `citations`, `insufficient_context` và `tags = contains-any` không đổi.
- Nhịp `v1` chỉ khóa file text-based đơn giản: `.txt` và `.md`.

## Phạm vi

Feature `v1` bao gồm:

- một entrypoint nội bộ rõ ràng để index file mà không đi qua public HTTP contract
- một use case hoặc orchestration nội bộ riêng cho file ingestion, thay vì nhồi logic parser vào HTTP use case hiện có
- adapter `DocumentParser` cho file `.txt` và `.md`
- normalize metadata tối thiểu từ file path và input nội bộ
- kiểm thử cho parser, orchestration và semantics re-index

Entry point nội bộ được khuyến nghị:

- script hoặc command trong repo, ví dụ `scripts/index_file.py`
- hoặc callable nội bộ tương đương nếu team muốn bọc lại sau

Mục tiêu của entrypoint này là:

- phục vụ local/staging/internal operations
- không trở thành public contract ngầm
- không ép team đưa file upload vào FastAPI trong cùng nhịp

## Ngoài phạm vi

- upload file qua multipart HTTP
- parser `html`, `pdf`, OCR hoặc layout-aware parsing
- index cả thư mục, directory crawling hoặc sync định kỳ
- async ingestion, batch queue hoặc retry orchestration riêng cho batch lớn
- tự động trích metadata nâng cao từ nội dung tài liệu

## Thiết kế và boundary

### 1. Giữ tách biệt giữa public ingestion và internal file ingestion

Luồng HTTP hiện tại tiếp tục xử lý payload text chuẩn hóa. Luồng file nội bộ là một capability path riêng, dùng parser để tạo `SourceDocument`, sau đó đi qua cùng semantics chunking/indexing đã khóa.

Không nên sửa `IngestionUseCase.execute()` hiện tại để nhận cả file path và payload HTTP trong cùng một object mơ hồ. Cách đơn giản hơn là:

- giữ `IngestionUseCase` cho normalized text
- thêm một `FileIngestionUseCase` hoặc orchestration tương đương
- tách phần index `SourceDocument` đã chuẩn hóa thành logic dùng chung mức nhỏ nếu cần

### 2. Parser contract

`DocumentParser` nhận raw input nội bộ và trả `SourceDocument`.

Raw input tối thiểu nên có:

- `path`
- `document_id`
- `index_name`
- `title` tùy chọn
- `metadata` tùy chọn

Rule gợi ý:

- `title` mặc định lấy từ tên file nếu caller không truyền
- `source_uri` mặc định là đường dẫn tuyệt đối hoặc URI file ổn định
- `source_type` được suy ra từ extension nhưng vẫn phải map về tập giá trị domain cho phép
- `metadata.language` và `metadata.tags` nếu caller truyền thì vẫn phải đi qua validation hiện tại

### 3. Migration coupling

Nếu `api.dependencies` hoặc shim chuyển tiếp khác vẫn còn tồn tại, nhịp này được phép giữ tạm trong lúc feature hoàn tất. Tuy nhiên sau khi regression và smoke pass, team nên:

- bỏ shim không còn cần thiết
- dọn import graph để feature mới đi qua `runtime/` và capability packages đúng hướng đã khóa

Không dùng feature này như lý do để mở thêm package hoặc abstraction mới ngoài phạm vi thực cần.

## Luồng xử lý

1. Entry point nội bộ nhận yêu cầu index file với `path`, `document_id`, `index_name` và metadata tùy chọn.
2. Validate `path` tồn tại, là file thường, extension thuộc tập hỗ trợ của `v1`, và caller đã cung cấp các field bắt buộc.
3. `FileIngestionUseCase` gọi `DocumentParser` để đọc file và map thành `SourceDocument`.
4. Sau khi parse xong, orchestration dùng cùng rule validation/chunking/indexing như ingestion hiện tại.
5. `IndexerService` tiếp tục áp dụng policy `replace-by-document_id-within-index_name`.
6. Kết quả trả về phản ánh cùng semantics `DocumentIndexResult`.
7. Failure của parser phải được map về lỗi có kiểm soát như `DOCUMENT_PARSE_ERROR` hoặc `INVALID_INPUT`, không làm lộ stack trace hay chi tiết parser library ra contract nội bộ.

## Acceptance criteria

- Có một đường vào nội bộ rõ ràng để index file `.txt` và `.md`.
- Public API `/documents/index` không đổi request/response schema.
- Cùng một file được index lặp lại với cùng `document_id` và `index_name` vẫn bám policy replace hiện tại.
- `SourceDocument` sinh từ parser có đủ field cần cho chunking, retrieval filter và citation trace hiện tại.
- Parser lỗi, file không tồn tại hoặc extension không hỗ trợ đều trả failure có kiểm soát.
- Regression suite hiện có vẫn pass sau khi thêm feature.
- Feature mới có runbook hoặc command example đủ để team khác chạy lại trong local/staging.

## Verification

- Unit test cho parser `.txt` và `.md`.
- Unit test hoặc use case test cho `FileIngestionUseCase`, bao gồm:
  - file hợp lệ
  - file rỗng sau normalize
  - extension không hỗ trợ
  - re-index cùng `document_id`
- Integration test chứng minh dữ liệu index từ file vẫn truy hồi được qua `/retrieve` và `/generate`.
- Chạy lại smoke test hiện có để xác nhận feature mới không làm hỏng baseline cũ.
- Chạy lại regression suite và benchmark Phase 3 nếu migration cleanup chạm vào import graph hoặc runtime wiring.

## Rủi ro và cách giảm rủi ro

Rủi ro chính:

- parser làm trộn boundary giữa raw file handling và ingestion orchestration
- nhịp feature đầu tiên bị phình sang upload HTTP hoặc parser phức tạp
- migration cleanup kéo dài quá mức và biến thành refactor không có điểm dừng

Cách giảm rủi ro:

- giữ `v1` chỉ hỗ trợ `.txt` và `.md`
- tách use case nội bộ riêng cho file thay vì nhồi nhiều mode vào endpoint hiện có
- dùng lại `DocumentIndexResult` và semantics hiện tại thay vì tạo contract mới
- chỉ bỏ compatibility shim sau khi test nền pass và import graph đã rõ


---

## Source: `docs/history/post-mvp/phase-4/44-checklist-phase-4-feature-expansion.md`

# 44. Checklist Phase 4 Feature Expansion

## Checklist định hướng

- [x] Đã chốt feature đầu tiên của Phase 4 là `internal file ingestion`.
- [x] Đã chốt nhịp đầu không mở endpoint HTTP công khai mới.
- [x] Đã gắn feature đầu tiên với migration docs `40` và `41`.
- [x] Đã mở rộng phạm vi Phase 4 từ `txt/md` ban đầu sang bộ file ingestion nội bộ hoàn chỉnh hơn mà vẫn không đổi public API.

## Checklist migration completion

- [x] Composition root và runtime wiring không còn phụ thuộc shim dài hạn không cần thiết.
- [x] Import graph của feature mới bám đúng `runtime/` và capability packages.
- [x] Không có object parser/framework-specific rò lên application/domain.
- [x] Regression và benchmark quan trọng đã được chạy lại sau cleanup chính.

## Checklist internal file ingestion

- [x] Có entrypoint nội bộ rõ ràng để index file.
- [x] Có parser `.txt`.
- [x] Có parser `.md`.
- [x] Có parser `.html` theo spec mở rộng đã chốt.
- [x] Có parser `.pdf` theo spec mở rộng đã chốt.
- [x] Có batch entrypoint cho local directory.
- [x] Có batch CLI với `--recursive`.
- [x] Có batch CLI với `--output`.
- [x] Có batch CLI với `--include` và `--exclude`.
- [x] Có batch CLI với `--dry-run`.
- [x] Có validation cho file không tồn tại hoặc extension không hỗ trợ.
- [x] Có semantics re-index giống ingestion hiện tại.
- [x] Không đổi contract của `/documents/index`.

## Checklist verification

- [x] Có unit test cho parser và use case nội bộ.
- [x] Có integration test cho luồng `index file -> retrieve -> generate`.
- [x] Smoke test hiện có vẫn pass.
- [x] Regression suite hiện có vẫn pass.
- [x] Runbook hoặc command example đã được cập nhật.

## Điều kiện done của nhịp đầu Phase 4

- [x] Team có thể index file `.txt`, `.md`, `.html`, `.pdf` qua entrypoint nội bộ bằng quy trình được tài liệu hóa.
- [x] Layout capability-oriented hiện tại đủ ổn để tiếp tục phát triển feature tiếp theo mà không cần rollback shim cũ.
- [x] Không có decision mới nào buộc phải đổi public API contract của MVP.
- [x] Phase 4 đã có tài liệu tổng hợp implementation và verification để đóng nhịp đầu tiên.


---

## Source: `docs/history/post-mvp/phase-4/45-runbook-internal-file-ingestion-v1.md`

# 45. Runbook Internal File Ingestion V1

## Mục tiêu

Ghi lại cách chạy entrypoint nội bộ cho file ingestion `v1`, phạm vi file được hỗ trợ, và các bước kiểm tra nhanh sau khi index.

## Phạm vi hỗ trợ

`v1` hiện chỉ hỗ trợ:

- `.txt`
- `.md`
- `.html`
- `.pdf`

Không hỗ trợ trong nhịp này:

- upload qua HTTP
- OCR hoặc parse layout phức tạp

## Command chuẩn

Command cơ bản:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.md \
  --document-id doc-refund-file \
  --index-name enterprise-kb
```

Command có metadata:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.md \
  --document-id doc-refund-file \
  --index-name enterprise-kb \
  --title "Refund policy" \
  --language en \
  --tag refund \
  --tag policy
```

Command với HTML:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.html \
  --document-id doc-refund-html \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

Command với PDF:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.pdf \
  --document-id doc-refund-pdf \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

Batch command cho local directory:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch
```

Batch command có quét nested directory:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch \
  --recursive
```

Batch command có lưu summary ra file:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch \
  --recursive \
  --output /tmp/tuesday-batch-summary.json
```

Batch command có filter pattern:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --recursive \
  --include '*.md' \
  --exclude 'handbook/*'
```

Batch command preview không ghi dữ liệu:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --recursive \
  --include '*.md' \
  --exclude 'handbook/*' \
  --dry-run
```

## Kết quả mong đợi

Entry point in ra JSON theo `DocumentIndexResult`, ví dụ:

```json
{
  "document_id": "doc-refund-file",
  "index_name": "enterprise-kb",
  "chunk_count": 1,
  "indexed_count": 1,
  "status": "indexed",
  "errors": [],
  "replaced_document": false
}
```

Nếu lỗi validation hoặc parse, command trả exit code khác `0` và in error JSON ra `stderr`.

Với batch command:

- in ra summary JSON của toàn batch qua `stdout`
- nếu có `--output`, ghi cùng summary JSON ra file
- trả exit code `0` nếu mọi file thành công
- trả exit code `1` nếu có file lỗi hoặc directory input không hợp lệ
- nếu có `--include` hoặc `--exclude`, pattern được áp trên relative path của file trong directory
- nếu có `--dry-run`, command chỉ preview candidate set và `document_id`, không ghi dữ liệu vào vector store

## Kiểm tra nhanh sau khi index

Sau khi index file, có thể chạy API local rồi gọi:

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H 'content-type: application/json' \
  -d '{
    "query": "How long can customers request a refund?",
    "index_name": "enterprise-kb",
    "filters": {"tags": ["refund"]}
  }'
```

Hoặc dùng smoke/regression hiện có để bảo đảm feature mới không làm hỏng baseline:

```bash
./.venv/bin/python -m pytest tests/smoke/test_index_retrieve_generate.py
./.venv/bin/python -m pytest tests/regression/test_quality_regression.py
```

## Failure cases cần kiểm tra đầu tiên

- file không tồn tại
- `path` không trỏ tới file thường
- extension không hỗ trợ
- file rỗng sau normalize
- metadata không hợp lệ
- directory không tồn tại hoặc không có file hỗ trợ với batch command

## Ghi chú vận hành

- Command này là entrypoint nội bộ, không phải public contract.
- Semantics re-index vẫn bám `replace-by-document_id-within-index_name`.
- Nếu cùng `document_id` và `index_name` được index lại, `replaced_document` phải chuyển thành `true`.
- Với file `.html`, parser nội bộ hiện rút text nền, bỏ `script` và `style`, và ưu tiên lấy `title` từ thẻ `<title>` nếu caller không truyền `--title`.
- Với file `.pdf`, parser nội bộ gọi `pdftotext` của hệ thống; nếu tool thiếu hoặc parse lỗi, command sẽ fail với `DOCUMENT_PARSE_ERROR`.
- Mặc định batch command chỉ quét file thường ngay dưới directory được truyền vào.
- Chỉ khi có `--recursive` thì batch command mới quét nested directory; nếu không có cờ này thì command giữ behavior ở level đầu.
- Với batch pattern filtering, `exclude` thắng cuối cùng nếu một file khớp cả `include` lẫn `exclude`.
- Dry-run không parse nội dung file; nó chỉ phản ánh candidate set sau khi áp extension, recursive và pattern filtering.


---

## Source: `docs/history/post-mvp/phase-4/46-spec-internal-file-ingestion-html-v1.md`

# 46. Spec Internal File Ingestion HTML V1

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Thiết kế parser
- Acceptance criteria
- Verification

## Mục tiêu

Mở rộng `internal file ingestion` hiện tại để hỗ trợ file `.html` theo cách tối giản, không đổi public API contract và không thêm dependency parser nặng.

## Phạm vi

Nhịp này bao gồm:

- parser `.html` trong adapter `DocumentParser` hiện có
- normalize nội dung HTML thành plain text đủ dùng cho chunking, retrieval và generation hiện tại
- giữ `source_type = "html"` cho tài liệu nguồn HTML
- cập nhật entrypoint nội bộ, example file, runbook và test liên quan

## Ngoài phạm vi

- parse layout nâng cao
- giữ cấu trúc bảng, danh sách hoặc semantic HTML giàu định dạng
- tải tài nguyên ngoài file HTML
- xử lý JavaScript render
- thêm endpoint HTTP upload HTML

## Thiết kế parser

Rule parser tối thiểu:

- chỉ nhận file `.html`
- đọc file UTF-8 từ local path như các parser file nội bộ khác
- bỏ qua nội dung trong `script` và `style`
- unescape HTML entities
- chuẩn hóa whitespace về plain text ổn định
- nếu caller không truyền `title`, ưu tiên lấy từ thẻ `<title>`, nếu không có thì fallback sang tên file

Boundary:

- parser chỉ trả `SourceDocument`
- mọi object/parser-specific concern dừng ở infrastructure
- `FileIngestionUseCase` và `IngestionUseCase` không biết chi tiết HTML parsing

## Acceptance criteria

- Có thể index file `.html` qua `scripts/index_file.py`.
- `SourceDocument.source_type` của file `.html` là `html`.
- Nội dung sau parse đủ để retrieval và generation hoạt động trên dữ kiện chính trong HTML.
- Parser vẫn trả lỗi có kiểm soát cho file không tồn tại, không phải file thường, extension không hỗ trợ hoặc UTF-8 lỗi.
- Không đổi contract của `/documents/index`, `/retrieve`, `/generate`.

## Verification

- Unit test cho parser `.html` gồm:
  - lấy `title` từ thẻ `<title>`
  - bỏ `script` và `style`
  - chuẩn hóa text đủ ổn định
- Unit test hoặc CLI test cho `scripts/index_file.py` với file `.html`
- Integration test `index html -> retrieve -> generate`
- Chạy lại smoke/regression suite hiện có


---

## Source: `docs/history/post-mvp/phase-4/47-spec-internal-batch-file-ingestion-v1.md`

# 47. Spec Internal Batch File Ingestion V1

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Hành vi batch
- Acceptance criteria
- Verification

## Mục tiêu

Thêm entrypoint nội bộ để index nhiều file từ một local directory bằng các parser đã hỗ trợ hiện có, không đổi public API contract và không thêm async orchestration.

## Phạm vi

Nhịp này bao gồm:

- script riêng cho batch ingestion từ directory local
- quét file theo extension đã hỗ trợ hiện tại: `.txt`, `.md`, `.html`
- suy ra `document_id` ổn định từ relative path
- summary JSON cho toàn batch
- continue-on-error ở mức từng file

## Ngoài phạm vi

- queue, async worker hoặc background job
- recursive sync từ remote source
- retry policy riêng cho từng file
- public HTTP endpoint cho batch ingestion
- thay đổi `FileIngestionUseCase` hoặc contract HTTP hiện có

## Hành vi batch

Rule tối thiểu:

- nhận `--dir` và `--index-name` là bắt buộc
- chỉ index file thường có extension được hỗ trợ
- nếu không có file phù hợp trong directory, trả lỗi có kiểm soát
- với mỗi file hợp lệ, script gọi lại `file_ingestion_use_case`
- `document_id` mặc định được suy ra từ relative path, gồm cả extension để tránh collision giữa `foo.md` và `foo.html`
- batch không dừng ở file lỗi; thay vào đó ghi lỗi vào summary và tiếp tục file tiếp theo
- exit code là `0` nếu tất cả file index thành công, `1` nếu có bất kỳ lỗi nào hoặc input directory không hợp lệ

Summary JSON tối thiểu cần có:

- `directory`
- `index_name`
- `total_files`
- `indexed_files`
- `failed_files`
- `results`
- `errors`

## Acceptance criteria

- Có thể index toàn bộ file hỗ trợ trong một local directory bằng một command nội bộ.
- Batch summary đủ để biết file nào thành công, file nào lỗi.
- Re-index semantics của từng file vẫn giữ `replace-by-document_id-within-index_name`.
- Unsupported file trong directory không được index nhầm.
- Không đổi contract của `/documents/index`, `/retrieve`, `/generate`.

## Verification

- Unit test cho CLI batch:
  - directory hợp lệ có nhiều file hỗ trợ
  - directory không tồn tại
  - directory không có file hỗ trợ
  - một file lỗi nhưng file khác vẫn tiếp tục index
- Chạy command thật với `examples/`
- Chạy lại smoke/regression suite hiện có


---

## Source: `docs/history/post-mvp/phase-4/48-spec-internal-batch-file-ingestion-recursive-v1.md`

# 48. Spec Internal Batch File Ingestion Recursive V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với cờ `--recursive` để index file hỗ trợ trong cây thư mục local, vẫn không đổi public API contract và không làm thay đổi default behavior của batch command.

## Phạm vi

- thêm cờ `--recursive` cho `scripts/index_directory.py`
- khi cờ không có mặt, command giữ nguyên behavior hiện tại: chỉ quét level đầu
- khi có `--recursive`, command quét toàn bộ subtree
- `document_id` tiếp tục suy ra từ relative path để tránh collision giữa các thư mục con

## Ngoài phạm vi

- include/exclude pattern phức tạp
- depth limit riêng
- symlink traversal policy riêng
- parallel processing hoặc async batch

## Acceptance criteria

- Không có `--recursive`: nested file không bị index.
- Có `--recursive`: nested file hỗ trợ được index.
- `document_id` của nested file phản ánh relative path ổn định.
- Summary JSON vẫn giữ schema hiện tại.
- Continue-on-error vẫn áp dụng theo từng file.

## Verification

- Unit test chứng minh nested file bị bỏ qua khi không có `--recursive`
- Unit test chứng minh nested file được index khi có `--recursive`
- Chạy command thật với `examples/` chứa nested file


---

## Source: `docs/history/post-mvp/phase-4/49-spec-internal-file-ingestion-pdf-v1.md`

# 49. Spec Internal File Ingestion PDF V1

## Mục tiêu

Mở rộng internal file ingestion để hỗ trợ `.pdf` bằng parser hạ tầng tối giản, không đổi public API contract và không thêm dependency Python mới vào repo.

## Phạm vi

- parser `.pdf` trong `DocumentParser` hiện có
- dùng `pdftotext` của hệ thống qua subprocess
- normalize plain text đầu ra đủ dùng cho chunking, retrieval và generation hiện tại
- cập nhật entrypoint nội bộ, example file, runbook và test liên quan

## Ngoài phạm vi

- OCR
- layout-aware parsing
- table extraction
- encrypted PDF hoặc password flow riêng
- public HTTP upload PDF

## Thiết kế parser

Rule tối thiểu:

- chỉ nhận file `.pdf`
- dùng `pdftotext <file> -` để lấy text từ stdout
- nếu `pdftotext` không tồn tại hoặc trả mã lỗi, map về `DOCUMENT_PARSE_ERROR`
- nếu caller không truyền `title`, fallback sang tên file
- `source_type` của tài liệu nguồn là `pdf`

Boundary:

- parser chỉ trả `SourceDocument`
- orchestration không biết gì về subprocess hoặc tool hệ thống
- parser không cố giữ layout PDF phức tạp; chỉ cần plain text đủ ổn định cho behavior hiện tại

## Acceptance criteria

- Có thể index file `.pdf` qua `scripts/index_file.py`.
- `SourceDocument.source_type` của file `.pdf` là `pdf`.
- Nội dung sau parse đủ để retrieval và generation hoạt động trên dữ kiện chính trong PDF đơn giản.
- Nếu `pdftotext` không có hoặc parse lỗi, hệ thống trả `DOCUMENT_PARSE_ERROR`.
- Không đổi contract của `/documents/index`, `/retrieve`, `/generate`.

## Verification

- Unit test parser `.pdf` trên file PDF đơn giản
- Unit test/CLI test cho `scripts/index_file.py` với file `.pdf`
- Integration test `index pdf -> retrieve -> generate`
- Chạy lại smoke/regression suite hiện có


---

## Source: `docs/history/post-mvp/phase-4/50-spec-internal-batch-file-ingestion-output-v1.md`

# 50. Spec Internal Batch File Ingestion Output V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với cờ `--output` để lưu summary JSON ra file, vẫn giữ behavior hiện tại của command trên `stdout`.

## Phạm vi

- thêm `--output <path>` cho `scripts/index_directory.py`
- summary JSON vẫn luôn được in ra `stdout`
- nếu có `--output`, cùng summary đó được ghi ra file
- command tự tạo parent directory của output file nếu cần

## Ngoài phạm vi

- nhiều output format
- append mode hoặc log rotation
- split summary riêng cho success/failure
- upload summary lên remote storage

## Acceptance criteria

- Không có `--output`: command giữ nguyên behavior hiện tại.
- Có `--output`: summary JSON xuất hiện cả ở `stdout` và file.
- Output file chứa đúng cùng payload JSON với `stdout`.
- Parent directory của output file được tạo tự động nếu chưa tồn tại.
- Nếu có file lỗi trong batch, summary vẫn được ghi ra output file.

## Verification

- Unit test cho `--output` ở case success
- Unit test cho `--output` ở case partial failure
- Chạy command thật với `examples/` và một output path trong `/tmp`


---

## Source: `docs/history/post-mvp/phase-4/51-spec-internal-batch-file-ingestion-pattern-filtering-v1.md`

# 51. Spec Internal Batch File Ingestion Pattern Filtering V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với `--include` và `--exclude` để lọc file theo glob pattern trên relative path, vẫn không đổi contract HTTP và không làm phình orchestration.

## Phạm vi

- thêm `--include <pattern>` nhiều lần
- thêm `--exclude <pattern>` nhiều lần
- pattern áp dụng trên relative path POSIX của file bên trong `--dir`
- chỉ lọc trong tập file có extension đã hỗ trợ

## Ngoài phạm vi

- regex đầy đủ
- negation pattern nâng cao
- precedence phức tạp ngoài `exclude` thắng cuối
- filter theo metadata hoặc nội dung file

## Hành vi

- nếu không có `--include`, mặc định coi như include mọi file hỗ trợ
- nếu có `--include`, chỉ giữ file khớp ít nhất một include pattern
- sau đó áp `--exclude`; file khớp bất kỳ exclude pattern nào bị loại
- nếu sau khi lọc không còn file nào, command trả `INVALID_INPUT`
- summary JSON phản ánh `include_patterns` và `exclude_patterns`

## Acceptance criteria

- Có thể chỉ index một subset file bằng `--include`.
- Có thể loại file hoặc subtree bằng `--exclude`.
- `exclude` thắng nếu một file khớp cả include lẫn exclude.
- Pattern hoạt động ổn định với nested path khi dùng cùng `--recursive`.

## Verification

- Unit test cho include only
- Unit test cho exclude only
- Unit test cho include + exclude conflict
- Chạy command thật với `examples/` và pattern đơn giản


---

## Source: `docs/history/post-mvp/phase-4/52-spec-internal-batch-file-ingestion-dry-run-v1.md`

# 52. Spec Internal Batch File Ingestion Dry Run V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với `--dry-run` để preview danh sách file sẽ được index và `document_id` tương ứng, không ghi vào vector store.

## Phạm vi

- thêm `--dry-run` cho `scripts/index_directory.py`
- vẫn áp toàn bộ logic chọn file hiện có: extension hỗ trợ, `--recursive`, `--include`, `--exclude`
- summary JSON phản ánh đây là dry-run và liệt kê candidate files

## Ngoài phạm vi

- preview nội dung parse
- validation parse từng file
- estimation chi phí hoặc latency
- dry-run cho single-file command

## Hành vi

- khi có `--dry-run`, command không gọi `file_ingestion_use_case`
- summary vẫn in ra `stdout`, và nếu có `--output` thì vẫn ghi ra file
- `results` chứa `path`, `document_id`, `index_name`, `status = "dry_run"`
- `indexed_files = 0`, `failed_files = 0`, `planned_files = total_files`
- nếu sau khi lọc không còn file nào, command vẫn trả `INVALID_INPUT` như batch rỗng

## Acceptance criteria

- Dry-run không ghi dữ liệu vào vector store.
- Dry-run vẫn phản ánh đúng candidate set theo recursive/include/exclude.
- Output file nếu có chứa cùng summary dry-run với `stdout`.

## Verification

- Unit test chứng minh dry-run không tạo retrieval result sau khi chạy
- Unit test chứng minh dry-run vẫn tôn trọng recursive/include/exclude
- Chạy command thật với `examples/`


---

## Source: `docs/history/post-mvp/phase-4/53-phase-4-implementation-summary.md`

# 53. Phase 4 Implementation Summary

## Mục tiêu

Chốt lại nhịp đầu tiên của Phase 4 theo trạng thái implementation thật, để team có một điểm dừng rõ trước khi mở nhịp feature tiếp theo.

## Kết quả đã hoàn tất

- bỏ compatibility shim không còn cần thiết ở `api/dependencies.py`
- giữ layout capability-oriented hiện tại làm nền chính thức cho feature mới
- thêm internal file ingestion qua `scripts/index_file.py`
- hỗ trợ parser:
  - `.txt`
  - `.md`
  - `.html`
  - `.pdf` qua `pdftotext`
- thêm batch ingestion qua `scripts/index_directory.py`
- harden batch CLI với:
  - `--recursive`
  - `--output`
  - `--include`
  - `--exclude`
  - `--dry-run`
- thêm example assets trong `examples/`
- cập nhật README và runbook để chạy lại toàn bộ flow nội bộ

## Boundary đã giữ nguyên

- không mở endpoint HTTP công khai mới
- không đổi contract của `/documents/index`, `/retrieve`, `/generate`
- không đổi semantics `insufficient_context`, `citations`, `tags = contains-any`
- không làm rò object parser/tool-specific lên application/domain

## Verification đã có

- unit test cho parser, CLI và use case nội bộ
- integration test cho các luồng:
  - `index md -> retrieve -> generate`
  - `index html -> retrieve -> generate`
  - `index pdf -> retrieve -> generate`
- smoke test hiện có vẫn pass
- regression suite hiện có vẫn pass
- benchmark baseline Phase 3 vẫn chạy lại được sau các nhịp cleanup chính

## Định nghĩa done cho Phase 4 nhịp đầu

Phase 4 được coi là đã done ở nhịp đầu tiên khi:

- feature mở rộng đầu tiên đã ship ở mức nội bộ có kiểm soát
- feature đó có giá trị vận hành thực tế, không chỉ là refactor cấu trúc
- codebase vẫn bám guardrail và public contract cũ
- docs, runbook và checklist đã phản ánh đúng implementation hiện tại

Trạng thái hiện tại: **đã đạt mức done cho nhịp đầu Phase 4**.

## Gợi ý cho nhịp tiếp theo

Các hướng tiếp theo nên được tách sang decision/spec mới thay vì tiếp tục mở rộng lẻ trong cùng nhịp:

- parser nâng cao hơn như OCR hoặc layout-aware PDF
- include/exclude semantics phong phú hơn nếu cần thật
- dry-run hoặc reporting cho single-file command
- feature expansion ngoài ingestion, ví dụ retrieval quality hoặc capability mới


---

## Source: `docs/history/post-mvp/phase-4/README.md`

# Phase 4: Feature Expansion

## Mục lục
- Mục tiêu phase
- Tài liệu nền bắt buộc
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 4 bắt đầu sau khi repo đã có baseline vận hành và baseline chất lượng tối thiểu. Mục tiêu của phase này là mở rộng giá trị của hệ thống một cách có kiểm soát, thay vì thêm feature theo cảm giác.

Ở nhịp đầu tiên, Phase 4 ưu tiên:

- hoàn tất migration capability-oriented theo guardrail đã chốt
- triển khai `internal file ingestion` qua entrypoint nội bộ
- giữ nguyên public HTTP contract của 3 endpoint MVP

## Tài liệu nền bắt buộc

- `../40-spec-quyet-dinh-migration-cau-truc-src.md`
- `../41-spec-target-layout-migration-phase-4.md`

## Danh sách spec con

- `42-phase-4-overview.md`
- `43-spec-internal-file-ingestion-v1.md`
- `44-checklist-phase-4-feature-expansion.md`
- `45-runbook-internal-file-ingestion-v1.md`
- `46-spec-internal-file-ingestion-html-v1.md`
- `47-spec-internal-batch-file-ingestion-v1.md`
- `48-spec-internal-batch-file-ingestion-recursive-v1.md`
- `49-spec-internal-file-ingestion-pdf-v1.md`
- `50-spec-internal-batch-file-ingestion-output-v1.md`
- `51-spec-internal-batch-file-ingestion-pattern-filtering-v1.md`
- `52-spec-internal-batch-file-ingestion-dry-run-v1.md`
- `53-phase-4-implementation-summary.md`

## Thứ tự đọc

1. `../40-spec-quyet-dinh-migration-cau-truc-src.md`
2. `../41-spec-target-layout-migration-phase-4.md`
3. `42-phase-4-overview.md`
4. `43-spec-internal-file-ingestion-v1.md`
5. `44-checklist-phase-4-feature-expansion.md`
6. `45-runbook-internal-file-ingestion-v1.md`
7. `46-spec-internal-file-ingestion-html-v1.md`
8. `47-spec-internal-batch-file-ingestion-v1.md`
9. `48-spec-internal-batch-file-ingestion-recursive-v1.md`
10. `49-spec-internal-file-ingestion-pdf-v1.md`
11. `50-spec-internal-batch-file-ingestion-output-v1.md`
12. `51-spec-internal-batch-file-ingestion-pattern-filtering-v1.md`
13. `52-spec-internal-batch-file-ingestion-dry-run-v1.md`
14. `53-phase-4-implementation-summary.md`

## Điều kiện done

- Feature đầu tiên của Phase 4 đã được chọn và có spec đủ để giao việc.
- Migration hiện tại đủ ổn để feature mới phát triển trên layout đã chốt mà không phải quay lại shim dài hạn.
- Có verification cho migration và feature mới ở mức unit/integration/smoke hoặc regression phù hợp.
- Public contract và semantics lõi của MVP không đổi nếu chưa có decision mới.
- Trạng thái hiện tại: các điều kiện trên đã được đáp ứng cho nhịp Phase 4 đầu tiên.
