# 24. Spec CI Baseline

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Pipeline tối thiểu
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Thiết lập automation tối thiểu để lint và test được chạy lặp lại theo cùng một baseline, giảm lệ thuộc vào kiểm tra thủ công trước merge hoặc release nội bộ.

## Phạm vi

- chọn một cơ chế automation phù hợp với repo
- chạy lint trên codebase
- chạy test trên codebase
- bảo đảm automation dùng cùng command đã khóa ở workstream dev setup

## Deliverable

- một pipeline CI hoặc automation tương đương trong repo
- job lint
- job test
- tài liệu ngắn giải thích khi nào pipeline được coi là pass/fail

## Pipeline tối thiểu

Pipeline tối thiểu của Phase 1 phải gồm:

1. checkout source
2. setup Python phiên bản phù hợp với `pyproject.toml`
3. cài dependency dev
4. chạy `ruff check .`
5. chạy `pytest`

Có thể tách `lint` và `test` thành hai job riêng nếu phù hợp với nền CI được chọn.

## Acceptance criteria

- Automation chạy được từ repo mà không cần thao tác tay không được tài liệu hóa.
- Automation dùng đúng command chuẩn của repo.
- Lint và test được tách bạch đủ để biết lỗi đang nằm ở đâu.
- Kết quả pass/fail đủ rõ để dùng làm baseline review nội bộ.

## Verification

- Chạy pipeline trên một branch hoặc môi trường test.
- Xác nhận lỗi lint làm fail pipeline.
- Xác nhận lỗi test làm fail pipeline.
- Xác nhận khi code ổn thì pipeline pass trọn vẹn.

## Guardrails

- Không nhét thêm kiểm tra ngoài phạm vi Phase 1 như benchmark, deploy production hay e2e phức tạp.
- Không để CI chạy command khác với command local đã khóa mà không có lý do rõ ràng.
- Không coi cảnh báo không fail là đủ cho baseline lint/test của Phase 1.
