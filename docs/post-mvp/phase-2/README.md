# Phase 2: Operational Hardening

## Mục lục
- Mục tiêu phase
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 2 nhằm đưa baseline Phase 1 sang mức vận hành cứng cáp hơn trước khi bắt đầu đo benchmark chất lượng hoặc mở rộng feature.

Phase này tập trung vào độ bền vận hành, khả năng quan sát và failure handling khi thay thành phần demo bằng thành phần bền hơn. Phase này không mở rộng public API contract.

## Danh sách spec con

- `28-phase-2-overview.md`
- `29-spec-persistence-va-runtime-wiring.md`
- `30-spec-integration-resilience-va-error-mapping.md`
- `31-spec-observability-va-smoke-test.md`
- `32-checklist-phase-2-operational-hardening.md`

## Thứ tự đọc

1. `28-phase-2-overview.md`
2. `29-spec-persistence-va-runtime-wiring.md`
3. `30-spec-integration-resilience-va-error-mapping.md`
4. `31-spec-observability-va-smoke-test.md`
5. `32-checklist-phase-2-operational-hardening.md`

## Điều kiện done

- Có storage/index adapter không còn phụ thuộc hoàn toàn vào memory của process.
- Có runtime wiring rõ ràng để bật persistence hoặc adapter bền hơn theo môi trường.
- Tích hợp ngoài có timeout tối thiểu, retry ở nơi phù hợp và error mapping có thể quan sát được.
- Có smoke test cho luồng `index -> retrieve -> generate`.
- Logging hoặc metrics đủ để phân biệt tối thiểu nhóm lỗi ứng dụng, provider và storage.
- Không đổi public API contract hoặc semantics lõi của MVP nếu chưa có decision mới.
