# 30. Spec Integration Resilience Và Error Mapping

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Failure handling baseline
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Khóa baseline chịu lỗi tối thiểu cho các tích hợp ngoài để request không treo vô thời hạn và failure path được phân loại nhất quán.

## Phạm vi

- thêm timeout tối thiểu cho provider/store có I/O ngoài process
- thêm retry ở nơi phù hợp, có giới hạn rõ ràng
- chuẩn hóa error mapping giữa lỗi hạ tầng và domain/API behavior hiện có
- tài liệu hóa điều kiện nào nên retry và điều kiện nào phải fail ngay

## Deliverable

- config timeout cho provider hoặc storage tích hợp ngoài
- chính sách retry tối thiểu cho failure tạm thời
- bảng hoặc tài liệu ngắn mô tả mapping lỗi hạ tầng sang nhóm lỗi quan sát được
- test hoặc integration check cho ít nhất một failure path quan trọng

## Failure handling baseline

Spec này khóa các nguyên tắc sau:

- timeout phải hữu hạn và được cấu hình rõ
- retry chỉ áp dụng cho lỗi tạm thời hoặc timeout có khả năng hồi phục
- retry phải có số lần giới hạn; không retry vô hạn
- lỗi không thể hồi phục do input/config phải fail ngay, không retry
- khi hết retry hoặc timeout, log phải cho biết request đang fail ở provider nào hoặc storage nào

Nếu phase này vẫn còn adapter demo trong một số môi trường, spec phải chỉ rõ:

- behavior resilience nào chỉ áp dụng khi có tích hợp ngoài thật
- behavior nào vẫn phải được kiểm thử bằng fake/integration test

## Acceptance criteria

- Không có request nào phụ thuộc provider/store ngoài process mà có thể treo vô thời hạn vì thiếu timeout.
- Retry policy được giới hạn và có lý do rõ cho từng loại lỗi.
- Error mapping giúp phân biệt tối thiểu lỗi ứng dụng, lỗi storage và lỗi provider.
- Public API contract không bị nới rộng chỉ để lộ lỗi hạ tầng nội bộ.
- Failure path chính có log hoặc metric đủ để điều tra mà không log raw content.

## Verification

- Tạo ít nhất một test hoặc sandbox check mô phỏng timeout/failure của provider hoặc storage.
- Xác nhận timeout dẫn đến kết quả fail có thể quan sát được thay vì treo request.
- Xác nhận retry không áp dụng cho lỗi input hoặc config sai.
- Review lại error mapping ở API để chắc lỗi hạ tầng được phân loại rõ hơn.

## Guardrails

- Không thêm retry mù cho mọi exception.
- Không dùng resilience layer để che lỗi contract hoặc lỗi validation.
- Không thêm field mới vào public response chỉ để lộ chi tiết hạ tầng nội bộ.
- Không làm coupling application/domain với SDK client cụ thể.
