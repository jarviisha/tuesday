# 45. Runbook Internal File Ingestion V1

## Mục tiêu

Ghi lại cách chạy entrypoint nội bộ cho file ingestion `v1`, phạm vi file được hỗ trợ, và các bước kiểm tra nhanh sau khi index.

## Phạm vi hỗ trợ

`v1` hiện chỉ hỗ trợ:

- `.txt`
- `.md`
- `.html`
- `.pdf`

Không hỗ trợ trong nhịp này:

- upload qua HTTP
- OCR hoặc parse layout phức tạp

## Command chuẩn

Command cơ bản:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.md \
  --document-id doc-refund-file \
  --index-name enterprise-kb
```

Command có metadata:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.md \
  --document-id doc-refund-file \
  --index-name enterprise-kb \
  --title "Refund policy" \
  --language en \
  --tag refund \
  --tag policy
```

Command với HTML:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.html \
  --document-id doc-refund-html \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

Command với PDF:

```bash
./.venv/bin/python scripts/index_file.py \
  --path ./examples/refund-policy.pdf \
  --document-id doc-refund-pdf \
  --index-name enterprise-kb \
  --language en \
  --tag refund
```

Batch command cho local directory:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch
```

Batch command có quét nested directory:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch \
  --recursive
```

Batch command có lưu summary ra file:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --language en \
  --tag batch \
  --recursive \
  --output /tmp/tuesday-batch-summary.json
```

Batch command có filter pattern:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --index-name enterprise-kb \
  --recursive \
  --include '*.md' \
  --exclude 'handbook/*'
```

Batch command preview không ghi dữ liệu:

```bash
./.venv/bin/python scripts/index_directory.py \
  --dir ./examples \
  --recursive \
  --include '*.md' \
  --exclude 'handbook/*' \
  --dry-run
```

## Kết quả mong đợi

Entry point in ra JSON theo `DocumentIndexResult`, ví dụ:

```json
{
  "document_id": "doc-refund-file",
  "index_name": "enterprise-kb",
  "chunk_count": 1,
  "indexed_count": 1,
  "status": "indexed",
  "errors": [],
  "replaced_document": false
}
```

Nếu lỗi validation hoặc parse, command trả exit code khác `0` và in error JSON ra `stderr`.

Với batch command:

- in ra summary JSON của toàn batch qua `stdout`
- nếu có `--output`, ghi cùng summary JSON ra file
- trả exit code `0` nếu mọi file thành công
- trả exit code `1` nếu có file lỗi hoặc directory input không hợp lệ
- nếu có `--include` hoặc `--exclude`, pattern được áp trên relative path của file trong directory
- nếu có `--dry-run`, command chỉ preview candidate set và `document_id`, không ghi dữ liệu vào vector store

## Kiểm tra nhanh sau khi index

Sau khi index file, có thể chạy API local rồi gọi:

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H 'content-type: application/json' \
  -d '{
    "query": "How long can customers request a refund?",
    "index_name": "enterprise-kb",
    "filters": {"tags": ["refund"]}
  }'
```

Hoặc dùng smoke/regression hiện có để bảo đảm feature mới không làm hỏng baseline:

```bash
./.venv/bin/python -m pytest tests/smoke/test_index_retrieve_generate.py
./.venv/bin/python -m pytest tests/regression/test_quality_regression.py
```

## Failure cases cần kiểm tra đầu tiên

- file không tồn tại
- `path` không trỏ tới file thường
- extension không hỗ trợ
- file rỗng sau normalize
- metadata không hợp lệ
- directory không tồn tại hoặc không có file hỗ trợ với batch command

## Ghi chú vận hành

- Command này là entrypoint nội bộ, không phải public contract.
- Semantics re-index vẫn bám `replace-by-document_id-within-index_name`.
- Nếu cùng `document_id` và `index_name` được index lại, `replaced_document` phải chuyển thành `true`.
- Với file `.html`, parser nội bộ hiện rút text nền, bỏ `script` và `style`, và ưu tiên lấy `title` từ thẻ `<title>` nếu caller không truyền `--title`.
- Với file `.pdf`, parser nội bộ gọi `pdftotext` của hệ thống; nếu tool thiếu hoặc parse lỗi, command sẽ fail với `DOCUMENT_PARSE_ERROR`.
- Mặc định batch command chỉ quét file thường ngay dưới directory được truyền vào.
- Chỉ khi có `--recursive` thì batch command mới quét nested directory; nếu không có cờ này thì command giữ behavior ở level đầu.
- Với batch pattern filtering, `exclude` thắng cuối cùng nếu một file khớp cả `include` lẫn `exclude`.
- Dry-run không parse nội dung file; nó chỉ phản ánh candidate set sau khi áp extension, recursive và pattern filtering.
