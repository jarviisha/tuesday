# 26. Checklist Phase 1 Stabilize

## Checklist tổng

- [x] Đã chia Phase 1 thành các workstream nhỏ có thể giao việc.
- [x] Đã xác định command chuẩn cho local development.
- [x] Đã xác định automation tối thiểu cho lint/test.
- [x] Đã xác định runbook/config/release baseline là một workstream riêng.

## Checklist dev setup and commands

- [x] Có hướng dẫn tạo hoặc dùng virtual environment.
- [x] Có hướng dẫn cài `pip install -e '.[dev]'`.
- [x] Có command chuẩn `ruff check .`.
- [x] Có command chuẩn `pytest`.
- [x] Có ví dụ test target để iterate nhanh.
- [x] Có command chuẩn chạy API local bằng `uvicorn`.

## Checklist CI baseline

- [x] Có pipeline lint.
- [x] Có pipeline test.
- [x] Pipeline dùng cùng command chuẩn với local.
- [x] Kết quả fail của lint được phân biệt với fail của test.

## Checklist runbook/config/release baseline

- [x] Có runbook local/staging ngắn gọn.
- [x] Có danh sách env vars đang được app đọc.
- [x] Có mô tả default config và override hợp lệ.
- [x] Có rà soát logging tối thiểu.
- [x] Có định nghĩa mốc release nội bộ cho Phase 1.

## Checklist guardrails

- [x] Không có feature mới chen vào Phase 1.
- [x] Không đổi public API contract.
- [x] Không đổi semantics `insufficient_context`.
- [x] Không đổi semantics `citations`.
- [x] Không đổi semantics `tags = contains-any`.
