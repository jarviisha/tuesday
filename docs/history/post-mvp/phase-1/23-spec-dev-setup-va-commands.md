# 23. Spec Dev Setup Và Commands

## Migration Note

Tài liệu này ghi lại command baseline của Phase 1 trước migration package ngày `2026-04-23`.

Ở trạng thái repo hiện tại:

- command chạy API chuẩn là `python -m uvicorn tuesday.api.app:app --reload`
- package source-of-truth là `src/tuesday/`, không còn là `src/tuesday_rag/`
- nếu gặp command hoặc path cũ trong phần nội dung bên dưới, hiểu đó là historical reference

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Commands chuẩn cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Chuẩn hóa luồng phát triển cục bộ để mọi thành viên trong team dùng cùng một tập lệnh và cùng một cách setup cơ bản.

## Phạm vi

- hướng dẫn tạo hoặc dùng virtual environment
- hướng dẫn cài dependency dev
- khóa các lệnh chuẩn cho `lint`, `test`, `test target`, `run api`
- bảo đảm command phản ánh đúng cấu hình hiện có của repo

## Deliverable

- tài liệu hoặc `README` nêu rõ các command chuẩn
- command lint chuẩn cho repo
- command test chuẩn cho repo
- command chạy API local chuẩn cho repo

## Commands chuẩn cần có

Các command sau phải được coi là nguồn sự thật cho Phase 1:

- cài dependency dev:
  - `pip install -e '.[dev]'`
- chạy lint:
  - `ruff check .`
- chạy test toàn bộ:
  - `pytest`
- chạy test mục tiêu:
  - `pytest tests/unit`
  - `pytest tests/api/test_health.py`
- chạy API local:
  - `python -m uvicorn tuesday_rag.api.app:app --reload`

Nếu team muốn dùng wrapper như `make`, `just` hoặc script shell, wrapper đó phải gọi đúng các command nguồn sự thật ở trên hoặc thay thế chúng một cách rõ ràng trong spec.

## Acceptance criteria

- Có một cách setup môi trường dev được mô tả rõ ràng.
- Có một lệnh lint chuẩn và một lệnh test chuẩn được thống nhất.
- Có ví dụ chạy test mục tiêu khi cần iterate nhanh.
- Có một lệnh chuẩn để chạy API local.
- Không yêu cầu công cụ cục bộ ngoài Python/pip trừ khi repo cung cấp hoặc tài liệu hóa rõ.

## Verification

- Thực hiện luồng setup từ đầu trên môi trường sạch.
- Chạy `ruff check .` thành công hoặc ghi rõ failure hiện có cần xử lý.
- Chạy `pytest` thành công hoặc ghi rõ failure hiện có cần xử lý.
- Chạy `python -m uvicorn tuesday_rag.api.app:app --reload` và xác nhận app khởi động được.

## Guardrails

- Không thêm command song song gây mơ hồ kiểu nhiều cách chạy lint/test mà không có command chuẩn.
- Không làm command chuẩn phụ thuộc shell alias cá nhân.
- Không đổi package structure hay public contract chỉ để tiện local setup.
