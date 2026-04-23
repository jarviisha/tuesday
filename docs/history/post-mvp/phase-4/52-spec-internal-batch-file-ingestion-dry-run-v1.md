# 52. Spec Internal Batch File Ingestion Dry Run V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với `--dry-run` để preview danh sách file sẽ được index và `document_id` tương ứng, không ghi vào vector store.

## Phạm vi

- thêm `--dry-run` cho `scripts/index_directory.py`
- vẫn áp toàn bộ logic chọn file hiện có: extension hỗ trợ, `--recursive`, `--include`, `--exclude`
- summary JSON phản ánh đây là dry-run và liệt kê candidate files

## Ngoài phạm vi

- preview nội dung parse
- validation parse từng file
- estimation chi phí hoặc latency
- dry-run cho single-file command

## Hành vi

- khi có `--dry-run`, command không gọi `file_ingestion_use_case`
- summary vẫn in ra `stdout`, và nếu có `--output` thì vẫn ghi ra file
- `results` chứa `path`, `document_id`, `index_name`, `status = "dry_run"`
- `indexed_files = 0`, `failed_files = 0`, `planned_files = total_files`
- nếu sau khi lọc không còn file nào, command vẫn trả `INVALID_INPUT` như batch rỗng

## Acceptance criteria

- Dry-run không ghi dữ liệu vào vector store.
- Dry-run vẫn phản ánh đúng candidate set theo recursive/include/exclude.
- Output file nếu có chứa cùng summary dry-run với `stdout`.

## Verification

- Unit test chứng minh dry-run không tạo retrieval result sau khi chạy
- Unit test chứng minh dry-run vẫn tôn trọng recursive/include/exclude
- Chạy command thật với `examples/`
