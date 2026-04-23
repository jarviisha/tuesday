# 43. Spec Internal File Ingestion V1

## Mục lục
- Mục tiêu
- Lý do ưu tiên
- Giả định đã khóa
- Phạm vi
- Ngoài phạm vi
- Thiết kế và boundary
- Luồng xử lý
- Acceptance criteria
- Verification
- Rủi ro và cách giảm rủi ro

## Mục tiêu

Bổ sung khả năng index file cục bộ hoặc nguồn nội bộ tương đương cho team vận hành mà không làm thay đổi public API contract của MVP.

Feature này phải đồng thời xác nhận rằng layout capability-oriented hiện tại đã đủ ổn để nhận feature mới đầu tiên mà không cần quay lại cấu trúc cũ.

## Lý do ưu tiên

`internal file ingestion` là bước mở rộng hợp lý nhất ở thời điểm hiện tại vì:

- nó nằm trong danh mục ưu tiên mặc định của Phase 4
- nó tăng giá trị ingestion trực tiếp mà không kéo theo endpoint công khai mới
- nó tận dụng boundary `DocumentParser` đã được thiết kế sẵn nhưng chưa dùng thật
- nó kiểm tra được chất lượng migration tốt hơn một refactor thuần cấu trúc không có feature thật đi kèm

## Giả định đã khóa

- `POST /documents/index` vẫn giữ contract JSON text chuẩn hóa như hiện tại.
- `IngestionUseCase` hiện tại tiếp tục là luồng cho dữ liệu text đã chuẩn hóa.
- `DocumentParser` vẫn là port hạ tầng; object parser/framework-specific không được rò lên application/domain.
- Semantics `replace-by-document_id-within-index_name`, `citations`, `insufficient_context` và `tags = contains-any` không đổi.
- Nhịp `v1` chỉ khóa file text-based đơn giản: `.txt` và `.md`.

## Phạm vi

Feature `v1` bao gồm:

- một entrypoint nội bộ rõ ràng để index file mà không đi qua public HTTP contract
- một use case hoặc orchestration nội bộ riêng cho file ingestion, thay vì nhồi logic parser vào HTTP use case hiện có
- adapter `DocumentParser` cho file `.txt` và `.md`
- normalize metadata tối thiểu từ file path và input nội bộ
- kiểm thử cho parser, orchestration và semantics re-index

Entry point nội bộ được khuyến nghị:

- script hoặc command trong repo, ví dụ `scripts/index_file.py`
- hoặc callable nội bộ tương đương nếu team muốn bọc lại sau

Mục tiêu của entrypoint này là:

- phục vụ local/staging/internal operations
- không trở thành public contract ngầm
- không ép team đưa file upload vào FastAPI trong cùng nhịp

## Ngoài phạm vi

- upload file qua multipart HTTP
- parser `html`, `pdf`, OCR hoặc layout-aware parsing
- index cả thư mục, directory crawling hoặc sync định kỳ
- async ingestion, batch queue hoặc retry orchestration riêng cho batch lớn
- tự động trích metadata nâng cao từ nội dung tài liệu

## Thiết kế và boundary

### 1. Giữ tách biệt giữa public ingestion và internal file ingestion

Luồng HTTP hiện tại tiếp tục xử lý payload text chuẩn hóa. Luồng file nội bộ là một capability path riêng, dùng parser để tạo `SourceDocument`, sau đó đi qua cùng semantics chunking/indexing đã khóa.

Không nên sửa `IngestionUseCase.execute()` hiện tại để nhận cả file path và payload HTTP trong cùng một object mơ hồ. Cách đơn giản hơn là:

- giữ `IngestionUseCase` cho normalized text
- thêm một `FileIngestionUseCase` hoặc orchestration tương đương
- tách phần index `SourceDocument` đã chuẩn hóa thành logic dùng chung mức nhỏ nếu cần

### 2. Parser contract

`DocumentParser` nhận raw input nội bộ và trả `SourceDocument`.

Raw input tối thiểu nên có:

