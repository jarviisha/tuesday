# 58. Spec Real Vector Store Adapter v1

## Trạng thái

`accepted` (`2026-04-23`)

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Semantics phải khóa trước khi code
- Success criteria
- Verification mong muốn

## Mục tiêu

Thay adapter vector store demo hiện tại bằng một adapter thật, với semantics được khóa rõ để không làm lệch behavior lõi khi chuyển nền lưu trữ.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- `VectorStore` protocol đã đủ để thêm adapter thật
- bottleneck thực dụng của hệ thống không chỉ nằm ở heuristic mà còn nằm ở adapter demo hiện tại
- việc tiếp tục tối ưu retrieval trên storage demo sẽ làm benchmark khó đại diện cho production hơn

## Phạm vi v1

Nhịp này nên ưu tiên:

- triển khai adapter thật với backend **`Qdrant`**
- cho phép dùng LlamaIndex theo mô hình **selective adoption** chỉ trong `infrastructure/`
- map đầy đủ contract `replace_document` và `query`
- khóa semantics `tags = contains-any`
- khóa semantics filter cho các field metadata còn lại
- khóa quy ước sắp xếp score trả về để tương thích behavior hiện có
- xác định rõ chiến lược `replace-by-document_id-within-index_name` trên backend thật
- thêm integration test cho adapter mới

## Ngoài phạm vi v1

- `pgvector`
- hybrid retrieval
- reranker
- multi-store federation
- tối ưu advanced indexing ngoài nhu cầu contract hiện có
- pivot sang mô hình để LlamaIndex điều phối toàn bộ pipeline

## Quyết định đã khóa cho nhịp này

- Backend v1 là **`Qdrant`**.
- LlamaIndex chỉ được dùng như adapter/helper hạ tầng trong `src/tuesday/rag/infrastructure/`.
- Không dùng `Settings`, `IngestionPipeline`, `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer` hoặc bất kỳ orchestration object nào của LlamaIndex.
- Không để `Document`, `Node`, `NodeWithScore`, `Response` hoặc object framework tương tự chảy ra ngoài `infrastructure/`.
- `domain`, `use_case`, `service`, `api` và public HTTP contract phải giữ nguyên.

## Semantics phải khóa trước khi code

- filter `tags` tiếp tục là `contains-any` tuyệt đối (theo DL-003)
- backend score được tin như nguồn sort chính; adapter vẫn phải trả kết quả theo thứ tự giảm dần của score để khớp `RetrievalResponse`
- chưa introduce thêm tầng normalize score ở application layer trong v1
- `replace_document` giữ semantics `replace-by-document_id-within-index_name`; strategy kỹ thuật v1 là delete theo `document_id + index_name` rồi upsert lại toàn bộ chunk của document trong cùng adapter operation, với integration test chứng minh behavior không lệch contract

## Success criteria

- backend `Qdrant` và boundary selective adoption của LlamaIndex đã được chốt rõ
- có implementation spec đủ chi tiết để code trực tiếp mà không phải quyết định lại kiến trúc
- có integration test chứng minh semantics query và replace không lệch
- benchmark/smoke/regression tối thiểu vẫn pass trên adapter mới hoặc trên fake đủ tương thích

## Verification mong muốn

- contract test cho `VectorStore`
- integration test cho query filters và score ordering
- integration test cho `replace-by-document_id-within-index_name`
- smoke test `index -> retrieve -> generate`
- benchmark so sánh với baseline trước đó nếu có thể

## Gợi ý phạm vi code change

Phạm vi thay đổi nên được giữ ở mức tối thiểu:

- thêm adapter vector store mới trong `src/tuesday/rag/infrastructure/`
- thêm mapper giữa domain model và object hạ tầng của `Qdrant`/LlamaIndex
- mở rộng `runtime/config.py` và `runtime/container.py` để chọn backend mới
- nếu `Qdrant` được ghép với demo embedding backend, dùng demo provider dạng dense fixed-size thay vì hash embedding độ dài biến thiên
- thêm integration test cho adapter mới

Các phần không nên đổi trong nhịp này:

- `src/tuesday/rag/domain/`
- `src/tuesday/rag/ingestion/`
- `src/tuesday/rag/retrieval/`
- `src/tuesday/rag/generation/`
- API contract hiện có
