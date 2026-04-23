# 10. Kế Hoạch Triển Khai Theo Sprint

## Mục lục

- Thứ tự triển khai
- Sprint 1
- Sprint 2
- Sprint 3
- Trạng thái chốt MVP
- Deliverable
- Rủi ro kỹ thuật
- Cách giảm rủi ro

## Thứ tự triển khai

Thứ tự đề xuất:

1. Chốt spec và model nội bộ.
2. Dựng skeleton ports/adapters và dependency wiring.
3. Hoàn thành ingestion trước.
4. Hoàn thành retrieval sau khi dữ liệu index được.
5. Hoàn thành generation sau khi retrieval ổn định.
6. Khóa API contract và bổ sung integration test tối thiểu.

## Sprint 1

Mục tiêu:

- Chốt domain và ingestion foundation.

Phạm vi:

- Khởi tạo cấu trúc thư mục theo ports/adapters.
- Tạo domain model và validator.
- Tạo port interface.
- Triển khai use case ingestion mức cơ bản.
- Tạo fake adapter để chạy test use case.
- Tạo API `POST /documents/index`.
- Giữ public API ingestion ở mode JSON text trước; parser file chỉ giữ ở dạng adapter mở rộng hoặc ingestion path nội bộ.
- Khóa `chunk_size/chunk_overlap` theo ký tự và wiring config runtime cơ bản.

Deliverable:

- Domain model compile được.
- Test ingestion xanh.
- Endpoint index hoạt động với adapter giả hoặc adapter thật tối thiểu.
- Parser file và partial indexing không phải deliverable bắt buộc của public MVP sprint này.

## Sprint 2

Mục tiêu:

- Hoàn thành retrieval foundation.

Phạm vi:

- Triển khai `EmbeddingProvider` adapter.
- Triển khai `VectorStore` adapter.
- Triển khai `Retriever`.
- Tạo API `POST /retrieve`.
- Bổ sung filter whitelist và `top_k` behavior.
- Khóa semantics `tags = contains-any`.

Deliverable:

- Retrieval use case chạy được end-to-end.
- API retrieve có contract test và ít nhất 1 integration test adapter.

## Sprint 3

Mục tiêu:

- Hoàn thành generation và khóa MVP.

Phạm vi:

- Triển khai `LLMProvider` adapter.
- Triển khai `Generator`.
- Tạo prompt builder theo spec grounding.
- Tạo API `POST /generate`.
- Bổ sung test cho citation, insufficient context, error mapping.
- Chốt policy: khi không có context thì application trả kết quả `insufficient_context` có kiểm soát, không bắt buộc gọi LLM.
- Khóa bảng HTTP error mapping MVP.
- Khóa literal mặc định cho response `insufficient_context` và log tối thiểu cho request lifecycle.

Deliverable:

- Luồng index -> retrieve -> generate chạy được.
- Bộ test cốt lõi xanh.
- Tài liệu spec được rà chéo và khóa cho MVP.

## Trạng thái chốt MVP

Trạng thái hiện tại: **public MVP đã được đóng scope**.

Public MVP được coi là hoàn tất khi thỏa các điều kiện sau:

- Có 3 endpoint công khai:
  - `POST /documents/index`
  - `POST /retrieve`
  - `POST /generate`
- Ingestion public chỉ khóa mode JSON text chuẩn hóa.
- Retrieval giữ đúng `top_k`, whitelist filter và semantics `tags = contains-any`.
- Generation giữ đúng nhánh `insufficient_context`, grounding theo context, citation theo `chunk_id`.
- Có test cho contract HTTP, use case cốt lõi, adapter integration tối thiểu và observability cơ bản.

Những phần không còn được coi là blocker của public MVP:

- parser file hoặc ingestion path nội bộ
- `DOCUMENT_PARSE_ERROR` ở HTTP public flow
- `PARTIAL_INDEXED`
- provider hoặc vector store thật thay cho adapter fake/in-memory

## Deliverable mỗi sprint

| Sprint   | Deliverable chính                                   |
| -------- | --------------------------------------------------- |
| Sprint 1 | Domain + ingestion + API index                      |
| Sprint 2 | Retrieval + API retrieve + integration vector store |
| Sprint 3 | Generation + API generate + end-to-end MVP          |

## Rủi ro kỹ thuật

| Rủi ro                                       | Tác động                                        |
| -------------------------------------------- | ----------------------------------------------- |
| Parse đầu vào không ổn định                  | Ingestion thất bại hoặc metadata kém chất lượng |
| Chunking không phù hợp                       | Retrieval kém chính xác                         |
| Embedding model không phù hợp ngôn ngữ       | Chất lượng retrieval thấp                       |
| Vector store filter hỗ trợ hạn chế           | Hành vi filter không nhất quán                  |
| LLM trả citation không ổn định               | Output khó kiểm soát                            |
| LlamaIndex abstraction rò rỉ lên application | Khó thay engine sau này                         |

## Cách giảm rủi ro

- Bắt đầu với input text chuẩn hóa trước, mở rộng parser sau.
- Khóa metadata schema từ đầu.
- Dùng prompt builder deterministic và hậu xử lý citation.
- Viết contract test cho adapter.
- Giữ LlamaIndex trong helper/adapters hạ tầng phía sau application services, không đưa object của nó ra ngoài.
- Chọn 1 bộ dữ liệu mẫu tiếng Việt để đánh giá retrieval sớm ngay từ Sprint 2.
- Giữ chunking strategy đơn giản theo ký tự ở MVP để tránh coupling vào tokenizer/model.
