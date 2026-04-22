# 08. API Contract

## Mục lục
- Danh sách endpoint MVP
- Request/response schema
- Validation rules
- Error response
- Ví dụ request/response

## Danh sách endpoint MVP

| Method | Endpoint | Mục đích |
|---|---|---|
| `POST` | `/documents/index` | Ingestion và index tài liệu |
| `POST` | `/retrieve` | Truy hồi context |
| `POST` | `/generate` | Sinh câu trả lời grounded |

## Nguyên tắc chung

- Content-Type: `application/json`
- Tất cả response thành công trả JSON.
- Lỗi nghiệp vụ và lỗi hạ tầng được chuẩn hóa cùng một envelope.
- `chunk_id` là định danh citation chuẩn xuyên suốt API.
- Các giới hạn input được khóa trong spec với default + min/max cho MVP, nhưng cho phép override bằng config runtime.
- Config runtime được nạp khi khởi động ứng dụng và áp dụng thống nhất cho mọi request trong cùng một phiên bản deploy.

## POST /documents/index

### Request schema

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | ID tài liệu |
| `title` | string | Không | Tiêu đề |
| `content` | string | Có | Nội dung văn bản đã chuẩn hóa cho public API MVP |
| `source_type` | string | Có | Loại nguồn |
| `source_uri` | string | Không | URI nguồn |
| `metadata` | object | Không | Metadata tài liệu |
| `index_name` | string | Có | Logical index |

### Response schema

| Trường | Kiểu | Mô tả |
|---|---|---|
| `document_id` | string | ID tài liệu |
| `index_name` | string | Logical index |
| `chunk_count` | int | Số chunk đã tạo |
| `indexed_count` | int | Số chunk đã index |
| `status` | string | `indexed`, `partial`, `failed` |
| `errors` | list[string] | Danh sách lỗi |
| `replaced_document` | bool | Có thay thế dữ liệu cũ của cùng `document_id` trong `index_name` hay không |

### Validation rules

- `document_id`, `content`, `source_type`, `index_name` là bắt buộc.
- `content` không được rỗng sau trim.
- `metadata` phải là JSON object hợp lệ.
- `source_type` phải thuộc tập giá trị cho phép của MVP.
- `document_id`: mặc định `1..128` ký tự.
- `index_name`: mặc định `1..64` ký tự.
- `content`: mặc định `1..100000` ký tự.

### Ví dụ request

```json
{
  "document_id": "doc-001",
  "title": "Chính sách hoàn tiền",
  "content": "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày...",
  "source_type": "text",
  "source_uri": "internal://policy/refund",
  "metadata": {
    "language": "vi",
    "tags": ["policy", "refund"]
  },
  "index_name": "enterprise-kb"
}
```

### Ví dụ response

```json
{
  "document_id": "doc-001",
  "index_name": "enterprise-kb",
  "chunk_count": 3,
  "indexed_count": 3,
  "status": "indexed",
  "errors": [],
  "replaced_document": false
}
```

## POST /retrieve

### Request schema

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Có | Truy vấn người dùng |
| `top_k` | int | Không | Mặc định `5` |
| `filters` | object | Không | Bộ lọc metadata |
| `index_name` | string | Có | Logical index |

### Response schema

| Trường | Kiểu | Mô tả |
|---|---|---|
| `query` | string | Truy vấn gốc |
| `top_k` | int | Giá trị đã áp dụng |
| `index_name` | string | Logical index |
| `applied_filters` | object | Filter đã áp dụng |
| `chunks` | array | Danh sách chunk truy hồi |

Schema cho từng phần tử `chunks`:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `chunk_id` | string | ID chunk |
| `document_id` | string | ID tài liệu |
| `text` | string | Nội dung chunk |
| `score` | float | Điểm liên quan |
| `metadata` | object | Metadata chunk |

### Validation rules

