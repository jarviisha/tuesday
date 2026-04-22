# 36. Spec Benchmark Và Baseline Metrics

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Chỉ số tối thiểu
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Định nghĩa benchmark nhỏ nhưng lặp lại được để đo retrieval quality, grounding/citation correctness và latency cơ bản.

## Phạm vi

- chọn command hoặc script benchmark chuẩn cho repo
- xác định cách chạy benchmark trên bộ fixture đã khóa
- đo các chỉ số tối thiểu của Phase 3
- chốt format kết quả baseline đầu tiên

## Deliverable

- command hoặc script benchmark chuẩn
- mô tả cách benchmark dùng fixture nào và chạy trong điều kiện nào
- kết quả baseline đầu tiên theo format đọc được
- ghi chú cách diễn giải kết quả và giới hạn của benchmark

## Chỉ số tối thiểu

Phase 3 tối thiểu phải đo:

- retrieval hit rate trên bộ fixture đã khóa
- tỷ lệ `insufficient_context`
- tỷ lệ citation hợp lệ theo rule `citations subset of used_chunks`
- latency `p50` và `p95` cho `index`, `retrieve`, `generate`
- nếu có lỗi, phân nhóm lỗi ở mức đủ đọc được

Nếu provider thật tạo biến thiên, benchmark phải phân biệt:

- chỉ số deterministic ở application/API
- chỉ số có thể biến thiên do provider hoặc timing môi trường

## Acceptance criteria

- Có thể chạy lại benchmark bằng cùng command hoặc script.
- Benchmark cho kết quả đủ ổn định để so sánh các thay đổi quan trọng.
- Kết quả baseline đầu tiên được đọc được mà không cần suy luận từ log thô.
- Benchmark không đòi hỏi hạ tầng production để chạy.

## Verification

- Chạy benchmark ít nhất một lần trên bộ fixture đã khóa.
- Lưu kết quả theo format mà team có thể review.
- Đối chiếu chỉ số benchmark với semantics và contract hiện tại.

## Guardrails

- Không biến benchmark Phase 3 thành load test quy mô lớn.
- Không đánh đồng latency của môi trường local với SLA production.
- Không dùng benchmark quá ngẫu nhiên khiến baseline không thể so sánh.
