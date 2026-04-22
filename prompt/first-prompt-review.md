Bạn là một staff engineer kiêm software architect reviewer.

Bối cảnh:
Trong repository hiện tại đã có một bộ tài liệu đặc tả kỹ thuật bằng tiếng Việt cho dự án MVP RAG core dùng:

- Python
- FastAPI
- LlamaIndex
- cloud embedding model
- cloud LLM
- kiến trúc ports/adapters
- hướng Spec-Driven Development + TDD

Nhiệm vụ của bạn:
Hãy review chéo toàn bộ bộ tài liệu trong thư mục docs/ để đảm bảo chúng:

1. nhất quán với nhau
2. không mâu thuẫn
3. đủ cụ thể để bắt đầu code
4. không bị framework-coupling quá mức
5. phù hợp cho MVP, không over-engineer
6. hỗ trợ tốt cho TDD

Mục tiêu đầu ra:

- không viết code ứng dụng
- chỉ review, chỉnh sửa tài liệu nếu cần
- tạo thêm tài liệu review/checklist nếu cần
- mọi nội dung phải bằng tiếng Việt

Các file cần review:

- docs/01-tong-quan-du-an.md
- docs/02-kien-truc-tong-the.md
- docs/03-domain-model.md
- docs/04-ports-va-adapters.md
- docs/05-use-case-ingestion.md
- docs/06-use-case-retrieval.md
- docs/07-use-case-generation.md
- docs/08-api-contract.md
- docs/09-test-strategy.md
- docs/10-ke-hoach-trien-khai-theo-sprint.md
- docs/11-glossary.md

Yêu cầu review chi tiết:

A. Review tính nhất quán

- kiểm tra tên domain model có thống nhất giữa các file không
- kiểm tra tên port/interface có thống nhất không
- kiểm tra API request/response có khớp với domain model và use case không
- kiểm tra acceptance criteria có khớp với test strategy không
- kiểm tra thuật ngữ trong glossary có khớp với phần còn lại không
- kiểm tra kiến trúc tổng thể có khớp với use case và sprint plan không

B. Review tính đầy đủ

- có thiếu use case quan trọng nào không
- có thiếu error cases quan trọng nào không
- có thiếu validation rules quan trọng nào không
- có thiếu metadata field quan trọng nào không
- có thiếu boundary giữa application và infrastructure không
- có thiếu quy tắc grounding / citations / insufficient context không

C. Review mức độ phù hợp với MVP

- có phần nào over-engineer không
- có phần nào nên hoãn sang phase sau không
- có phần nào chưa đủ để triển khai MVP không
- có phần nào nên đơn giản hóa để phù hợp sprint đầu không

D. Review khả năng hỗ trợ TDD

- use case đã đủ cụ thể để viết test trước chưa
- API contract đã đủ rõ để viết API test chưa
- port/interface đã đủ rõ để mock chưa
- acceptance criteria có đo được không
- test strategy có thực thi được không

E. Review coupling với LlamaIndex / provider

- có chỗ nào business logic phụ thuộc trực tiếp vào LlamaIndex không
- có chỗ nào domain model bị leak framework type không
- có chỗ nào contract bị phụ thuộc provider cloud cụ thể quá mức không
- có chỗ nào cần trừu tượng hóa lại để đổi engine sau này dễ hơn không

Cách làm:

1. Đọc toàn bộ thư mục docs/
2. Tạo một báo cáo review tổng hợp tại:
   - docs/12-review-tong-hop.md
3. Nếu phát hiện vấn đề nhỏ và rõ ràng, hãy chỉnh trực tiếp trong file liên quan
4. Nếu phát hiện vấn đề lớn hoặc mơ hồ, ghi rõ trong báo cáo review thay vì đoán
5. Tạo thêm một checklist review cuối tại:
   - docs/13-checklist-truoc-khi-code.md

Nội dung bắt buộc của docs/12-review-tong-hop.md:

- Tóm tắt chất lượng bộ tài liệu hiện tại
- Điểm mạnh
- Điểm chưa ổn
- Các mâu thuẫn phát hiện được
- Các điểm thiếu
- Các điểm over-engineer
- Các điểm cần làm rõ trước khi code
- Đề xuất thứ tự review thủ công của con người
- Kết luận: bộ tài liệu đã sẵn sàng để code hay chưa

Nội dung bắt buộc của docs/13-checklist-truoc-khi-code.md:

- Checklist kiến trúc
- Checklist domain model
- Checklist API contract
- Checklist use case
- Checklist TDD/testability
- Checklist adapter boundaries
- Checklist MVP scope
- Checklist dữ liệu mẫu/test data

Tiêu chí review:

- Ưu tiên tính thực dụng
- Ưu tiên khả năng triển khai thật
- Ưu tiên tính nhất quán giữa tài liệu
- Không thêm complexity không cần thiết
- Không biến MVP thành production full-scale

Nguyên tắc chỉnh sửa:

- Giữ văn phong tiếng Việt rõ ràng, kỹ thuật
- Không viết lại toàn bộ nếu không cần
- Ưu tiên chỉnh các mâu thuẫn và khoảng trống
- Nếu thay đổi tên model/port/contract, phải sửa đồng bộ ở tất cả file liên quan

Đầu ra cuối cùng:

1. Cập nhật các file docs nếu cần
2. Tạo docs/12-review-tong-hop.md
3. Tạo docs/13-checklist-truoc-khi-code.md
4. In ra:
   - danh sách file đã chỉnh
   - các vấn đề còn mở
   - 5 quyết định kiến trúc cần chốt trước khi bắt đầu code
   - đề xuất bước tiếp theo

Lưu ý rất quan trọng:

- chưa viết code
- chưa sinh test file
- chỉ review, chuẩn hóa, và bổ sung tài liệu review/checklist
- mọi nội dung phải bằng tiếng Việt
