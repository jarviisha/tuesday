# 28. Phase 2 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa baseline vận hành sau MVP ở mức:

- dữ liệu index không bị mất hoàn toàn chỉ vì restart process
- failure của provider/store không treo request vô thời hạn
- lỗi tích hợp được quan sát và phân loại rõ hơn
- team có một luồng smoke test ngắn cho hành trình chính

## Phạm vi

Phase 2 bao gồm 3 workstream:

1. `persistence_and_runtime_wiring`
2. `integration_resilience_and_error_mapping`
3. `observability_and_smoke_test`

## Ngoài phạm vi

- đổi public API contract hiện tại
- thêm endpoint công khai mới
- thêm feature retrieval mới như hybrid retrieval hoặc reranker
- production deployment hoàn chỉnh
- autoscaling, distributed orchestration hoặc workflow queue đầy đủ
- benchmark chất lượng retrieval/generation theo baseline định lượng

## Workstreams

### 1. Persistence and runtime wiring

Đưa index/storage ra khỏi trạng thái chỉ sống trong memory của process và khóa cách chọn adapter theo môi trường chạy.

### 2. Integration resilience and error mapping

Đảm bảo tích hợp ngoài có timeout tối thiểu, retry ở nơi hợp lý và failure path được map thành behavior quan sát được.

### 3. Observability and smoke test

Bổ sung quan sát tối thiểu cho các luồng chính và khóa một smoke test ngắn cho chuỗi `index -> retrieve -> generate`.

## Tiêu chí thành công

- Team có thể khởi động repo ở chế độ dùng adapter persistence-backed hoặc thành phần bền hơn mà không đổi contract HTTP.
- Khi provider/store lỗi hoặc chậm, request không treo vô thời hạn và log/metric cho biết nhóm lỗi chính.
- Có một smoke test ngắn đủ để phát hiện lỗi wiring giữa ingestion, retrieval và generation.
- Application/domain vẫn chỉ phụ thuộc protocol nội bộ, không bị lộ object framework/provider cụ thể.
