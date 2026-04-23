# 17. Tổng Quan Giai Đoạn Sau MVP

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi mặc định
- Giả định kỹ thuật
- Thứ tự ưu tiên
- Nguyên tắc triển khai
- Trạng thái hiện tại

## Mục tiêu

Sau khi public MVP đã đóng scope, mục tiêu của giai đoạn tiếp theo là:

- Ổn định hóa bản hiện tại để team có thể chạy, test, release và demo lặp lại được.
- Tăng mức sẵn sàng vận hành của hệ thống trước khi mở rộng tính năng.
- Thiết lập baseline chất lượng cho retrieval, grounding, citation và độ trễ.
- Chỉ mở rộng feature khi đã có dữ liệu vận hành và benchmark tối thiểu.

## Phạm vi

Giai đoạn sau MVP được chia thành 4 phase:

1. `stabilize`
2. `operational_hardening`
3. `quality_evaluation`
4. `feature_expansion`

Phạm vi của bộ spec này:

- khóa thứ tự ưu tiên giữa các phase
- xác định deliverable, acceptance criteria và verification cho từng phase
- giữ boundary kiến trúc hiện tại trong lúc thay adapter, thêm observability hoặc thêm benchmark
- ngăn việc mở rộng feature quá sớm khi nền vận hành và đánh giá chưa ổn

## Ngoài phạm vi mặc định

Những phần sau không mặc định là blocker ngay sau MVP:

- endpoint HTTP công khai mới
- streaming response cho `/generate`
- async ingestion hoặc queue orchestration
- hybrid retrieval
- reranker
- giao diện chat hoàn chỉnh
- multi-tenant, RBAC, workflow quản trị

Các hạng mục trên chỉ được đưa vào phase thực thi nếu:

- đã hoàn tất `stabilize`
- đã có mức `operational_hardening` tối thiểu
- có lý do nghiệp vụ hoặc dữ liệu benchmark rõ ràng

## Giả định kỹ thuật

- Kiến trúc ports/adapters hiện tại vẫn là ràng buộc chính.
- Public contract của 3 endpoint MVP được giữ ổn định trừ khi có quyết định mới trong decision log.
- Runtime config tiếp tục được nạp một lần khi khởi động ứng dụng.
- Đánh giá chất lượng phase sau MVP ưu tiên dữ liệu tiếng Việt trước.
- Team chấp nhận thêm adapter thật, persistence, CI và metric mà không yêu cầu đổi model nội bộ.

## Thứ tự ưu tiên

Thứ tự ưu tiên được khóa như sau:

1. Làm cho bản hiện tại chạy ổn định trong môi trường dev/staging.
2. Làm cho hệ thống quan sát được và chịu lỗi tốt hơn khi tích hợp hạ tầng thật.
3. Đo được chất lượng retrieval/generation bằng fixture và benchmark nhỏ nhưng ổn định.
4. Chỉ sau đó mới cân nhắc mở rộng tính năng.

## Nguyên tắc triển khai

- Không dùng feature mới để che vấn đề vận hành hoặc chất lượng chưa được đo.
- Mọi thay đổi behavior sau MVP vẫn phải đi kèm test hoặc benchmark thể hiện behavior mới.
- Nếu một thay đổi làm đổi thứ tự ưu tiên giữa các phase, phải ghi decision mới.
- Nếu cần mở rộng feature sớm do yêu cầu nghiệp vụ thật, phải nêu rõ feature đó đang chen vào phase nào và rủi ro gì bị chấp nhận.

## Trạng thái hiện tại

Chương `post-mvp` hiện đã hoàn tất ở mức roadmap đã định và được giữ lại như hồ sơ lịch sử triển khai.

Các spec mới sau mốc này nên chuyển sang track tài liệu riêng, bắt đầu tại:

- `docs/54-closeout-post-mvp.md`
- `docs/core/README.md`
