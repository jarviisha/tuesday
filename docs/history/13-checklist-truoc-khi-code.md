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
