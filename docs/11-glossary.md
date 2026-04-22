# 11. Glossary

## Mục lục
- Thuật ngữ chính

## Thuật ngữ chính

| Thuật ngữ | Giải thích |
|---|---|
| RAG | Mô hình sinh có tăng cường truy hồi. Hệ thống truy tìm ngữ cảnh trước rồi mới sinh câu trả lời. |
| chunk | Đoạn văn bản nhỏ được cắt ra từ tài liệu để làm đơn vị embedding và retrieval. |
| embedding | Biểu diễn vector của văn bản để đo độ tương đồng ngữ nghĩa. |
| retrieval | Bước truy hồi các chunk liên quan từ chỉ mục dựa trên truy vấn. |
| reranker | Thành phần xếp hạng lại kết quả retrieval bằng mô hình chuyên biệt. Không thuộc MVP hiện tại. |
| grounding | Nguyên tắc buộc câu trả lời bám vào ngữ cảnh đã truy hồi. |
| citation | Tham chiếu nguồn trong câu trả lời. Trong dự án này citation chuẩn là `chunk_id`. |
| composite service | Service ở application layer điều phối nhiều port lõi để thực hiện một luồng nghiệp vụ. Trong MVP này gồm `Indexer`, `Retriever`, `Generator`. |
| hot path | Luồng xử lý trực tiếp ảnh hưởng độ trễ người dùng, ví dụ `/retrieve`, `/generate`. |
| adapter | Thành phần triển khai một port để tích hợp với công nghệ cụ thể. |
| port | Interface ở ranh giới application với hạ tầng. |
| config runtime | Tập cấu hình được nạp khi ứng dụng khởi động để override các giá trị mặc định trong biên spec. |
| vector store | Hệ lưu trữ vector và metadata, hỗ trợ truy vấn tương đồng. |
| ingestion | Luồng tiếp nhận tài liệu, parse, chunk, embed và index. |
| generation | Luồng sinh câu trả lời từ context. |
| metadata filter | Điều kiện lọc trên metadata để giới hạn phạm vi retrieval. |
| top_k | Số lượng chunk tối đa được trả về ở retrieval. |
| chunk_size | Kích thước chunk mục tiêu trong ingestion. MVP hiện dùng theo số ký tự thay vì token. |
| chunk_overlap | Phần chồng lặp giữa hai chunk liên tiếp để giảm mất ngữ cảnh khi cắt tài liệu. |
| logical index | Tên chỉ mục logic do ứng dụng quản lý, độc lập với engine cụ thể. |
| re-index | Hành vi index lại một tài liệu đã tồn tại. MVP dùng policy `replace-by-document_id-within-index_name`. |
| idempotency | Kỳ vọng nghiệp vụ rằng cùng một request lặp lại không làm sai semantics hệ thống ngoài các thay đổi kỹ thuật được chấp nhận. |
| source document | Tài liệu nguồn sau khi parse và chuẩn hóa. |
| indexed chunk | Chunk đã có embedding và được ghi vào chỉ mục. |
| retrieved chunk | Chunk được lấy ra từ retrieval để dùng làm context. |
| insufficient context | Trạng thái không đủ ngữ cảnh để trả lời chắc chắn. |
| observability tối thiểu | Mức log/trace tối thiểu để debug MVP, ví dụ `request_id`, `use_case`, `error_code`, `latency_ms`, nhưng không lộ dữ liệu nhạy cảm. |
| ports/adapters | Kiến trúc tách application khỏi công nghệ hạ tầng bằng interface và adapter. |
