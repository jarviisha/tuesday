# 58. Spec Real Vector Store Adapter v1

## Trạng thái

`proposed`

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

- chọn một adapter thật giữa `Qdrant` và `pgvector`
- map đầy đủ contract `replace_document` và `query`
- khóa semantics `tags = contains-any`
- khóa semantics filter cho các field metadata còn lại
- khóa quy ước sắp xếp score trả về để tương thích behavior hiện có
- xác định rõ chiến lược `replace-by-document_id-within-index_name` trên backend thật
- thêm integration test cho adapter mới

## Ngoài phạm vi v1

- hybrid retrieval
- reranker
- multi-store federation
- tối ưu advanced indexing ngoài nhu cầu contract hiện có

## Semantics phải khóa trước khi code

- filter `tags` có phải tiếp tục là contains-any tuyệt đối không
- backend trả score theo thang nào và app có cần normalize hay không
- app có tiếp tục sort lại theo score ở application layer hay tin hoàn toàn vào backend
- replace document có cần transaction-like behavior nào để tránh partial state hay không

## Success criteria

- có decision rõ backend nào được chọn cho v1
- có spec implementation chi tiết cho adapter mới
- có integration test chứng minh semantics query và replace không lệch
- benchmark/smoke/regression tối thiểu vẫn pass trên adapter mới hoặc trên fake đủ tương thích

## Verification mong muốn

- contract test cho `VectorStore`
- integration test cho query filters và score ordering
- smoke test `index -> retrieve -> generate`
- benchmark so sánh với baseline trước đó nếu có thể
