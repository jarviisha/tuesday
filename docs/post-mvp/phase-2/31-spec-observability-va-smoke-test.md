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