- `query` không được rỗng sau trim.
- `query`: mặc định `1..2000` ký tự.
- `top_k`: mặc định `5`, min `1`, max `20`.
- `filters` chỉ nhận các khóa whitelist:
  - `document_id`
  - `source_type`
  - `language`
  - `tags`
- `filters.tags` dùng semantics `contains-any`.

### Ví dụ request

```json
{
  "query": "Khách hàng được hoàn tiền trong bao lâu?",
  "top_k": 3,
  "filters": {
    "language": "vi",
    "tags": ["refund"]
  },
  "index_name": "enterprise-kb"
}
```

### Ví dụ response

```json
{
  "query": "Khách hàng được hoàn tiền trong bao lâu?",
  "top_k": 3,
  "index_name": "enterprise-kb",
  "applied_filters": {
    "language": "vi",
    "tags": ["refund"]
  },
  "chunks": [
    {
      "chunk_id": "chunk-doc-001-0001",
      "document_id": "doc-001",
      "text": "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán.",
      "score": 0.92,
      "metadata": {
        "document_id": "doc-001",
        "chunk_id": "chunk-doc-001-0001",
        "title": "Chính sách hoàn tiền",
        "source_type": "text",
        "source_uri": "internal://policy/refund",
        "sequence_no": 1,
        "language": "vi",
        "tags": ["policy", "refund"]
      }
    }
  ]
}
```

## POST /generate

### Request schema

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `question` | string | Có | Câu hỏi người dùng |
| `index_name` | string | Không | Dùng khi cần retrieval nội bộ |
| `retrieval_request` | object | Không | Cấu hình retrieval nếu hệ thống tự retrieval |
| `retrieved_chunks` | array | Không | Context có sẵn |
| `max_context_chunks` | int | Không | Giới hạn chunk đưa vào prompt |

Quy tắc:

- Phải có ít nhất một trong hai:
  - `retrieval_request`
  - `retrieved_chunks`

Schema cho `retrieval_request`:

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Không | Nếu bỏ trống thì mặc định dùng `question` làm query retrieval |
| `top_k` | int | Không | Mặc định `5` |
| `filters` | object | Không | Filter metadata |
| `index_name` | string | Không | Cho phép override nếu muốn chỉ rõ logical index ở nhánh retrieval |

Quy tắc mapping sang domain:

- Ở application layer, `retrieval_request` của API phải được map thành `RetrievalRequest`.
- Nếu `retrieval_request.query` bị bỏ trống thì application phải gán `query = question` trước khi gọi use case retrieval.

Schema cho từng phần tử `retrieved_chunks` giống response của `/retrieve`.

### Response schema

| Trường | Kiểu | Mô tả |
|---|---|---|
| `answer` | string | Câu trả lời cuối cùng |
| `citations` | list[string] | Danh sách `chunk_id` |
| `grounded` | bool | Có bám context hay không |
| `insufficient_context` | bool | Có thiếu dữ liệu hay không |
| `used_chunks` | array | Danh sách chunk đã dùng |

Quy tắc response:

- `citations` phải là tập con của `used_chunks[].chunk_id`.
- Nếu `used_chunks` rỗng thì `citations` phải rỗng.
- Khi `insufficient_context = true`, `grounded` phải là `false`.
- Khi `insufficient_context = true`, `answer` dùng literal mặc định của MVP:
  - `Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn.`
- Literal trên có thể override bằng config runtime, nhưng phải giữ nguyên semantics và schema response.

### Validation rules

- `question` không được rỗng.
- `question`: mặc định `1..2000` ký tự.
- `max_context_chunks`: mặc định `5`, min `1`, max `10`.
- Nếu có `retrieved_chunks`, mỗi chunk phải đủ:
  - `chunk_id`
  - `document_id`
  - `text`
  - `metadata`
- Nếu có `retrieval_request`, `index_name` phải xác định được từ `retrieval_request.index_name` hoặc từ field `index_name` ở request ngoài.
- Nếu `retrieved_chunks` là mảng rỗng, request vẫn hợp lệ và hệ thống phải trả lời theo nhánh `insufficient_context`.
- Public API MVP chưa khóa contract upload file; ingestion qua HTTP hiện dùng JSON text đơn giản.

