# 50. Spec Internal Batch File Ingestion Output V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với cờ `--output` để lưu summary JSON ra file, vẫn giữ behavior hiện tại của command trên `stdout`.

## Phạm vi

- thêm `--output <path>` cho `scripts/index_directory.py`
- summary JSON vẫn luôn được in ra `stdout`
- nếu có `--output`, cùng summary đó được ghi ra file
- command tự tạo parent directory của output file nếu cần

## Ngoài phạm vi

- nhiều output format
- append mode hoặc log rotation
- split summary riêng cho success/failure
- upload summary lên remote storage

## Acceptance criteria

- Không có `--output`: command giữ nguyên behavior hiện tại.
- Có `--output`: summary JSON xuất hiện cả ở `stdout` và file.
- Output file chứa đúng cùng payload JSON với `stdout`.
- Parent directory của output file được tạo tự động nếu chưa tồn tại.
- Nếu có file lỗi trong batch, summary vẫn được ghi ra output file.

## Verification

- Unit test cho `--output` ở case success
- Unit test cho `--output` ở case partial failure
- Chạy command thật với `examples/` và một output path trong `/tmp`