- `path`
- `document_id`
- `index_name`
- `title` tùy chọn
- `metadata` tùy chọn

Rule gợi ý:

- `title` mặc định lấy từ tên file nếu caller không truyền
- `source_uri` mặc định là đường dẫn tuyệt đối hoặc URI file ổn định
- `source_type` được suy ra từ extension nhưng vẫn phải map về tập giá trị domain cho phép
- `metadata.language` và `metadata.tags` nếu caller truyền thì vẫn phải đi qua validation hiện tại

### 3. Migration coupling

Nếu `api.dependencies` hoặc shim chuyển tiếp khác vẫn còn tồn tại, nhịp này được phép giữ tạm trong lúc feature hoàn tất. Tuy nhiên sau khi regression và smoke pass, team nên:

- bỏ shim không còn cần thiết
- dọn import graph để feature mới đi qua `runtime/` và capability packages đúng hướng đã khóa

Không dùng feature này như lý do để mở thêm package hoặc abstraction mới ngoài phạm vi thực cần.

## Luồng xử lý

1. Entry point nội bộ nhận yêu cầu index file với `path`, `document_id`, `index_name` và metadata tùy chọn.
2. Validate `path` tồn tại, là file thường, extension thuộc tập hỗ trợ của `v1`, và caller đã cung cấp các field bắt buộc.
3. `FileIngestionUseCase` gọi `DocumentParser` để đọc file và map thành `SourceDocument`.
4. Sau khi parse xong, orchestration dùng cùng rule validation/chunking/indexing như ingestion hiện tại.
5. `IndexerService` tiếp tục áp dụng policy `replace-by-document_id-within-index_name`.
6. Kết quả trả về phản ánh cùng semantics `DocumentIndexResult`.
7. Failure của parser phải được map về lỗi có kiểm soát như `DOCUMENT_PARSE_ERROR` hoặc `INVALID_INPUT`, không làm lộ stack trace hay chi tiết parser library ra contract nội bộ.

## Acceptance criteria

- Có một đường vào nội bộ rõ ràng để index file `.txt` và `.md`.
- Public API `/documents/index` không đổi request/response schema.
- Cùng một file được index lặp lại với cùng `document_id` và `index_name` vẫn bám policy replace hiện tại.
- `SourceDocument` sinh từ parser có đủ field cần cho chunking, retrieval filter và citation trace hiện tại.
- Parser lỗi, file không tồn tại hoặc extension không hỗ trợ đều trả failure có kiểm soát.
- Regression suite hiện có vẫn pass sau khi thêm feature.
- Feature mới có runbook hoặc command example đủ để team khác chạy lại trong local/staging.

## Verification

- Unit test cho parser `.txt` và `.md`.
- Unit test hoặc use case test cho `FileIngestionUseCase`, bao gồm:
  - file hợp lệ
  - file rỗng sau normalize
  - extension không hỗ trợ
  - re-index cùng `document_id`
- Integration test chứng minh dữ liệu index từ file vẫn truy hồi được qua `/retrieve` và `/generate`.
- Chạy lại smoke test hiện có để xác nhận feature mới không làm hỏng baseline cũ.
- Chạy lại regression suite và benchmark Phase 3 nếu migration cleanup chạm vào import graph hoặc runtime wiring.

## Rủi ro và cách giảm rủi ro

Rủi ro chính:

- parser làm trộn boundary giữa raw file handling và ingestion orchestration
- nhịp feature đầu tiên bị phình sang upload HTTP hoặc parser phức tạp
- migration cleanup kéo dài quá mức và biến thành refactor không có điểm dừng

Cách giảm rủi ro:

- giữ `v1` chỉ hỗ trợ `.txt` và `.md`
- tách use case nội bộ riêng cho file thay vì nhồi nhiều mode vào endpoint hiện có
- dùng lại `DocumentIndexResult` và semantics hiện tại thay vì tạo contract mới
- chỉ bỏ compatibility shim sau khi test nền pass và import graph đã rõ
