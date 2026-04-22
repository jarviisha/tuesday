# 21. Checklist Giai Đoạn Sau MVP

## Checklist phase ordering

- [x] Đã chốt thứ tự `stabilize -> operational_hardening -> quality_evaluation -> feature_expansion`.
- [x] Đã xác nhận feature mới không mặc định chen vào trước `stabilize`.
- [x] Đã xác nhận phase sau MVP không tự động mở thêm endpoint công khai.

## Checklist stabilize

- [ ] Có quy trình cài dependency dev rõ ràng.
- [ ] Có lệnh chuẩn để chạy lint.
- [ ] Có lệnh chuẩn để chạy test.
- [ ] Có lệnh chuẩn để chạy API local.
- [ ] Có CI hoặc automation tương đương cho lint + test.
- [ ] Có runbook local/staging ngắn gọn.

## Checklist operational hardening

- [ ] Dữ liệu index không còn phụ thuộc hoàn toàn vào memory của process.
- [ ] Tích hợp ngoài có timeout tối thiểu.
- [ ] Tích hợp ngoài có retry ở nơi phù hợp.
- [ ] Error mapping cho failure path đã được rà lại.
- [ ] Có smoke test cho luồng `index -> retrieve -> generate`.
- [ ] Logging/metrics đủ để phân biệt nhóm lỗi chính.

## Checklist quality evaluation

- [ ] Có bộ fixture/golden cases sau MVP.
- [ ] Có baseline retrieval quality.
- [ ] Có baseline cho grounding/citation correctness.
- [ ] Có baseline latency `p50/p95`.
- [ ] Có regression suite cho case quan trọng.
- [ ] Có nơi lưu kết quả benchmark ban đầu.

## Checklist feature expansion

- [ ] Feature đầu tiên sau MVP đã có spec riêng.
- [ ] Feature đầu tiên sau MVP đã nêu rõ lý do ưu tiên.
- [ ] Feature đầu tiên sau MVP có test hoặc benchmark chứng minh giá trị.
- [ ] Feature đầu tiên sau MVP không phá contract hiện tại nếu chưa có decision mới.

## Checklist boundary và guardrails

- [ ] Không có object provider/store/framework rò rỉ lên application/domain.
- [ ] Không đổi semantics `insufficient_context`.
- [ ] Không đổi semantics `citations`.
- [ ] Không đổi semantics `tags = contains-any`.
- [ ] Không log raw content ngoài mức tối thiểu cần thiết.

## Kết luận vào phase mở rộng

- [ ] `stabilize` đã đạt mức done.
- [ ] `operational_hardening` đã đạt mức done tối thiểu.
- [ ] `quality_evaluation` đã có baseline đủ dùng.
- [ ] Có quyết định rõ feature nào được làm tiếp theo.
