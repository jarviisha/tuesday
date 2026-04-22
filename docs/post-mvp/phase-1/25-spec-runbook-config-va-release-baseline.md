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
