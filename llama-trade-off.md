# Ý Kiến Kỹ Thuật: Tận Dụng LlamaIndex Mà Không Phá Kiến Trúc Hiện Tại

## Bối cảnh

Track `core` hiện đang ở nhịp `real_vector_store_adapter` (spec 58). Mục tiêu gần nhất là thay vector store giả hiện tại bằng backend vector thật, nhưng vẫn giữ nguyên HTTP contract, domain model, và các semantics đã khóa trong `docs/00-core-brief.md` và decision log hiện hành.

Điểm cần lưu ý: kiến trúc hiện tại đã khóa rất chặt boundary giữa `domain` / `use case` / `infrastructure`. Vì vậy, câu hỏi không phải là "có dùng LlamaIndex hay không", mà là "dùng LlamaIndex ở lớp nào".

## Các lựa chọn

### 1. Không dùng LlamaIndex, tự viết adapter trực tiếp

Ưu điểm:
- Ít dependency mới.
- Kiểm soát semantics tối đa.
- Scope gọn, phù hợp với spec 58.

Nhược điểm:
- Tự duy trì integration với backend.
- Về sau nếu cần loaders, reranker, hoặc backend khác thì sẽ phải tiếp tục tự làm.

### 2. Dùng LlamaIndex như adapter hạ tầng có kiểm soát

Đây là phương án tối ưu nhất cho hiện tại.

Nguyên tắc:
- Chỉ dùng các thành phần data-access hoặc utility của LlamaIndex trong `src/tuesday/rag/infrastructure/`.
- Không dùng `VectorStoreIndex`, `QueryEngine`, `ResponseSynthesizer`, `IngestionPipeline`, `Settings`, hoặc các orchestration object khác.
- Không để `Document`, `Node`, `NodeWithScore`, hoặc object của LlamaIndex chảy ra ngoài `infrastructure/`.
- Toàn bộ phần còn lại của hệ thống vẫn tiếp tục dùng domain model và ports hiện có.

Ưu điểm:
- Tận dụng được integration sẵn có của ecosystem LlamaIndex.
- Giữ nguyên boundary và test strategy hiện tại.
- Không cần rewrite `domain`, `use_case`, `api`, hoặc runtime flow.
- Có đường lui rõ ràng nếu sau này muốn bỏ LlamaIndex.

Nhược điểm:
- Phải viết mapper giữa domain model và type của LlamaIndex.
- Phải pin version cẩn thận vì API của LlamaIndex biến động khá nhanh.

### 3. Dùng LlamaIndex như orchestration spine

Phương án này không nên chọn trong nhịp hiện tại.

Lý do:
- Sẽ lan framework vào các lớp `ingestion`, `retrieval`, `generation`.
- Làm suy yếu hoặc phá vỡ các guardrail hiện có.
- Buộc phải viết lại nhiều test và cập nhật nhiều decision log/spec cùng lúc.
- Chi phí lớn hơn rất nhiều so với giá trị cần cho spec 58.

## Khuyến nghị

Khuyến nghị chọn **phương án 2**: dùng LlamaIndex như adapter hạ tầng có kiểm soát.

Cụ thể:
- Giữ nguyên `domain`, `use_case`, `service`, `api`, `runtime` theo kiến trúc hiện tại.
- Chỉ thêm adapter mới ở `infrastructure/` để wrap backend vector thật.
- Bắt đầu với **Qdrant** cho v1.

## Vì sao chọn Qdrant cho v1

- Phù hợp hơn với use case vector store thuần.
- Semantics filter, đặc biệt `tags contains-any`, có khả năng map tự nhiên hơn.
- Có lựa chọn chạy cục bộ thuận tiện cho integration test.
- Giảm số lượng workaround ở tầng application so với các lựa chọn nặng tính relational hơn như `pgvector`.

## Những gì sẽ thay đổi nếu chốt hướng này

Thay đổi nên giới hạn ở các phần sau:

- Thêm adapter vector store mới trong `src/tuesday/rag/infrastructure/`.
- Thêm mapper giữa domain model và object của LlamaIndex.
- Mở rộng `runtime/config.py` và `runtime/container.py` để chọn backend mới.
- Thêm integration test cho adapter mới.

Những phần **không nên đổi**:

- `src/tuesday/rag/domain/`
- `src/tuesday/rag/ingestion/`
- `src/tuesday/rag/retrieval/`
- `src/tuesday/rag/generation/`
- HTTP contract hiện có
- Các semantics đã khóa trong decision log

## Trade-off chấp nhận

- Thêm dependency và rủi ro version churn từ LlamaIndex.
- Chấp nhận một lớp mapper ở `infrastructure/`.

Đổi lại:
- Không phải "làm lại bánh xe" cho integration.
- Không phải pivot kiến trúc toàn hệ thống.
- Vẫn giữ quyền kiểm soát behavior cốt lõi ở codebase của dự án.

## Quyết định đề xuất

Chốt theo hướng sau:

1. Không pivot sang mô hình để LlamaIndex điều phối toàn bộ pipeline.
2. Cho phép dùng LlamaIndex trong `infrastructure/` như một adapter library có kiểm soát.
3. Backend đầu tiên cho spec 58 là `Qdrant`.
4. Phạm vi triển khai chỉ gồm adapter, mapper, config/container wiring, và integration test.

## Kết luận

Nếu mục tiêu là đi nhanh nhưng vẫn giữ được kiến trúc đã khóa, thì hướng đúng không phải là "đưa LlamaIndex vào toàn bộ hệ thống", mà là "dùng đúng phần của LlamaIndex ở đúng chỗ". Với nhịp hiện tại, lựa chọn hợp lý nhất là **selective adoption ở lớp infrastructure, bắt đầu bằng Qdrant**.
