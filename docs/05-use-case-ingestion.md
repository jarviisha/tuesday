# 05. Use Case Ingestion

## Mục lục
- Mục tiêu
- Input / output
- Luồng xử lý
- Validation rules
- Error cases
- Definition of done
- Acceptance criteria
- Test cases mức use case

## Mục tiêu use case ingestion

Nhận một tài liệu đầu vào, chuẩn hóa thành domain model, chia chunk, sinh embedding, lưu vào vector store và trả về kết quả chỉ mục hóa.

## Input / output

### Input

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `document_id` | string | Có | ID tài liệu |
| `content` | string | Có | Nội dung văn bản đã chuẩn hóa cho public API MVP |
| `title` | string | Không | Tiêu đề |
| `source_type` | string | Có | Loại nguồn |
| `source_uri` | string | Không | URI nguồn |
| `metadata` | object | Không | Metadata tài liệu |
| `index_name` | string | Có | Logical index |

### Output

`DocumentIndexResult`

## Luồng xử lý chi tiết

1. Validate request mức API và use case.
2. Với public API MVP, map request trực tiếp thành `SourceDocument`.
3. Chỉ gọi `DocumentParser` nếu có ingestion path nội bộ hoặc nguồn vào chưa ở dạng văn bản chuẩn hóa.
4. Kiểm tra nội dung sau chuẩn hóa không rỗng.
5. Gọi `Chunker` tạo danh sách `Chunk`.
6. Kiểm tra danh sách chunk không rỗng.
7. Gọi `Indexer` để:
   - thay thế dữ liệu cũ nếu đã tồn tại cùng `document_id` trong `index_name`
   - sinh embedding cho từng chunk
   - map thành `IndexedChunk`
   - upsert vào `VectorStore`
8. Thu thập kết quả thành `DocumentIndexResult`.

## Validation rules

- `document_id` không rỗng.
- `index_name` không rỗng.
- `content` sau trim không được rỗng.
- `content` nên có giới hạn mặc định `1..100000` ký tự cho MVP; ngưỡng thực thi có thể override bằng config runtime.
- `document_id` nên có giới hạn mặc định `1..128` ký tự.
- `index_name` nên có giới hạn mặc định `1..64` ký tự.
- `Chunker` của MVP dùng cấu hình theo ký tự để tránh phụ thuộc tokenizer/provider:
  - `chunk_size`: mặc định `1000`, min `300`, max `2000`
  - `chunk_overlap`: mặc định `150`, min `0`, max `300`
- `chunk_overlap` không được lớn hơn hoặc bằng `chunk_size`.
- `source_type` phải thuộc tập giá trị cho phép của MVP, ví dụ `text`, `pdf`, `html`.
- Metadata tài liệu phải là object phẳng hoặc object JSON hợp lệ.
- Nếu `metadata.language` có mặt thì phải là mã ngôn ngữ ngắn ổn định, ví dụ `vi`, `en`.
- Nếu `metadata.tags` có mặt thì phải là danh sách string không rỗng phần tử.
- Tổng số chunk sinh ra không được vượt giới hạn cấu hình cứng của MVP.

## Error cases

| Mã lỗi gợi ý | Tình huống |
|---|---|
| `INVALID_INPUT` | Thiếu trường bắt buộc hoặc giá trị không hợp lệ |
| `DOCUMENT_PARSE_ERROR` | Parse tài liệu thất bại |
| `EMPTY_DOCUMENT` | Tài liệu rỗng sau chuẩn hóa |
| `CHUNKING_ERROR` | Không tạo được chunk hợp lệ |
| `EMBEDDING_ERROR` | Provider embedding lỗi |
| `INDEX_WRITE_ERROR` | Ghi vector store thất bại |
| `PARTIAL_INDEXED` | Chỉ mục hóa thành công một phần |

Ghi chú triển khai MVP hiện tại:

- Public API hiện chỉ khóa mode JSON text chuẩn hóa, nên nhánh `DOCUMENT_PARSE_ERROR` là cho ingestion path nội bộ hoặc phase sau.
- Nhánh `PARTIAL_INDEXED` chưa được bật trong adapter MVP hiện tại; mặc định hệ thống phản ánh thất bại toàn phần khi vector store ghi lỗi.

## Definition of done

- Tài liệu được map thành `SourceDocument`.
- Chunk được tạo với metadata chuẩn.
- Mỗi chunk hợp lệ được embed và lưu vào vector store.
- Trả về `DocumentIndexResult` phản ánh đúng số lượng đã xử lý.
- `DocumentIndexResult.replaced_document` phản ánh đúng việc có thay thế dữ liệu cũ hay không.
- Lỗi được chuẩn hóa, không lộ object hoặc stack trace framework ra contract công khai.

## Acceptance criteria

- Khi input hợp lệ và hạ tầng hoạt động, hệ thống trả `status = indexed`.
- `chunk_count` lớn hơn 0 với tài liệu đủ dài.
- `indexed_count` bằng số chunk đã lưu thành công.
- Nếu cùng `document_id` đã tồn tại trong cùng `index_name`, dữ liệu cũ phải được thay thế trước khi ghi mới.
- Nếu cùng `document_id` chưa từng tồn tại trong cùng `index_name`, `replaced_document = false`.
- Nếu cùng request ingestion được gửi lặp lại với cùng `document_id`, `index_name` và nội dung chuẩn hóa không đổi, hệ thống vẫn hợp lệ và kết quả phải tương đương về mặt nghiệp vụ.
- Mỗi chunk lưu xuống phải có:
  - `chunk_id`
  - `document_id`
  - metadata chuẩn
- Nếu tài liệu rỗng sau chuẩn hóa, use case thất bại có kiểm soát.
- Nếu một phần chunk ghi thất bại, hệ thống phải phản ánh `partial` hoặc thất bại toàn phần theo chiến lược đã cấu hình.
- Public API MVP không bắt buộc hỗ trợ upload file; nếu chưa có ingestion path riêng cho file thì contract vẫn nhất quán với mode text chuẩn hóa.
- Với adapter MVP hiện tại, partial write chưa được hỗ trợ; hành vi đang khóa là fail toàn phần khi ghi lỗi.

## Test cases mức use case

| ID | Kịch bản | Input chính | Kỳ vọng |
|---|---|---|---|
| ING-01 | Index tài liệu text hợp lệ | Nội dung ngắn hợp lệ | `status = indexed`, `indexed_count > 0` |
| ING-02 | Nội dung chỉ có khoảng trắng | `content = "   "` | Lỗi `EMPTY_DOCUMENT` hoặc `INVALID_INPUT` |
| ING-03 | Parser thất bại | File hỏng hoặc format không hỗ trợ | Lỗi `DOCUMENT_PARSE_ERROR` |
| ING-04 | Chunker tạo 0 chunk | Nội dung bất thường | Lỗi `CHUNKING_ERROR` |
| ING-05 | Embedding provider lỗi | Provider timeout | Lỗi `EMBEDDING_ERROR` |
| ING-06 | Vector store ghi lỗi toàn phần | Upsert thất bại | Lỗi `INDEX_WRITE_ERROR` |
| ING-07 | Vector store ghi lỗi một phần | Một số chunk lỗi | `status = partial`, có `errors` |
| ING-08 | Re-index cùng `document_id` | Tài liệu đã tồn tại | Dữ liệu cũ bị thay thế theo policy MVP |
| ING-09 | Gửi lại cùng tài liệu không đổi | Cùng `document_id`, `index_name`, `content` | Thành công hợp lệ, không làm sai semantics nghiệp vụ |
