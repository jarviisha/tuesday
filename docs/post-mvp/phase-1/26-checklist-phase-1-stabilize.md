# 26. Checklist Phase 1 Stabilize

## Checklist tổng

- [x] Đã chia Phase 1 thành các workstream nhỏ có thể giao việc.
- [x] Đã xác định command chuẩn cho local development.
- [x] Đã xác định automation tối thiểu cho lint/test.
- [x] Đã xác định runbook/config/release baseline là một workstream riêng.

## Checklist dev setup and commands

- [ ] Có hướng dẫn tạo hoặc dùng virtual environment.
- [ ] Có hướng dẫn cài `pip install -e '.[dev]'`.
- [ ] Có command chuẩn `ruff check .`.
- [ ] Có command chuẩn `pytest`.
- [ ] Có ví dụ test target để iterate nhanh.
- [ ] Có command chuẩn chạy API local bằng `uvicorn`.

## Checklist CI baseline

- [ ] Có pipeline lint.
- [ ] Có pipeline test.
- [ ] Pipeline dùng cùng command chuẩn với local.
- [ ] Kết quả fail của lint được phân biệt với fail của test.

## Checklist runbook/config/release baseline

- [ ] Có runbook local/staging ngắn gọn.
- [ ] Có danh sách env vars đang được app đọc.
- [ ] Có mô tả default config và override hợp lệ.
- [ ] Có rà soát logging tối thiểu.
- [ ] Có định nghĩa mốc release nội bộ cho Phase 1.

## Checklist guardrails

- [ ] Không có feature mới chen vào Phase 1.
- [ ] Không đổi public API contract.
- [ ] Không đổi semantics `insufficient_context`.
- [ ] Không đổi semantics `citations`.
- [ ] Không đổi semantics `tags = contains-any`.
