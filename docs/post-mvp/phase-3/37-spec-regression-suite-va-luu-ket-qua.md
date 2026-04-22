# 37. Spec Regression Suite Và Lưu Kết Quả

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Baseline cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Biến các behavior nhạy cảm nhất thành regression suite có thể chạy lại và xác định cách lưu baseline benchmark ban đầu.

## Phạm vi

- chọn các case nhạy cảm cần khóa thành regression suite
- xác định command hoặc target test cho regression suite
- chọn nơi lưu baseline benchmark đầu tiên trong repo
- mô tả cách cập nhật baseline khi behavior thay đổi có chủ đích

## Deliverable

- regression suite hoặc target test rõ ràng
- danh sách các behavior nhạy cảm đang được khóa
- thư mục hoặc file chứa baseline benchmark ban đầu
- quy tắc cập nhật baseline khi có decision mới

## Baseline cần có

Regression suite tối thiểu nên khóa:

- semantics `insufficient_context`
- citation subset correctness
- semantics `tags = contains-any`
- replace policy theo `document_id` trong cùng `index_name`
- ít nhất một case retrieval/generation tiếng Việt quan trọng

Nơi lưu baseline phải rõ:

- nằm trong repo hoặc đường dẫn được tài liệu hóa rõ
- có format dễ diff và review
- đủ metadata để biết benchmark chạy với config nào

## Acceptance criteria

- Có target regression suite đủ ngắn để chạy trước các thay đổi quan trọng.
- Baseline benchmark ban đầu có nơi lưu và cách đọc rõ ràng.
- Khi behavior thay đổi có chủ đích, team biết phải cập nhật những file nào.
- Regression suite không trùng lặp vô nghĩa với toàn bộ test suite hiện có.

## Verification

- Chạy regression suite và xác nhận các behavior nhạy cảm vẫn ổn.
- Kiểm tra nơi lưu baseline đã tồn tại và format đủ đọc được.
- Review lại quy tắc cập nhật baseline với decision log và docs Phase 3.

## Guardrails

- Không biến regression suite thành bản sao toàn bộ test suite.
- Không cập nhật baseline benchmark lặng lẽ khi chưa có lý do hoặc decision rõ.
- Không lưu kết quả baseline theo format khó diff hoặc phụ thuộc công cụ riêng của cá nhân.
