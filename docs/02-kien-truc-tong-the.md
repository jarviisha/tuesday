# 02. Kiến Trúc Tổng Thể

## Mục lục
- Kiến trúc tổng thể MVP
- Thành phần chính
- Hot path và non-hot path
- Vai trò công nghệ
- Luồng online và offline
- Hướng mở rộng sau MVP

## Kiến trúc tổng thể MVP

MVP khởi đầu theo kiến trúc 4 lớp, và sau nhịp migration Phase 4 đầu tiên repo đang ở trạng thái capability-oriented nhẹ:

1. `api/`
   - FastAPI nhận request, validate schema, map lỗi và giữ request-level observability.
2. `runtime/`
   - Chứa composition root và runtime wiring dùng chung.
3. Capability packages
   - `ingestion/`, `retrieval/`, `generation/` chứa use case/service gần với từng capability.
4. `domain/`
   - Chứa domain model, invariant, interface/port.
5. `infrastructure/`
   - Adapter cho chunking, provider, resilience và vector store.

Luồng phụ thuộc hiện tại:

- `api -> runtime -> capability packages -> domain ports -> infrastructure adapters`
- Không có chiều ngược lại từ `domain` hoặc capability packages sang framework object.

## Các thành phần chính

| Thành phần | Vai trò | Ghi chú |
|---|---|---|
| FastAPI API | Điểm vào HTTP cho MVP | Không chứa business logic |
| Runtime Container | Composition root và runtime wiring | Không neo trực tiếp vào HTTP layer |
| Ingestion Use Case | Parse, chunk, embed, index | Nằm trong capability `ingestion/` |
| Retrieval Use Case | Embed query, tìm kiếm, lọc metadata | Nằm trong capability `retrieval/` |
| Generation Use Case | Build prompt, grounding, sinh answer | Nằm trong capability `generation/` |
| Domain Models | Mô hình dữ liệu nội bộ | Không phụ thuộc framework |
| Ports | Khai báo interface lõi | Là hợp đồng giữa app và hạ tầng |
| Capability Services | Điều phối port gần với capability | Gồm `Indexer`, `Retriever`, `Generator` |
| LlamaIndex Adapter | Tận dụng engine indexing/retrieval nếu cần | Chỉ là adapter |
| Vector Store Adapter | Lưu và truy vấn vector | Có thể thay thế |
| Cloud Embedding Adapter | Sinh embedding | Có thể thay thế |
| Cloud LLM Adapter | Sinh câu trả lời | Có thể thay thế |

## Hot path và non-hot path

### Hot path

Hot path là các luồng ảnh hưởng trực tiếp đến độ trễ request online:

- `POST /retrieve`
- `POST /generate`

Yêu cầu:

- Số bước xử lý ít, rõ ràng.
- Không parse lại tài liệu gốc ở hot path.
- Không gọi adapter không cần thiết.
- Truy vết được `request_id`, `chunk_id`.

### Non-hot path

Non-hot path là các luồng chấp nhận độ trễ cao hơn:

- `POST /documents/index`
- Chuẩn hóa tài liệu
- Re-index khi đổi chiến lược chunking hoặc embedding

Yêu cầu:

- Ưu tiên tính đúng và khả năng phục hồi.
- Có thể nâng cấp sang bất đồng bộ sau MVP.

## Vai trò của FastAPI, LlamaIndex, vector store, cloud LLM, cloud embedding

| Công nghệ | Vai trò trong MVP | Boundary |
|---|---|---|
| FastAPI | HTTP transport, schema validation, error mapping | Chỉ ở API layer |
| LlamaIndex | Engine/adaptor hỗ trợ indexing/retrieval/generation plumbing | Chỉ ở infrastructure |
| Vector store | Lưu vector và metadata, truy hồi tương đồng | Sau port `VectorStore` |
| Cloud embedding | Biến text thành vector embedding | Sau port `EmbeddingProvider` |
| Cloud LLM | Sinh câu trả lời từ prompt có context | Sau port `LLMProvider` |

## Luồng online và luồng offline

### Luồng offline: ingestion

1. API nhận tài liệu đầu vào.
2. Với public API MVP, request JSON được map trực tiếp thành `SourceDocument`.
3. `DocumentParser` chỉ được gọi khi nguồn vào không phải văn bản đã chuẩn hóa hoặc khi có ingestion path nội bộ riêng.
4. Capability `ingestion` gọi `Chunker` để tạo danh sách `Chunk`.
5. Capability `ingestion` gọi `EmbeddingProvider` để sinh embedding cho từng chunk.
6. Capability `ingestion` gọi service `Indexer` để map `Chunk` thành `IndexedChunk` và ghi vào `VectorStore`.
7. Trước khi ghi mới, hệ thống xóa hoặc thay thế toàn bộ dữ liệu cũ của cùng `document_id` trong cùng `index_name` theo policy `replace-by-document_id-within-index_name`.
8. Trả về `DocumentIndexResult`.

### Luồng online: retrieval

1. API nhận truy vấn.
2. Capability `retrieval` tạo `RetrievalRequest`.
3. Gọi service `Retriever`.
4. `Retriever` dùng `EmbeddingProvider` + `VectorStore`.
5. Kết quả được map về `RetrievalResponse` gồm danh sách `RetrievedChunk`.

### Luồng online: generation

1. API nhận câu hỏi và tùy chọn retrieved context hoặc yêu cầu hệ thống tự retrieval.
2. Capability `generation` chuẩn hóa thành `GenerationRequest`.
3. Nếu chưa có context, gọi service `Retriever`.
4. Nếu sau retrieval không có context phù hợp, capability `generation` có thể trả trực tiếp kết quả `insufficient_context` theo policy MVP mà không cần gọi `LLMProvider`.
5. Nếu có context, build prompt theo quy tắc grounding.
6. Gọi service `Generator`, bên dưới dùng `LLMProvider`.
7. Trả về `GeneratedAnswer` với citation theo `chunk_id`.

## Hướng mở rộng sau MVP

- Tách ingestion sang job queue.
- Bổ sung reranker qua port riêng.
- Hỗ trợ nhiều parser theo loại file.
- Bổ sung hybrid retrieval: vector + keyword.
- Thêm tenant boundary và quyền truy cập metadata.
- Thêm evaluation harness cho retrieval precision và answer grounding.
- Bổ sung streaming, conversation state, caching.
