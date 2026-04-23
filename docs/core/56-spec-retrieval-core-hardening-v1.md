# 56. Spec Retrieval Core Hardening v1

## Trạng thái

`proposed`

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Giả thuyết kỹ thuật
- Success criteria
- Verification mong muốn

## Mục tiêu

Xác định nhịp đầu tiên để cải thiện phần lõi retrieval của hệ thống trên baseline hiện tại, trước khi mở thêm capability lớn hoặc thay toàn bộ framework.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- ingestion nội bộ đã đủ dùng cho việc đưa dữ liệu thật vào hệ thống
- benchmark và regression đã tồn tại để đo tác động của thay đổi
- retrieval hiện vẫn còn khá tối giản, nên đây là nơi có tiềm năng tăng giá trị lớn nhất cho chất lượng đầu ra

## Phạm vi v1

Nhịp `v1` của `retrieval_core_hardening` nên ưu tiên:

- rà lại scoring và ranking hiện tại
- xác định các heuristic retrieval đang quá đơn giản hoặc quá mong manh
- bổ sung benchmark/regression thể hiện các failure mode retrieval rõ hơn
- chọn một cải tiến retrieval nhỏ nhưng đo được, thay vì nhảy ngay sang framework rewrite

## Ngoài phạm vi v1

- rewrite toàn bộ core sang framework khác
- hybrid retrieval đầy đủ nếu chưa có benchmark chứng minh cần
- reranker phụ thuộc model ngoài nếu chưa có baseline cho vấn đề đang gặp
- đổi public API

## Giả thuyết kỹ thuật

Giả thuyết mở đầu của nhịp này là:

- nút thắt hiện tại nhiều khả năng nằm ở retrieval policy và adapter retrieval/store đơn giản, không chỉ ở prompt generation
- lợi ích lớn nhất trước mắt đến từ việc đo và cải thiện retrieval đúng chỗ, không phải mở thêm utility

Giả thuyết này cần được xác nhận lại bằng benchmark và đọc code trước khi implement.

## Success criteria

- có decision mới khóa hướng retrieval đầu tiên được chọn
- có ít nhất một spec implementation cụ thể hơn từ tài liệu này
- có benchmark hoặc regression mới chứng minh vấn đề retrieval hiện tại
- có implementation plan đủ nhỏ để code trong một nhịp riêng

## Verification mong muốn

- benchmark trước/sau trên golden cases hiện có
- regression test cho failure mode retrieval vừa được nhắm tới
- smoke test hiện có vẫn pass
