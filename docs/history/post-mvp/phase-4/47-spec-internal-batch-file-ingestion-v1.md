# 47. Spec Internal Batch File Ingestion V1

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Hành vi batch
- Acceptance criteria
- Verification

## Mục tiêu

Thêm entrypoint nội bộ để index nhiều file từ một local directory bằng các parser đã hỗ trợ hiện có, không đổi public API contract và không thêm async orchestration.

## Phạm vi

Nhịp này bao gồm:

- script riêng cho batch ingestion từ directory local
- quét file theo extension đã hỗ trợ hiện tại: `.txt`, `.md`, `.html`
- suy ra `document_id` ổn định từ relative path
- summary JSON cho toàn batch
- continue-on-error ở mức từng file

## Ngoài phạm vi

- queue, async worker hoặc background job
- recursive sync từ remote source
- retry policy riêng cho từng file
- public HTTP endpoint cho batch ingestion
- thay đổi `FileIngestionUseCase` hoặc contract HTTP hiện có

## Hành vi batch

Rule tối thiểu:

- nhận `--dir` và `--index-name` là bắt buộc
- chỉ index file thường có extension được hỗ trợ
- nếu không có file phù hợp trong directory, trả lỗi có kiểm soát
- với mỗi file hợp lệ, script gọi lại `file_ingestion_use_case`
- `document_id` mặc định được suy ra từ relative path, gồm cả extension để tránh collision giữa `foo.md` và `foo.html`
- batch không dừng ở file lỗi; thay vào đó ghi lỗi vào summary và tiếp tục file tiếp theo
- exit code là `0` nếu tất cả file index thành công, `1` nếu có bất kỳ lỗi nào hoặc input directory không hợp lệ

Summary JSON tối thiểu cần có:

- `directory`
- `index_name`
- `total_files`
- `indexed_files`
- `failed_files`
- `results`
- `errors`

## Acceptance criteria

- Có thể index toàn bộ file hỗ trợ trong một local directory bằng một command nội bộ.
- Batch summary đủ để biết file nào thành công, file nào lỗi.
- Re-index semantics của từng file vẫn giữ `replace-by-document_id-within-index_name`.
- Unsupported file trong directory không được index nhầm.
- Không đổi contract của `/documents/index`, `/retrieve`, `/generate`.

## Verification

- Unit test cho CLI batch:
  - directory hợp lệ có nhiều file hỗ trợ
  - directory không tồn tại
  - directory không có file hỗ trợ
  - một file lỗi nhưng file khác vẫn tiếp tục index
- Chạy command thật với `examples/`
- Chạy lại smoke/regression suite hiện có
