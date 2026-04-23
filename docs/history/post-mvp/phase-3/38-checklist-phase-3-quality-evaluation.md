# 38. Checklist Phase 3 Quality Evaluation

## Checklist tổng

- [x] Đã chia Phase 3 thành các workstream nhỏ có thể giao việc.
- [x] Đã khóa Phase 3 là baseline đánh giá chất lượng, không phải feature expansion.
- [x] Đã xác định fixture/golden cases là một workstream riêng.
- [x] Đã xác định benchmark/baseline metrics là một workstream riêng.
- [x] Đã xác định regression suite/result storage là một workstream riêng.

## Checklist fixtures and golden cases

- [x] Có bộ fixture/golden cases sau MVP được khóa.
- [x] Có mapping giữa golden case và behavior cần bảo vệ.
- [x] Có ít nhất một case retrieval match và một case no-match.
- [x] Có ít nhất một case grounded generation và một case `insufficient_context`.

## Checklist benchmark and baseline metrics

- [x] Có command hoặc script benchmark rõ ràng.
- [x] Có baseline retrieval quality.
- [x] Có baseline grounding/citation correctness.
- [x] Có baseline latency `p50/p95`.
- [x] Có ghi chú cách đọc và giới hạn của benchmark.

## Checklist regression suite and result storage

- [x] Có regression suite cho case quan trọng.
- [x] Có nơi lưu baseline benchmark ban đầu.
- [x] Có quy tắc cập nhật baseline khi behavior đổi có chủ đích.
- [x] Có target đủ ngắn để chạy lại trước thay đổi retrieval/generation quan trọng.

## Checklist guardrails

- [x] Không có feature mới chen vào Phase 3.
- [x] Không đổi public API contract.
- [x] Không đổi semantics `insufficient_context`.
- [x] Không đổi semantics `citations`.
- [x] Không đổi semantics `tags = contains-any`.
- [x] Không dùng benchmark ngẫu nhiên khiến baseline không thể so sánh.
