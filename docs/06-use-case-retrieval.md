# 06. Use Case Retrieval

## Mục lục
- Mục tiêu
- Input / output
- Luồng xử lý
- Metadata filtering
- top_k behavior
- Error cases
- Definition of done
- Acceptance criteria
- Test cases mức use case

## Mục tiêu use case retrieval

Nhận truy vấn người dùng, thực hiện truy hồi các chunk liên quan nhất từ chỉ mục theo embedding similarity và bộ lọc metadata.

## Input / output

### Input

`RetrievalRequest`

### Output

`RetrievalResponse`

## Luồng xử lý chi tiết

1. Validate `query`, `top_k`, `index_name`, `filters`.
2. Chuẩn hóa query:
   - trim khoảng trắng
   - loại bỏ trường hợp rỗng
3. Gọi composite service `Retriever`.
4. Bên trong `Retriever`:
   - gọi `EmbeddingProvider` để embed query
   - gọi `VectorStore` để truy hồi theo vector + filter
   - map kết quả sang `RetrievedChunk`
5. Sắp xếp kết quả theo score giảm dần nếu adapter chưa đảm bảo.
6. Trả về `RetrievalResponse`.

## Metadata filtering

MVP hỗ trợ bộ lọc đơn giản theo phép so sánh bằng:

| Trường filter | Kiểu | Ghi chú |
|---|---|---|
| `document_id` | string | Giới hạn theo tài liệu |
| `source_type` | string | Ví dụ `pdf`, `text` |
| `language` | string | Ví dụ `vi`, `en` |
| `tags` | list[string] | Semantics chính thức của MVP là `contains-any` |

Nguyên tắc:

- Chỉ chấp nhận whitelist field đã định nghĩa.
- Filter không hợp lệ phải bị từ chối ở application layer.
- Nếu vector store không hỗ trợ native filter tương ứng, adapter phải fail rõ ràng hoặc degrade có kiểm soát; không được âm thầm bỏ filter.
- `tags` trong MVP dùng semantics `contains-any` và phải được giữ nhất quán giữa fake adapter, adapter thật và test contract.

## top_k behavior

- `top_k` phải > 0.
- `top_k` mặc định do API quy định, ví dụ `5`.
- `top_k` tối đa bị chặn bởi cấu hình hệ thống, ví dụ `20`.
- Nếu số chunk khả dụng nhỏ hơn `top_k`, trả về số thực có sẵn.
- Kết quả phải theo thứ tự score giảm dần.
- `top_k` phải được khóa bằng spec với giá trị mặc định/min/max, nhưng vẫn cho phép override qua config runtime.
- Không áp dụng ngưỡng score cứng ở domain nếu chưa có số liệu hiệu chỉnh cho MVP; việc cắt theo score nên để mở cho phase sau.

## Error cases

| Mã lỗi gợi ý | Tình huống |
|---|---|
| `INVALID_INPUT` | Query rỗng, top_k không hợp lệ, filter sai schema |
| `EMBEDDING_ERROR` | Embed query thất bại |
| `RETRIEVAL_ERROR` | Vector store query lỗi |
| `UNSUPPORTED_FILTER` | Filter không được hỗ trợ |

## Definition of done

- Query hợp lệ được embed và truy hồi thành công.
- Kết quả trả về đúng logical index.
- Áp dụng đúng filter và `top_k`.
- Mọi chunk trả về đều có `chunk_id`, `document_id`, `text`, `score`, `metadata`.

## Acceptance criteria

- Với query hợp lệ, hệ thống trả tối đa `top_k` chunk.
- Nếu có filter `document_id`, chỉ trả chunk thuộc tài liệu đó.
- Nếu không có kết quả, hệ thống trả `chunks = []`, không coi là lỗi hệ thống.
- Nếu filter không hợp lệ, request bị từ chối trước khi gọi adapter.
- Nếu vector store lỗi, hệ thống trả lỗi chuẩn hóa.

## Test cases mức use case

| ID | Kịch bản | Input chính | Kỳ vọng |
|---|---|---|---|
| RET-01 | Retrieval cơ bản | Query hợp lệ, `top_k=3` | Trả tối đa 3 chunk, đúng schema |
| RET-02 | Query rỗng | `"   "` | Lỗi `INVALID_INPUT` |
| RET-03 | `top_k = 0` | Query hợp lệ | Lỗi `INVALID_INPUT` |
| RET-04 | Có filter `document_id` | Query + filter | Chỉ trả chunk thuộc tài liệu chỉ định |
| RET-05 | Filter không whitelist | `filters = {"foo":"bar"}` | Lỗi `UNSUPPORTED_FILTER` hoặc `INVALID_INPUT` |
| RET-06 | Không có kết quả | Query không liên quan | `chunks = []` |
| RET-07 | Embedding provider lỗi | Provider timeout | Lỗi `EMBEDDING_ERROR` |
| RET-08 | Vector store lỗi | Query backend lỗi | Lỗi `RETRIEVAL_ERROR` |
