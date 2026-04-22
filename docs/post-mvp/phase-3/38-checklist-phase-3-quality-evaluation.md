# 38. Checklist Phase 3 Quality Evaluation

## Checklist tổng

- [x] Đã chia Phase 3 thành các workstream nhỏ có thể giao việc.
- [x] Đã khóa Phase 3 là baseline đánh giá chất lượng, không phải feature expansion.
- [x] Đã xác định fixture/golden cases là một workstream riêng.
- [x] Đã xác định benchmark/baseline metrics là một workstream riêng.
- [x] Đã xác định regression suite/result storage là một workstream riêng.

## Checklist fixtures and golden cases

- [ ] Có bộ fixture/golden cases sau MVP được khóa.
- [ ] Có mapping giữa golden case và behavior cần bảo vệ.
- [ ] Có ít nhất một case retrieval match và một case no-match.
- [ ] Có ít nhất một case grounded generation và một case `insufficient_context`.

## Checklist benchmark and baseline metrics

- [ ] Có command hoặc script benchmark rõ ràng.
- [ ] Có baseline retrieval quality.
- [ ] Có baseline grounding/citation correctness.
- [ ] Có baseline latency `p50/p95`.
- [ ] Có ghi chú cách đọc và giới hạn của benchmark.

## Checklist regression suite and result storage

- [ ] Có regression suite cho case quan trọng.
- [ ] Có nơi lưu baseline benchmark ban đầu.
- [ ] Có quy tắc cập nhật baseline khi behavior đổi có chủ đích.
- [ ] Có target đủ ngắn để chạy lại trước thay đổi retrieval/generation quan trọng.

## Checklist guardrails

- [ ] Không có feature mới chen vào Phase 3.
- [ ] Không đổi public API contract.
- [ ] Không đổi semantics `insufficient_context`.
- [ ] Không đổi semantics `citations`.
- [ ] Không đổi semantics `tags = contains-any`.
- [ ] Không dùng benchmark ngẫu nhiên khiến baseline không thể so sánh.
