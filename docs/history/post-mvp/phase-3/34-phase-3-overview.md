# 34. Phase 3 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa baseline đánh giá chất lượng sau hardening ở mức:

- team có bộ dữ liệu chung để review, regression và benchmark
- retrieval/generation được đo bằng một bộ chỉ số tối thiểu
- các thay đổi về chunking, retrieval hoặc generation có thể so sánh với mốc ban đầu
- kết quả benchmark đầu tiên được lưu và đọc lại được

## Phạm vi

Phase 3 bao gồm 3 workstream:

1. `fixtures_and_golden_cases`
2. `benchmark_and_baseline_metrics`
3. `regression_suite_and_result_storage`

## Ngoài phạm vi

- tuning production quy mô lớn
- benchmark tải cao hoặc benchmark chi phí chi tiết theo production traffic
- mở rộng feature retrieval mới như hybrid hoặc reranker
- thay đổi contract HTTP để phục vụ benchmarking
- dashboard observability hoàn chỉnh kiểu production BI

## Workstreams

### 1. Fixtures and golden cases

Khóa bộ dữ liệu và kỳ vọng chuẩn để team dùng chung khi review, regression và benchmark.

### 2. Benchmark and baseline metrics

Định nghĩa benchmark nhỏ, deterministic nhất có thể và các chỉ số tối thiểu phải đo.

### 3. Regression suite and result storage

Biến các case quan trọng thành regression suite có thể chạy lại và xác định nơi lưu baseline đầu tiên.

## Tiêu chí thành công

- Một người mới vào repo có thể chạy fixture, benchmark và đọc baseline theo một quy trình rõ.
- Thay đổi về retrieval/generation không còn được đánh giá chỉ bằng demo cảm tính.
- Kết quả benchmark đầu tiên đủ để làm mốc so sánh khi bước sang feature expansion.
- Application/API contract vẫn được giữ ổn định trong suốt Phase 3.
