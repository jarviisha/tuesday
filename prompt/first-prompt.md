Bạn là một kỹ sư phần mềm kiêm solution architect senior.

Nhiệm vụ:
Hãy xây dựng bộ tài liệu phân tích và đặc tả cho một dự án RAG core theo hướng Spec-Driven Development + TDD, viết hoàn toàn bằng tiếng Việt, rõ ràng, chuyên nghiệp, dễ dùng cho team kỹ thuật triển khai.

Bối cảnh dự án:
Tôi đang xây dựng MVP cho một hệ thống RAG core làm nền cho chatbot doanh nghiệp.
Hệ thống dùng:

- Python
- FastAPI
- LlamaIndex
- Cloud embedding model
- Cloud LLM
- Vector store có thể thay đổi sau này
- Kiến trúc theo hướng ports/adapters để tránh lock-in

Mục tiêu của tài liệu:

1. Chốt rõ phạm vi MVP
2. Chốt kiến trúc tổng thể
3. Chốt boundary giữa ingestion / retrieval / generation
4. Chốt domain model và interface
5. Chốt API contract
6. Chốt use case behavior
7. Chốt test strategy theo TDD
8. Tạo nền tảng để sau đó Codex có thể code theo đúng spec

Yêu cầu cực kỳ quan trọng:

- Chỉ tạo tài liệu, chưa viết code triển khai
- Tất cả nội dung phải bằng tiếng Việt
- Viết theo giọng kỹ thuật, ngắn gọn, rõ ràng, có cấu trúc
- Không giải thích lan man
- Nếu có chỗ chưa chắc, hãy nêu giả định rõ ràng
- Tài liệu phải thực dụng, phục vụ triển khai MVP thật
- Kiến trúc phải ưu tiên modular, dễ mở rộng, nhưng không over-engineer
- LlamaIndex chỉ nên được mô tả như engine/adaptor layer, không để business logic phụ thuộc trực tiếp
- Mọi object framework-specific phải được map về domain model nội bộ

Hãy tạo các file tài liệu sau trong thư mục docs/:

1. docs/01-tong-quan-du-an.md
   Nội dung cần có:

- Mục tiêu dự án
- Phạm vi MVP
- Ngoài phạm vi
- Các giả định kỹ thuật
- Các ràng buộc kiến trúc
- Các nguyên tắc thiết kế

2. docs/02-kien-truc-tong-the.md
   Nội dung cần có:

- Kiến trúc tổng thể MVP
- Các thành phần chính
- Hot path và non-hot path
- Vai trò của FastAPI, LlamaIndex, vector store, cloud LLM, cloud embedding
- Luồng online và luồng offline
- Hướng mở rộng sau MVP

3. docs/03-domain-model.md
   Nội dung cần có:

- Danh sách domain model cốt lõi
- Mô tả từng model
- Thuộc tính của từng model
- Các invariant / rule quan trọng
- Metadata schema cho chunk
- Mối quan hệ giữa các model

Phải bao gồm tối thiểu:

- SourceDocument
- Chunk
- IndexedChunk
- RetrievedChunk
- RetrievalRequest
- RetrievalResponse
- GenerationRequest
- GeneratedAnswer
- DocumentIndexResult

4. docs/04-ports-va-adapters.md
   Nội dung cần có:

- Giải thích cách áp dụng ports/adapters cho dự án
- Boundary giữa application và infrastructure
- Danh sách interface/port cần có
- Trách nhiệm của từng port
- Adapter nào dùng LlamaIndex
- Adapter nào dùng cloud provider
- Nguyên tắc thay thế engine

Phải bao gồm tối thiểu:

- EmbeddingProvider
- LLMProvider
- VectorStore
- DocumentParser
- Chunker
- Indexer
- Retriever
- Generator

5. docs/05-use-case-ingestion.md
   Nội dung cần có:

- Mục tiêu use case ingestion
- Input / output
- Luồng xử lý chi tiết
- Validation rules
- Error cases
- Definition of done
- Test cases mức use case

6. docs/06-use-case-retrieval.md
   Nội dung cần có:

