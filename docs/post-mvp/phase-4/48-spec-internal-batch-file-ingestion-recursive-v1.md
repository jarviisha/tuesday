# 48. Spec Internal Batch File Ingestion Recursive V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với cờ `--recursive` để index file hỗ trợ trong cây thư mục local, vẫn không đổi public API contract và không làm thay đổi default behavior của batch command.

## Phạm vi

- thêm cờ `--recursive` cho `scripts/index_directory.py`
- khi cờ không có mặt, command giữ nguyên behavior hiện tại: chỉ quét level đầu
- khi có `--recursive`, command quét toàn bộ subtree
- `document_id` tiếp tục suy ra từ relative path để tránh collision giữa các thư mục con

## Ngoài phạm vi

- include/exclude pattern phức tạp
- depth limit riêng
- symlink traversal policy riêng
- parallel processing hoặc async batch

## Acceptance criteria

- Không có `--recursive`: nested file không bị index.
- Có `--recursive`: nested file hỗ trợ được index.
- `document_id` của nested file phản ánh relative path ổn định.
- Summary JSON vẫn giữ schema hiện tại.
- Continue-on-error vẫn áp dụng theo từng file.

## Verification

- Unit test chứng minh nested file bị bỏ qua khi không có `--recursive`
- Unit test chứng minh nested file được index khi có `--recursive`
- Chạy command thật với `examples/` chứa nested file
