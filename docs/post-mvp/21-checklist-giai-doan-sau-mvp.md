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
- [ ] Feature đầu tiên sau MVP đã có spec riêng.
- [ ] Feature đầu tiên sau MVP đã nêu rõ lý do ưu tiên.
- [ ] Feature đầu tiên sau MVP có test hoặc benchmark chứng minh giá trị.
- [ ] Feature đầu tiên sau MVP không phá contract hiện tại nếu chưa có decision mới.

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
- [ ] Có quyết định rõ feature nào được làm tiếp theo.
