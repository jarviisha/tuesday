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

- Fixture phải deterministic và không phụ thuộc dịch vụ ngoài để khẳng định behavior ở application layer.
- Nội dung mẫu không chứa dữ liệu thật hoặc thông tin nhạy cảm.
- Dùng lại cùng một bộ fixture cho unit test, API contract test và tài liệu ví dụ khi có thể.
- Nếu adapter thật sinh kết quả không hoàn toàn deterministic, golden cases chỉ khóa các phần behavior cần ổn định ở application/API contract.

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
