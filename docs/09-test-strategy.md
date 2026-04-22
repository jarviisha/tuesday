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
