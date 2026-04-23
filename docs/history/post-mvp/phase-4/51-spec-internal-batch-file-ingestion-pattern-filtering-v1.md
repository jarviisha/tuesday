# 51. Spec Internal Batch File Ingestion Pattern Filtering V1

## Mục tiêu

Mở rộng batch ingestion nội bộ với `--include` và `--exclude` để lọc file theo glob pattern trên relative path, vẫn không đổi contract HTTP và không làm phình orchestration.

## Phạm vi

- thêm `--include <pattern>` nhiều lần
- thêm `--exclude <pattern>` nhiều lần
- pattern áp dụng trên relative path POSIX của file bên trong `--dir`
- chỉ lọc trong tập file có extension đã hỗ trợ

## Ngoài phạm vi

- regex đầy đủ
- negation pattern nâng cao
- precedence phức tạp ngoài `exclude` thắng cuối
- filter theo metadata hoặc nội dung file

## Hành vi

- nếu không có `--include`, mặc định coi như include mọi file hỗ trợ
- nếu có `--include`, chỉ giữ file khớp ít nhất một include pattern
- sau đó áp `--exclude`; file khớp bất kỳ exclude pattern nào bị loại
- nếu sau khi lọc không còn file nào, command trả `INVALID_INPUT`
- summary JSON phản ánh `include_patterns` và `exclude_patterns`

## Acceptance criteria

- Có thể chỉ index một subset file bằng `--include`.
- Có thể loại file hoặc subtree bằng `--exclude`.
- `exclude` thắng nếu một file khớp cả include lẫn exclude.
- Pattern hoạt động ổn định với nested path khi dùng cùng `--recursive`.

## Verification

- Unit test cho include only
- Unit test cho exclude only
- Unit test cho include + exclude conflict
- Chạy command thật với `examples/` và pattern đơn giản
