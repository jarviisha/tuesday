# 32. Checklist Phase 2 Operational Hardening

## Checklist tổng

- [x] Đã chia Phase 2 thành các workstream nhỏ có thể giao việc.
- [x] Đã khóa boundary Phase 2 không mở rộng public API contract.
- [x] Đã xác định persistence/runtime wiring là một workstream riêng.
- [x] Đã xác định resilience/error mapping là một workstream riêng.
- [x] Đã xác định observability/smoke test là một workstream riêng.

## Checklist persistence and runtime wiring

- [ ] Có storage/index adapter không còn phụ thuộc hoàn toàn vào memory của process.
- [ ] Có runtime wiring rõ ràng để chọn adapter theo môi trường.
- [ ] Có tài liệu config local/staging cho adapter persistence-backed.
- [ ] Có integration test cho storage mới.
- [ ] Có kiểm chứng `replace-by-document_id-within-index_name` trên storage mới.

## Checklist integration resilience and error mapping

- [ ] Có timeout tối thiểu cho tích hợp ngoài.
- [ ] Có retry ở nơi phù hợp với failure tạm thời.
- [ ] Có giới hạn retry rõ ràng.
- [ ] Có rà soát error mapping cho failure path chính.
- [ ] Có test hoặc sandbox check cho ít nhất một failure path timeout hoặc retry.

## Checklist observability and smoke test

- [ ] Có định nghĩa nhóm lỗi chính cần phân biệt.
- [ ] Có logging hoặc metrics đủ để phân biệt lỗi ứng dụng, storage, provider.
- [ ] Có smoke test `index -> retrieve -> generate`.
- [ ] Có command hoặc script rõ ràng để chạy smoke test.
- [ ] Có runbook ngắn cho việc đọc tín hiệu khi smoke test fail.

## Checklist guardrails

- [ ] Không có feature mới chen vào Phase 2.
- [ ] Không đổi public API contract.
- [ ] Không đổi semantics `insufficient_context`.
- [ ] Không đổi semantics `citations`.
- [ ] Không đổi semantics `tags = contains-any`.
- [ ] Không log raw content ngoài mức tối thiểu cần thiết.
