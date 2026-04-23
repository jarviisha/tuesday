# Phase 4: Feature Expansion

## Mục lục
- Mục tiêu phase
- Tài liệu nền bắt buộc
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 4 bắt đầu sau khi repo đã có baseline vận hành và baseline chất lượng tối thiểu. Mục tiêu của phase này là mở rộng giá trị của hệ thống một cách có kiểm soát, thay vì thêm feature theo cảm giác.

Ở nhịp đầu tiên, Phase 4 ưu tiên:

- hoàn tất migration capability-oriented theo guardrail đã chốt
- triển khai `internal file ingestion` qua entrypoint nội bộ
- giữ nguyên public HTTP contract của 3 endpoint MVP

## Tài liệu nền bắt buộc

- `../40-spec-quyet-dinh-migration-cau-truc-src.md`
- `../41-spec-target-layout-migration-phase-4.md`

## Danh sách spec con

- `42-phase-4-overview.md`
- `43-spec-internal-file-ingestion-v1.md`
- `44-checklist-phase-4-feature-expansion.md`
- `45-runbook-internal-file-ingestion-v1.md`
- `46-spec-internal-file-ingestion-html-v1.md`
- `47-spec-internal-batch-file-ingestion-v1.md`
- `48-spec-internal-batch-file-ingestion-recursive-v1.md`
- `49-spec-internal-file-ingestion-pdf-v1.md`
- `50-spec-internal-batch-file-ingestion-output-v1.md`
- `51-spec-internal-batch-file-ingestion-pattern-filtering-v1.md`
- `52-spec-internal-batch-file-ingestion-dry-run-v1.md`
- `53-phase-4-implementation-summary.md`

## Thứ tự đọc

1. `../40-spec-quyet-dinh-migration-cau-truc-src.md`
2. `../41-spec-target-layout-migration-phase-4.md`
3. `42-phase-4-overview.md`
4. `43-spec-internal-file-ingestion-v1.md`
5. `44-checklist-phase-4-feature-expansion.md`
6. `45-runbook-internal-file-ingestion-v1.md`
7. `46-spec-internal-file-ingestion-html-v1.md`
8. `47-spec-internal-batch-file-ingestion-v1.md`
9. `48-spec-internal-batch-file-ingestion-recursive-v1.md`
10. `49-spec-internal-file-ingestion-pdf-v1.md`
11. `50-spec-internal-batch-file-ingestion-output-v1.md`
12. `51-spec-internal-batch-file-ingestion-pattern-filtering-v1.md`
13. `52-spec-internal-batch-file-ingestion-dry-run-v1.md`
14. `53-phase-4-implementation-summary.md`

## Điều kiện done

- Feature đầu tiên của Phase 4 đã được chọn và có spec đủ để giao việc.
- Migration hiện tại đủ ổn để feature mới phát triển trên layout đã chốt mà không phải quay lại shim dài hạn.
- Có verification cho migration và feature mới ở mức unit/integration/smoke hoặc regression phù hợp.
- Public contract và semantics lõi của MVP không đổi nếu chưa có decision mới.
- Trạng thái hiện tại: các điều kiện trên đã được đáp ứng cho nhịp Phase 4 đầu tiên.
