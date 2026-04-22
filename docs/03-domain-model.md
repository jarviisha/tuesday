# 03. Domain Model

## Mục lục
- Danh sách model cốt lõi
- Mô tả và thuộc tính
- Invariant
- Metadata schema cho chunk
- Quan hệ giữa các model

## Danh sách domain model cốt lõi

- `SourceDocument`
- `Chunk`
- `IndexedChunk`
- `RetrievedChunk`
- `RetrievalRequest`
- `RetrievalResponse`
- `GenerationRequest`
- `GeneratedAnswer`
- `DocumentIndexResult`

## Mô tả từng model

### SourceDocument

Biểu diễn tài liệu nguồn sau khi parse và chuẩn hóa.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | Định danh duy nhất của tài liệu |
| `title` | string | Không | Tiêu đề tài liệu nếu có |
| `content` | string | Có | Nội dung văn bản đã chuẩn hóa |
| `source_type` | string | Có | Loại nguồn, ví dụ `text`, `pdf`, `html` |
| `source_uri` | string | Không | Đường dẫn hoặc URI nguồn |
| `language` | string | Không | Ngôn ngữ chính của tài liệu |
| `metadata` | object | Có | Metadata cấp tài liệu |
| `checksum` | string | Không | Dấu vết nội dung để phát hiện thay đổi |

### Chunk

Đơn vị văn bản nhỏ nhất được dùng cho embedding và retrieval.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `chunk_id` | string | Có | Định danh duy nhất của chunk |
| `document_id` | string | Có | Tham chiếu tới `SourceDocument` |
| `text` | string | Có | Nội dung chunk |
| `sequence_no` | int | Có | Vị trí tuần tự trong tài liệu |
| `token_count` | int | Không | Số token ước lượng |
| `char_start` | int | Không | Vị trí bắt đầu trong tài liệu |
| `char_end` | int | Không | Vị trí kết thúc trong tài liệu |
| `metadata` | object | Có | Metadata chuẩn cho retrieval/citation |

### IndexedChunk

Chunk đã được gắn embedding và lưu được vào chỉ mục truy hồi.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `chunk_id` | string | Có | Trùng với `Chunk.chunk_id` |
| `document_id` | string | Có | Tài liệu nguồn |
| `text` | string | Có | Nội dung chunk |
| `embedding` | list[float] | Có | Vector embedding |
| `metadata` | object | Có | Metadata lưu cùng vector |
| `index_name` | string | Có | Tên logical index |

### RetrievedChunk

Chunk được trả về từ retrieval.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `chunk_id` | string | Có | Định danh chunk |
| `document_id` | string | Có | Tài liệu nguồn |
| `text` | string | Có | Nội dung chunk |
| `score` | float | Có | Điểm liên quan tương đối |
| `metadata` | object | Có | Metadata để lọc và citation |

### RetrievalRequest

Yêu cầu truy hồi ngữ cảnh.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Có | Câu hỏi hoặc truy vấn |
| `top_k` | int | Có | Số chunk tối đa cần trả về |
| `filters` | object | Không | Bộ lọc metadata |
| `index_name` | string | Có | Logical index cần truy vấn |
| `request_id` | string | Không | ID trace |

### RetrievalResponse

Kết quả trả về từ retrieval.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `query` | string | Có | Truy vấn gốc |
| `top_k` | int | Có | Giá trị đã áp dụng |
| `chunks` | list[RetrievedChunk] | Có | Danh sách chunk trả về |
| `applied_filters` | object | Có | Bộ lọc đã áp dụng thực tế |
| `index_name` | string | Có | Logical index đã truy vấn |

### GenerationRequest

Yêu cầu sinh câu trả lời.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `question` | string | Có | Câu hỏi người dùng |
| `retrieval_request` | RetrievalRequest | Không | Dùng khi hệ thống tự retrieval |
| `retrieved_chunks` | list[RetrievedChunk] | Không | Dùng khi context đã có sẵn |
| `max_context_chunks` | int | Không | Giới hạn số chunk dùng để build prompt |
| `request_id` | string | Không | ID trace |

### GeneratedAnswer

