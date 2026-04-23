# 12. Review Tổng Hợp Bộ Tài Liệu

## Tóm tắt chất lượng bộ tài liệu hiện tại

Bộ tài liệu hiện tại có nền tảng tốt cho một MVP RAG core theo hướng ports/adapters, Spec-Driven Development và TDD. Các phần chính đã bao phủ được `ingestion`, `retrieval`, `generation`, API contract và test strategy.

Sau khi rà chéo và chốt các quyết định kiến trúc mở, bộ tài liệu đã nhất quán hơn giữa domain, use case và API contract. Trạng thái hiện tại là:

- Có thể bắt đầu code MVP theo TDD.
- Cần giữ phạm vi sprint đầu đúng spec đã khóa, không nới sang production-grade features.

## Điểm mạnh

- Phân tách lớp rõ giữa API, application, domain và infrastructure.
- Đã giữ được nguyên tắc không làm rò rỉ object của LlamaIndex, vector store hay cloud provider vào domain.
- Domain model bao phủ được các thực thể cốt lõi cho MVP.
- Use case có cấu trúc khá tốt: input, output, validation, error cases, acceptance criteria, test cases.
- API contract đã đủ rõ để bắt đầu viết contract test cho 3 endpoint chính.
- Citation semantics đã được khóa theo `chunk_id` và không cho phép viện dẫn ngoài tập chunk thực tế đã dùng.
- Contract cho nhánh `insufficient_context` đã rõ hơn cả ở behavior lẫn schema phản hồi.
- Test strategy bám đúng tinh thần TDD, ưu tiên use case test và contract test trước integration test.
- Sprint plan hợp lý theo thứ tự `ingestion -> retrieval -> generation`.

## Điểm chưa ổn

- Một số chỗ còn trộn giữa “khả năng hệ thống có thể hỗ trợ” và “public API MVP thực sự khóa gì”.
- Tên contract ở generation trước đó chưa thống nhất giữa domain và API.
- Bộ port/service nội bộ vẫn cần được implement cẩn thận để không trôi boundary khi vào code.
- Các giới hạn input đã được khóa, nhưng vẫn cần map rõ vào config runtime khi triển khai.

## Các mâu thuẫn phát hiện được

- `GenerationRequest` trong domain dùng `retrieval_request`, trong khi API contract trước đó dùng `retrieval`.
  - Đã chỉnh đồng bộ về `retrieval_request`.
- Ingestion use case trước đó nói `content` “có nếu không có file”, nhưng API contract lại chỉ có mode JSON text.
  - Đã chỉnh rõ public API MVP chỉ khóa mode text chuẩn hóa; parser file là hướng nội bộ hoặc phase sau.
- Generation flow trước đó mô tả luôn gọi generator/LLM, trong khi acceptance criteria lại yêu cầu xử lý hợp lệ khi `retrieved_chunks = []`.
  - Đã chỉnh rõ application có thể trả trực tiếp `insufficient_context` mà không cần gọi LLM.
- API `/generate` cho phép bỏ trống `retrieval.query`, trong khi domain `RetrievalRequest.query` là bắt buộc.
  - Đã bổ sung quy tắc mapping: nếu thiếu thì lấy từ `question`.

## Các điểm thiếu

- Thiếu quy tắc validation cụ thể cho một số field:
  - format `document_id`
  - format `index_name`
  - regex ký tự hợp lệ nếu team muốn khóa thêm
- Thiếu quy tắc tách biệt dữ liệu nhạy cảm trong metadata ngoài cảnh báo mức nguyên tắc.
- Thiếu bộ dữ liệu mẫu được khóa thật sự trong repo để dùng chung cho spec review và TDD.

## Các điểm over-engineer

- Bộ port hiện tại có xu hướng dày hơn mức MVP:
  - cần tránh nâng `Indexer`, `Retriever`, `Generator` thành abstraction hạ tầng quá sớm khi chúng đã được chốt là service nội bộ gần capability.
- Parser file đã được nhắc ở nhiều nơi dù public API MVP hiện chỉ khóa JSON text.
- Tài liệu có nói tới nhiều hướng mở rộng hợp lý nhưng cần tránh để đội triển khai “thi công trước cho tương lai”, nhất là:
  - hybrid retrieval
  - reranker
  - queue/batch async
  - evaluation harness đầy đủ

Quyết định đã khóa:

- Giữ các port hạ tầng thật sự cần cho sprint đầu:
  - `EmbeddingProvider`
  - `LLMProvider`
  - `VectorStore`
  - `Chunker`
  - `DocumentParser` nếu có ingestion path nội bộ
- Giữ `Indexer`, `Retriever`, `Generator` như service nội bộ gần capability.
- Re-index policy là `replace-by-document_id-within-index_name`.
- `tags` dùng semantics `contains-any`.
- `version` chỉ để metadata, chưa ảnh hưởng retrieval logic.
- Khi không có context, trả `insufficient_context` trực tiếp và không gọi LLM.
- Chunking của MVP dùng cấu hình theo ký tự: `chunk_size = 1000`, `chunk_overlap = 150`, có min/max và override bằng config runtime.
- Config runtime được nạp khi khởi động ứng dụng và chỉ override trong biên spec.
- Response `insufficient_context` có literal mặc định và không đổi schema.
- Observability tối thiểu của MVP gồm `request_id`, `use_case`, `error_code`, `latency_ms`, không log raw content ngoài mức cần thiết.

