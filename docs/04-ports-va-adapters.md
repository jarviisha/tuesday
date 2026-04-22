# 04. Ports Và Adapters

## Mục lục
- Cách áp dụng kiến trúc ports/adapters
- Boundary orchestration/capability và infrastructure
- Danh sách port
- Service nội bộ gần capability
- Trách nhiệm từng port
- Adapter sử dụng LlamaIndex và cloud provider
- Nguyên tắc thay thế engine

## Cách áp dụng ports/adapters cho dự án

Mục tiêu của ports/adapters trong dự án này:

- Ổn định orchestration nội bộ khi thay đổi công nghệ hạ tầng.
- Cô lập SDK và object model bên ngoài.
- Cho phép test use case bằng fake hoặc mock adapter.

Quy tắc:

- Orchestration/capability layer chỉ biết interface.
- Infrastructure chịu trách nhiệm:
  - gọi SDK
  - map dữ liệu vào/ra domain model
  - chuyển lỗi kỹ thuật sang lỗi hạ tầng có kiểm soát

## Boundary giữa orchestration/capability và infrastructure

### Orchestration/capability layer chịu trách nhiệm

- Validate nghiệp vụ.
- Điều phối thứ tự xử lý use case.
- Ghép dữ liệu từ nhiều port.
- Quyết định fallback và error mapping ở mức use case.

### Infrastructure layer chịu trách nhiệm

- Gọi LlamaIndex nếu được dùng như engine phụ trợ.
- Gọi cloud provider cho embedding và LLM.
- Gọi vector store cụ thể.
- Parse file đầu vào.
- Chuyển object bên ngoài thành domain model nội bộ.

## Danh sách interface/port lõi cần có

- `EmbeddingProvider`
- `LLMProvider`
- `VectorStore`
- `DocumentParser`
- `Chunker`

## Service nội bộ gần capability

Trong MVP này:

- `Indexer`
- `Retriever`
- `Generator`

được xem là service nội bộ gần capability, chưa phải port lõi.

Nguyên tắc:

- Service nội bộ có thể điều phối nhiều port lõi.
- Service nội bộ không làm thay đổi boundary giữa orchestration/capability và infrastructure.
- Nếu sau này cần thay engine hoặc tách abstraction sâu hơn, khi đó mới cân nhắc nâng chúng thành port riêng.

## Trách nhiệm của từng port

### EmbeddingProvider

Trách nhiệm:

- Nhận danh sách text hoặc một query text.
- Trả về embedding dưới dạng `list[float]`.
- Không trả về object SDK.

Đầu ra kỳ vọng:

- Embedding cùng kích thước ổn định theo cấu hình model.

### LLMProvider

Trách nhiệm:

- Nhận prompt hoàn chỉnh hoặc message đã chuẩn hóa nội bộ.
- Trả về văn bản sinh ra.
- Không tự ý fetch thêm dữ liệu ngoài context đã cung cấp.

### VectorStore

Trách nhiệm:

- Upsert `IndexedChunk`.
- Truy vấn theo embedding + filter metadata.
- Xóa hoặc thay thế bản ghi nếu cần ở mức kỹ thuật.

Lưu ý:

- Port này không được buộc orchestration/capability layer biết chi tiết engine của vector store.

### DocumentParser

Trách nhiệm:

- Nhận input tài liệu thô.
- Parse và chuẩn hóa thành `SourceDocument`.

### Chunker

Trách nhiệm:

- Nhận `SourceDocument`.
- Trả về danh sách `Chunk`.
- Bảo toàn mapping thứ tự và metadata nền.

### Indexer

Vai trò hiện tại: service nội bộ gần capability, không phải port lõi.

Trách nhiệm:

- Điều phối bước biến `Chunk` thành `IndexedChunk`.
- Thường dùng:
  - `EmbeddingProvider`
  - `VectorStore`
- Áp dụng policy `replace-by-document_id-within-index_name` trước khi ghi mới.
- Có thể dùng helper hạ tầng như LlamaIndex nhưng phải trả về model nội bộ.

### Retriever

Vai trò hiện tại: service nội bộ gần capability, không phải port lõi.

Trách nhiệm:

- Nhận `RetrievalRequest`.
- Gọi embedding cho query.
- Gọi vector store để truy hồi.
- Map kết quả thành `RetrievalResponse`.

### Generator

Vai trò hiện tại: service nội bộ gần capability, không phải port lõi.

Trách nhiệm:

- Nhận `GenerationRequest`.
- Build prompt từ retrieved context theo quy tắc grounding.
- Gọi `LLMProvider`.
- Map kết quả thành `GeneratedAnswer`.
- Nếu không có context khả dụng thì trả trực tiếp `insufficient_context`, không gọi `LLMProvider`.

## Adapter nào dùng LlamaIndex

LlamaIndex chỉ được dùng trong infrastructure với vai trò engine phụ trợ. Các helper hoặc adapter hạ tầng có thể dùng LlamaIndex để phục vụ:

| Thành phần hạ tầng | Có thể dùng LlamaIndex | Ghi chú |
|---|---|---|
| Helper cho `Indexer` | Có | Dùng để pipeline embedding/indexing nếu tiện |
| Helper cho `Retriever` | Có | Dùng retrieval abstraction nhưng phải map về `RetrievedChunk` |
| Helper cho `Generator` | Có giới hạn | Chỉ dùng như helper build context/prompt nếu cần |

Ràng buộc:

- Không expose `Node`, `Document`, `QueryEngine`, `Response` của LlamaIndex ra orchestration/capability layer.
- Nếu LlamaIndex bị thay thế, domain và use case không phải sửa contract.

## Adapter nào dùng cloud provider

| Port | Loại adapter | Ví dụ vai trò |
|---|---|---|
| `EmbeddingProvider` | Cloud embedding adapter | Gọi API embedding |
| `LLMProvider` | Cloud LLM adapter | Gọi API chat/completion |
| `VectorStore` | Vector database adapter | Gọi SDK/query API |
| `DocumentParser` | Parser adapter | Parse text, pdf cơ bản |

## Nguyên tắc thay thế engine

- Port phải mô tả bằng ngôn ngữ nghiệp vụ hoặc kỹ thuật mức hệ thống, không gắn SDK.
- Mọi adapter phải có bài test contract tối thiểu.
- Không đưa kiểu dữ liệu riêng của provider vào domain.
- Mọi field trả về ra ngoài API phải lấy từ domain model nội bộ.
- Khi thay engine:
  - không đổi API contract
  - không đổi use case behavior đã chốt
  - chỉ thay adapter và test integration tương ứng