- Mục tiêu use case retrieval
- Input / output
- Luồng xử lý chi tiết
- Metadata filtering
- top_k behavior
- Error cases
- Definition of done
- Test cases mức use case

7. docs/07-use-case-generation.md
   Nội dung cần có:

- Mục tiêu use case generation
- Input / output
- Luồng xử lý chi tiết
- Quy tắc build prompt
- Quy tắc grounding
- Quy tắc citations
- Hành vi khi context không đủ
- Error cases
- Definition of done
- Test cases mức use case

Generation spec phải nêu rõ:

- chỉ trả lời dựa trên retrieved context
- không được bịa giá, chính sách, cam kết
- nếu không đủ dữ liệu thì phải nói rõ
- citations phải tham chiếu chunk ids

8. docs/08-api-contract.md
   Nội dung cần có:

- Danh sách endpoint MVP
- Request/response schema
- Validation rules
- Error response
- Ví dụ request/response

Phải có tối thiểu:

- POST /documents/index
- POST /retrieve
- POST /generate

9. docs/09-test-strategy.md
   Nội dung cần có:

- Chiến lược TDD cho dự án
- Unit test vs use case test vs integration test vs API test
- Những phần nào nên mock
- Những phần nào không nên mock
- Test pyramid đề xuất
- Test data strategy
- Acceptance criteria theo từng giai đoạn

10. docs/10-ke-hoach-trien-khai-theo-sprint.md
    Nội dung cần có:

- Thứ tự triển khai
- Sprint 1 làm gì
- Sprint 2 làm gì
- Sprint 3 làm gì
- Deliverable mỗi sprint
- Rủi ro kỹ thuật
- Cách giảm rủi ro

11. docs/11-glossary.md
    Nội dung cần có:

- Giải thích các thuật ngữ chính bằng tiếng Việt
- Ví dụ: RAG, chunk, embedding, retrieval, reranker, grounding, citation, hot path, adapter, port, vector store

Định dạng yêu cầu:

- Mỗi file là markdown
- Có tiêu đề, mục lục ngắn, các section rõ ràng
- Dùng bullet points vừa đủ
- Ưu tiên bảng khi mô tả schema, contract, test matrix
- Văn phong kỹ thuật, dễ đọc
- Không dùng tiếng Anh khi đã có từ tiếng Việt phù hợp, trừ tên kỹ thuật bắt buộc

Nguyên tắc nội dung:

- Tài liệu phải đủ cụ thể để lập trình viên khác có thể code theo
- Không phụ thuộc trực tiếp vào object model của LlamaIndex
- Không over-spec những phần chưa cần cho MVP
- Mọi behavior quan trọng phải có acceptance criteria hoặc test cases đi kèm
- Nếu cần giả định, ghi rõ mục "Giả định"

Đầu ra mong muốn:

1. Tạo đầy đủ các file markdown trong thư mục docs/
2. Mỗi file có nội dung hoàn chỉnh
3. Sau khi tạo xong, in ra:
   - cây thư mục docs/
   - tóm tắt ngắn từng file
   - các giả định còn mở
   - đề xuất file nào nên được review trước khi bắt đầu code

Cách làm:

- Bắt đầu bằng việc đề xuất ngắn một outline tổng thể
- Sau đó tạo lần lượt từng file
- Giữ tính nhất quán giữa các tài liệu
- Cuối cùng tự rà soát chéo để đảm bảo tên model, tên port, API contract, use case và test strategy không mâu thuẫn nhau

Lưu ý:

- Chưa viết code
- Chưa sinh test file
- Chỉ tạo tài liệu đặc tả và kế hoạch kỹ thuật

Hãy viết tài liệu như thể đây là tài liệu nội bộ để team kỹ thuật review và triển khai ngay.
Ưu tiên specificity hơn là diễn giải dài.
Mỗi use case phải có:

- input
- output
- luồng xử lý
- error cases
- acceptance criteria
- test cases mức use case

Mỗi API phải có:

- request schema
- response schema
- validation rules
- error cases
- ví dụ request/response
