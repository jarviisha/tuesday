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
