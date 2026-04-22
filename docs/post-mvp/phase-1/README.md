# Phase 1: Stabilize

## Mục lục
- Mục tiêu phase
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 1 nhằm biến bản MVP đã đóng scope thành một baseline nội bộ có thể cài đặt, chạy test, chạy API và release lặp lại được mà không phụ thuộc kiến thức ngầm của cá nhân triển khai.

Phase này không thêm feature mới. Nó chuẩn hóa nền phát triển và vận hành tối thiểu để Phase 2 trở đi có thể triển khai trên một baseline ổn định.

## Danh sách spec con

- `22-phase-1-overview.md`
- `23-spec-dev-setup-va-commands.md`
- `24-spec-ci-baseline.md`
- `25-spec-runbook-config-va-release-baseline.md`
- `26-checklist-phase-1-stabilize.md`

## Artefact triển khai

- `../../../README.md`
- `27-runbook-config-va-release-baseline-implementation.md`
- `../../../.github/workflows/ci.yml`

## Thứ tự đọc

1. `22-phase-1-overview.md`
2. `23-spec-dev-setup-va-commands.md`
3. `24-spec-ci-baseline.md`
4. `25-spec-runbook-config-va-release-baseline.md`
5. `26-checklist-phase-1-stabilize.md`

## Điều kiện done

- Có luồng chuẩn để cài dependency dev, chạy lint, chạy test và chạy API local.
- Có automation tối thiểu cho lint và test.
- Có runbook ngắn cho local/staging.
- Có danh sách cấu hình runtime và biến môi trường đang dùng thật sự.
- Không đổi public API contract và không nới scope sang feature mới.
