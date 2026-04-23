# 49. Spec Internal File Ingestion PDF V1

## Mục tiêu

Mở rộng internal file ingestion để hỗ trợ `.pdf` bằng parser hạ tầng tối giản, không đổi public API contract và không thêm dependency Python mới vào repo.

## Phạm vi

- parser `.pdf` trong `DocumentParser` hiện có
- dùng `pdftotext` của hệ thống qua subprocess
- normalize plain text đầu ra đủ dùng cho chunking, retrieval và generation hiện tại
- cập nhật entrypoint nội bộ, example file, runbook và test liên quan

## Ngoài phạm vi

- OCR
- layout-aware parsing
- table extraction
- encrypted PDF hoặc password flow riêng
- public HTTP upload PDF

## Thiết kế parser

Rule tối thiểu:

- chỉ nhận file `.pdf`
- dùng `pdftotext <file> -` để lấy text từ stdout
- nếu `pdftotext` không tồn tại hoặc trả mã lỗi, map về `DOCUMENT_PARSE_ERROR`
- nếu caller không truyền `title`, fallback sang tên file
- `source_type` của tài liệu nguồn là `pdf`

Boundary:

- parser chỉ trả `SourceDocument`
- orchestration không biết gì về subprocess hoặc tool hệ thống
- parser không cố giữ layout PDF phức tạp; chỉ cần plain text đủ ổn định cho behavior hiện tại

## Acceptance criteria

- Có thể index file `.pdf` qua `scripts/index_file.py`.
- `SourceDocument.source_type` của file `.pdf` là `pdf`.
- Nội dung sau parse đủ để retrieval và generation hoạt động trên dữ kiện chính trong PDF đơn giản.
- Nếu `pdftotext` không có hoặc parse lỗi, hệ thống trả `DOCUMENT_PARSE_ERROR`.
- Không đổi contract của `/documents/index`, `/retrieve`, `/generate`.

## Verification

- Unit test parser `.pdf` trên file PDF đơn giản
- Unit test/CLI test cho `scripts/index_file.py` với file `.pdf`
- Integration test `index pdf -> retrieve -> generate`
- Chạy lại smoke/regression suite hiện có
