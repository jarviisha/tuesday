# 22. Phase 1 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa baseline phát triển nội bộ cho bản MVP hiện tại để team có thể:

- setup môi trường theo một cách thống nhất
- chạy lint/test bằng lệnh chuẩn
- khởi động API local mà không phải đoán config
- review và release nội bộ trên cùng một baseline

## Phạm vi

Phase 1 bao gồm 3 workstream:

1. `dev_setup_and_commands`
2. `ci_baseline`
3. `runbook_config_and_release_baseline`

## Ngoài phạm vi

- thay adapter demo bằng adapter thật
- thêm persistence
- thêm metrics mới ngoài observability tối thiểu đã có
- thêm endpoint mới
- tuning retrieval/generation quality
- feature expansion dưới bất kỳ hình thức nào

## Workstreams

### 1. Dev setup and commands

Chuẩn hóa cách cài dependency dev, cách chạy lint/test và cách chạy API local.

### 2. CI baseline

Đảm bảo lint và test không chỉ là quy ước miệng mà đã có automation lặp lại được.

### 3. Runbook, config and release baseline

Khóa tài liệu vận hành tối thiểu cho local/staging, liệt kê env vars đang dùng thật sự và xác định mốc release nội bộ cho bản stabilize.

## Tiêu chí thành công

- Thành viên mới trong team có thể vào repo và làm theo tài liệu để chạy được project.
- Kết quả lint/test không phụ thuộc vào thao tác thủ công không được ghi lại.
- Khi có lỗi cấu hình cơ bản, người vận hành có thể biết phải kiểm tra biến nào và command nào.
- Public contract và semantics lõi của MVP không thay đổi.
