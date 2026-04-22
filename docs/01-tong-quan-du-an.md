# 01. Tổng Quan Dự Án

## Mục lục
- Mục tiêu dự án
- Phạm vi MVP
- Ngoài phạm vi
- Giả định kỹ thuật
- Ràng buộc kiến trúc
- Nguyên tắc thiết kế

## Mục tiêu dự án

Xây dựng một RAG core cho chatbot doanh nghiệp với các mục tiêu:

- Cung cấp pipeline nền tảng cho `ingestion`, `retrieval`, `generation`.
- Tách biệt rõ domain và hạ tầng để tránh phụ thuộc trực tiếp vào LlamaIndex hoặc provider cụ thể.
- Cho phép thay thế vector store, cloud LLM, cloud embedding với chi phí thay đổi thấp.
- Tạo nền đặc tả đủ rõ để team triển khai theo hướng Spec-Driven Development kết hợp TDD.

## Phạm vi MVP

MVP bao gồm:

- Nhận tài liệu đầu vào ở dạng văn bản đã chuẩn hóa cho public API MVP.
- Cho phép parser file tồn tại ở infrastructure để phục vụ nguồn nhập nội bộ hoặc mở rộng sau MVP, nhưng không khóa contract HTTP công khai vào upload file ngay từ sprint đầu.
- Tách tài liệu thành `Chunk`, gắn metadata chuẩn, sinh embedding, và lập chỉ mục vào vector store.
- Nhận truy vấn, thực hiện truy hồi ngữ cảnh theo `top_k` và bộ lọc metadata cơ bản.
- Sinh câu trả lời dựa trên ngữ cảnh truy hồi được.
- Trả về citation theo `chunk_id`.
- Cung cấp API đồng bộ qua FastAPI cho:
  - `POST /documents/index`
  - `POST /retrieve`
  - `POST /generate`
- Ghi log kỹ thuật tối thiểu để trace request.
- Khi không có context phù hợp, trả kết quả `insufficient_context` trực tiếp ở orchestration/capability layer, không gọi LLM.

## Ngoài phạm vi

Các hạng mục chưa thuộc MVP:

- Giao diện người dùng chat hoàn chỉnh.
- Quản trị người dùng, phân quyền đa tenant, RBAC.
- Đồng bộ tài liệu theo lịch, CDC, webhook ingestion.
- OCR nâng cao, parse bảng phức tạp, parse layout nâng cao.
- Reranker chuyên biệt.
- Bộ nhớ hội thoại dài hạn.
- Streaming response.
- Cơ chế feedback loop, evaluation tự động, A/B test.
- Workflow orchestration phân tán, hàng đợi nền, batch job quy mô lớn.

## Giả định kỹ thuật

- Hệ thống ưu tiên tài liệu tiếng Việt và tiếng Anh dạng văn bản.
- Tài liệu đầu vào ban đầu có kích thước vừa phải, phục vụ MVP nội bộ.
- Cloud embedding model hỗ trợ embedding cho nội dung tài liệu và truy vấn.
- Cloud LLM hỗ trợ sinh câu trả lời không cần fine-tune.
- Vector store ban đầu có thể là một giải pháp managed hoặc self-hosted, nhưng phải được che sau port nội bộ.
- LlamaIndex chỉ được dùng trong adapter hoặc engine layer, không đi vào domain model và use case.
- MVP chấp nhận xử lý ingestion đồng bộ trước, nếu cần tối ưu sẽ tách bất đồng bộ sau MVP.
- Public API MVP ưu tiên JSON đơn giản; các mode ingestion phức tạp hơn có thể bổ sung sau khi luồng text chuẩn hóa ổn định.
- Re-index policy của MVP là `replace-by-document_id-within-index_name`.
- Cấu hình runtime của MVP được nạp một lần khi khởi động ứng dụng; cho phép override các default/min/max đã khóa trong spec nhưng không được làm thay đổi public contract.

## Ràng buộc kiến trúc

- Ngôn ngữ triển khai: Python.
- API layer: FastAPI.
- Kiến trúc: ports/adapters.
- Domain model nội bộ là nguồn sự thật duy nhất cho use case.
- Business logic không phụ thuộc trực tiếp vào:
  - object model của LlamaIndex
  - SDK riêng của vector store
  - SDK riêng của cloud LLM/embedding
- Mọi object framework-specific phải được map về model nội bộ trước khi đi vào orchestration/capability layer.
- Hành vi `generation` phải grounding vào context đã truy hồi.

## Nguyên tắc thiết kế

- Ưu tiên đơn giản nhưng tách lớp đúng chỗ.
- Chỉ đặc tả những gì cần để triển khai MVP thật.
- Tách rõ 3 boundary:
  - `ingestion`
  - `retrieval`
  - `generation`
- Mỗi use case phải có input, output, validation, error cases, acceptance criteria và test case mức use case.
- Mọi cổng tích hợp ngoài hệ thống phải đi qua port.
- Metadata của chunk phải đủ để:
  - lọc theo tài liệu
  - truy vết citation
  - hỗ trợ mở rộng sau MVP
- Ưu tiên deterministic behavior ở orchestration/capability layer; phần không deterministic được cô lập trong adapter gọi mô hình.
- Thiết kế để thay thế engine mà không làm đổi API contract công khai.
- Với trường hợp không có context phù hợp, orchestration/capability layer nên trả kết quả `insufficient_context` có kiểm soát thay vì phụ thuộc hoàn toàn vào hành vi ngẫu nhiên của LLM.