## Review theo từng nhóm tiêu chí

### A. Tính nhất quán

- Tên domain model hiện tương đối thống nhất sau khi đã đồng bộ `retrieval_request`.
- Tên thành phần hiện nhất quán hơn sau khi chốt `Indexer`/`Retriever`/`Generator` là service nội bộ gần capability.
- API request/response nhìn chung khớp với use case, trừ một số chỗ đã chỉnh như trên.
- Acceptance criteria và test strategy nhìn chung khớp nhau; phần generation đã tốt hơn sau khi khóa nhánh `insufficient_context`.
- Glossary khớp ở mức thuật ngữ chung, chưa có vấn đề lớn.
- Kiến trúc tổng thể khớp với sprint plan và use case, nhưng ingestion path cho file nên được coi là mở rộng thay vì contract công khai của sprint đầu.

### B. Tính đầy đủ

- 3 use case cốt lõi cho MVP đã có.
- Error cases cơ bản đã đủ để bắt đầu code.
- Validation rules đã đủ để bắt đầu code MVP; phần còn lại chủ yếu là regex/format chi tiết nếu team muốn siết thêm.
- Metadata schema chunk ở mức đủ dùng cho MVP: trace, filter, citation.
- Citation semantics và insufficient-context contract đã đủ rõ để viết test hành vi trước.
- Boundary orchestration và infrastructure đã có; điểm cần giữ là không làm service nội bộ trôi sang vai trò adapter.
- Grounding/citations/insufficient context đã có, và đã rõ hơn sau khi chỉnh nhánh context rỗng.

### C. Mức độ phù hợp với MVP

- Tổng thể phù hợp MVP.
- Phần dễ trượt sang over-engineer là parser file, composite ports, và các hướng mở rộng retrieval.
- Sprint 1 nên bám đúng mode text chuẩn hóa, fake adapters, contract test và use case test.
- Chưa cần tối ưu async ingestion, reranker, hybrid retrieval hay streaming.

### D. Hỗ trợ TDD

- Use case đủ cụ thể để viết test trước ở mức orchestration/capability.
- API contract đủ rõ để viết API test cơ bản.
- Port/interface đủ rõ để fake hoặc mock.
- Acceptance criteria phần lớn đo được.
- Các default/min/max đã được khóa cho `top_k`, `max_context_chunks`, `content`, `query`, `question`, `chunk_size`, `chunk_overlap`.
- Test strategy thực thi được, đặc biệt sau khi chốt nhánh `insufficient_context` không buộc phải gọi LLM.

### E. Coupling với LlamaIndex / provider

- Không thấy business logic bị khóa trực tiếp vào object của LlamaIndex trong domain.
- Domain model chưa bị leak framework type.
- Contract công khai chưa bị phụ thuộc vào provider cloud cụ thể.
- Điểm cần canh là không để adapter LlamaIndex quyết định prompt format, retrieval response format hay citation format ở phía orchestration.

## Các điểm cần làm rõ trước khi code

1. Regex hoặc format hợp lệ cho `document_id` và `index_name` có cần khóa thêm ngay hay không.
2. Adapter vector store thật có hỗ trợ `replace-by-document_id-within-index_name` hiệu quả hay cần chiến lược kỹ thuật riêng.
3. Bộ fixture dữ liệu mẫu nào sẽ là chuẩn chung cho review và TDD.
4. Regex hoặc format hợp lệ cho `document_id` và `index_name` có cần siết thêm ở mức implementation hay không.

## Đề xuất thứ tự review thủ công của con người

1. Review `03-domain-model.md` và `08-api-contract.md` cùng nhau để khóa model công khai và model nội bộ.
2. Review `05/06/07-use-case-*.md` để xác nhận behavior thật sự mong muốn trước khi viết test.
3. Review `04-ports-va-adapters.md` để cắt bớt phần thừa nếu cần, tránh over-engineer.
4. Review `09-test-strategy.md` để khóa bộ test đầu tiên theo sprint.
5. Review `10-ke-hoach-trien-khai-theo-sprint.md` để bảo đảm phạm vi sprint đầu không trượt.

## Kết luận: bộ tài liệu đã sẵn sàng để code hay chưa

Kết luận hiện tại: **đã sẵn sàng để code MVP**.

Đánh giá thực dụng:

- Có thể bắt đầu dựng skeleton dự án, domain model, validator, use case test, API contract test và adapter MVP.
- Các điểm còn lại là tinh chỉnh triển khai, không còn là blocker ở mức spec.

Với các quyết định vừa được khóa, bộ tài liệu này đủ tốt để bắt đầu code theo TDD mà không cần viết lại toàn bộ spec.

## Trạng thái sau triển khai MVP

Trạng thái mới: **public MVP đã được triển khai và có thể đóng scope**.

Phạm vi được coi là đã hoàn tất:

- ingestion qua JSON text
- retrieval qua logical index với filter MVP
- generation grounded với citation theo `chunk_id`
- config runtime trong biên spec
- logging tối thiểu cho request lifecycle
- bộ test cốt lõi cho public contract và behavior chính

Các hạng mục vẫn để phase sau nhưng không còn là blocker của việc đóng MVP:

- parser file cho ingestion path nội bộ
- `PARTIAL_INDEXED`
- adapter thật cho cloud/vector store
- siết thêm regex cho `document_id` và `index_name` nếu team muốn
