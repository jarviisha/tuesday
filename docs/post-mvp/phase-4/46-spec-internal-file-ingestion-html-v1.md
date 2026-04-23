# 46. Spec Internal File Ingestion HTML V1

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Thiết kế parser
- Acceptance criteria
- Verification

## Mục tiêu

Mở rộng `internal file ingestion` hiện tại để hỗ trợ file `.html` theo cách tối giản, không đổi public API contract và không thêm dependency parser nặng.

## Phạm vi

Nhịp này bao gồm:

- parser `.html` trong adapter `DocumentParser` hiện có
- normalize nội dung HTML thành plain text đủ dùng cho chunking, retrieval và generation hiện tại
- giữ `source_type = "html"` cho tài liệu nguồn HTML
- cập nhật entrypoint nội bộ, example file, runbook và test liên quan

## Ngoài phạm vi

- parse layout nâng cao
- giữ cấu trúc bảng, danh sách hoặc semantic HTML giàu định dạng
- tải tài nguyên ngoài file HTML
- xử lý JavaScript render
- thêm endpoint HTTP upload HTML

## Thiết kế parser

Rule parser tối thiểu:

- chỉ nhận file `.html`
- đọc file UTF-8 từ local path như các parser file nội bộ khác
- bỏ qua nội dung trong `script` và `style`
- unescape HTML entities
- chuẩn hóa whitespace về plain text ổn định
- nếu caller không truyền `title`, ưu tiên lấy từ thẻ `<title>`, nếu không có thì fallback sang tên file

Boundary:

- parser chỉ trả `SourceDocument`
- mọi object/parser-specific concern dừng ở infrastructure
- `FileIngestionUseCase` và `IngestionUseCase` không biết chi tiết HTML parsing

## Acceptance criteria

- Có thể index file `.html` qua `scripts/index_file.py`.
- `SourceDocument.source_type` của file `.html` là `html`.
- Nội dung sau parse đủ để retrieval và generation hoạt động trên dữ kiện chính trong HTML.
- Parser vẫn trả lỗi có kiểm soát cho file không tồn tại, không phải file thường, extension không hỗ trợ hoặc UTF-8 lỗi.
- Không đổi contract của `/documents/index`, `/retrieve`, `/generate`.

## Verification

- Unit test cho parser `.html` gồm:
  - lấy `title` từ thẻ `<title>`
  - bỏ `script` và `style`
  - chuẩn hóa text đủ ổn định
- Unit test hoặc CLI test cho `scripts/index_file.py` với file `.html`
- Integration test `index html -> retrieve -> generate`
- Chạy lại smoke/regression suite hiện có