### Ví dụ request

```json
{
  "question": "Khách hàng được hoàn tiền trong bao lâu?",
  "index_name": "enterprise-kb",
  "retrieval_request": {
    "top_k": 3,
    "filters": {
      "language": "vi"
    }
  },
  "max_context_chunks": 3
}
```

### Ví dụ response

```json
{
  "answer": "Theo tài liệu hiện có, khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán. [chunk-doc-001-0001]",
  "citations": ["chunk-doc-001-0001"],
  "grounded": true,
  "insufficient_context": false,
  "used_chunks": [
    {
      "chunk_id": "chunk-doc-001-0001",
      "document_id": "doc-001",
      "text": "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán.",
      "score": 0.92,
      "metadata": {
        "document_id": "doc-001",
        "chunk_id": "chunk-doc-001-0001",
        "title": "Chính sách hoàn tiền",
        "source_type": "text",
        "source_uri": "internal://policy/refund",
        "sequence_no": 1,
        "language": "vi",
        "tags": ["policy", "refund"]
      }
    }
  ]
}
```

## Error response

Schema lỗi chuẩn:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `error_code` | string | Mã lỗi chuẩn hóa |
| `message` | string | Mô tả ngắn |
| `details` | object | Chi tiết có kiểm soát |

### HTTP error mapping MVP

| `error_code` | HTTP status | Ghi chú |
|---|---|---|
| `INVALID_INPUT` | `400` | Lỗi validate request hoặc rule đầu vào |
| `UNSUPPORTED_FILTER` | `400` | Filter ngoài whitelist hoặc adapter không hỗ trợ theo spec |
| `DOCUMENT_PARSE_ERROR` | `422` | Input parse thất bại |
| `EMPTY_DOCUMENT` | `422` | Nội dung rỗng sau chuẩn hóa |
| `CHUNKING_ERROR` | `422` | Không tạo được chunk hợp lệ |
| `EMBEDDING_ERROR` | `502` | Provider embedding lỗi hoặc timeout |
| `INDEX_WRITE_ERROR` | `502` | Vector store ghi thất bại |
| `RETRIEVAL_ERROR` | `502` | Vector store query thất bại |
| `RETRIEVAL_REQUIRED_INDEX_MISSING` | `400` | Thiếu `index_name` để tự retrieval |
| `PROMPT_BUILD_ERROR` | `500` | Lỗi nội bộ khi build prompt |
| `GENERATION_ERROR` | `502` | LLM provider lỗi hoặc timeout |
| `INVALID_GENERATION_OUTPUT` | `502` | Provider trả output không map được về contract |

Ví dụ:

```json
{
  "error_code": "INVALID_INPUT",
  "message": "query không được để trống",
  "details": {
    "field": "query"
  }
}
```

## Runtime defaults MVP

| Cấu hình | Default | Min | Max | Ghi chú |
|---|---|---|---|---|
| `retrieval.top_k` | `5` | `1` | `20` | Áp dụng cho `/retrieve` và `retrieval_request` |
| `generation.max_context_chunks` | `5` | `1` | `10` | Giới hạn chunk đưa vào prompt |
| `ingestion.chunk_size_chars` | `1000` | `300` | `2000` | Dùng theo ký tự, không theo token |
| `ingestion.chunk_overlap_chars` | `150` | `0` | `300` | Phải nhỏ hơn `chunk_size_chars` |
| `limits.content_length` | `100000` | `1` | `100000` | Public API MVP |
| `limits.query_length` | `2000` | `1` | `2000` | Public API MVP |
| `limits.question_length` | `2000` | `1` | `2000` | Public API MVP |

Nguyên tắc override:

- Config runtime chỉ được siết chặt hoặc nới trong biên đã khóa của spec.
- Mọi thay đổi config runtime phải được phản ánh ở test cấu hình tương ứng.
