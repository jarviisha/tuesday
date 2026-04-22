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