Kết quả cuối cùng của generation.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `answer` | string | Có | Câu trả lời cho người dùng |
| `citations` | list[string] | Có | Danh sách `chunk_id` được viện dẫn |
| `grounded` | bool | Có | Có đủ căn cứ từ context hay không |
| `insufficient_context` | bool | Có | Có thiếu ngữ cảnh hay không |
| `used_chunks` | list[RetrievedChunk] | Có | Các chunk thực tế đã dùng |

### DocumentIndexResult

Kết quả của use case ingestion.

| Thuộc tính | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | Tài liệu đã xử lý |
| `index_name` | string | Có | Logical index đã ghi |
| `chunk_count` | int | Có | Số chunk đã tạo |
| `indexed_count` | int | Có | Số chunk đã lưu thành công |
| `status` | string | Có | `indexed`, `partial`, `failed` |
| `errors` | list[string] | Có | Danh sách lỗi mức nghiệp vụ |
| `replaced_document` | bool | Có | Có thay thế dữ liệu cũ của cùng `document_id` trong `index_name` hay không |

## Invariant / rule quan trọng

- `document_id` phải duy nhất trong phạm vi logical index hoặc namespace.
- `chunk_id` phải duy nhất trong toàn bộ chỉ mục.
- `Chunk.document_id` phải tham chiếu tới một `SourceDocument` hợp lệ.
- `IndexedChunk.embedding` không được rỗng.
- Khi ingest lại cùng `document_id` trong cùng `index_name`, hệ thống phải thay thế dữ liệu cũ theo policy `replace-by-document_id-within-index_name`.
- `RetrievalRequest.top_k` phải > 0 và không vượt trần cấu hình.
- `RetrievedChunk.score` chỉ dùng để sắp xếp tương đối, không được coi là xác suất.
- `GenerationRequest` phải có ít nhất một trong hai trường sau được cung cấp:
  - `retrieval_request`
  - `retrieved_chunks`
- Nếu `retrieved_chunks` đã được cung cấp thì application không được tự ý gọi retrieval lại.
- Nếu `retrieved_chunks` được cung cấp dưới dạng danh sách rỗng thì request vẫn hợp lệ và phải đi theo nhánh `insufficient_context`.
- `GeneratedAnswer.citations` phải là tập con của `used_chunks.chunk_id`.
- Nếu `insufficient_context = true` thì `grounded` không được là `true`.
- Nếu `used_chunks` rỗng thì `citations` phải rỗng.

## Metadata schema cho chunk

Schema metadata chuẩn cho `Chunk`, `IndexedChunk`, `RetrievedChunk`:

| Trường | Kiểu | Bắt buộc | Mục đích |
|---|---|---|---|
| `document_id` | string | Có | Truy vết tài liệu |
| `chunk_id` | string | Có | Citation và trace |
| `title` | string | Không | Hiển thị nguồn |
| `source_type` | string | Có | Lọc theo loại nguồn |
| `source_uri` | string | Không | Truy vết nguồn |
| `sequence_no` | int | Có | Bảo toàn thứ tự |
| `language` | string | Không | Lọc ngôn ngữ |
| `tags` | list[string] | Không | Lọc nghiệp vụ cơ bản |
| `created_at` | string | Không | Theo dõi thời điểm ingest |
| `version` | string | Không | Chỉ để theo dõi version metadata, chưa ảnh hưởng retrieval logic ở MVP |

Nguyên tắc:

- Metadata phải đủ để truy vết và lọc nhưng không nhồi dữ liệu lớn.
- Không lưu object framework-specific vào metadata domain.
- Không lưu thông tin bí mật nhạy cảm trong metadata nếu không có cơ chế kiểm soát phù hợp.

## Mối quan hệ giữa các model

- Một `SourceDocument` sinh ra nhiều `Chunk`.
- Một `Chunk` sau khi được embed trở thành `IndexedChunk`.
- Từ một `RetrievalRequest`, hệ thống trả về một `RetrievalResponse` gồm nhiều `RetrievedChunk`.
- Một `GenerationRequest` dùng danh sách `RetrievedChunk` để tạo `GeneratedAnswer`.
- Một `SourceDocument` sau ingestion trả về một `DocumentIndexResult`.
