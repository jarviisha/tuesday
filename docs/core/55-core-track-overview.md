# 55. Core Track Overview

## Mục lục

- Bối cảnh
- Mục tiêu
- Phạm vi
- Ngoài phạm vi mặc định
- Workstream đề xuất
- Acceptance criteria của track

## Bối cảnh

Sau khi chương `post-mvp` đã hoàn tất, repo không còn ở trạng thái thiếu baseline vận hành, thiếu benchmark hay thiếu utility nội bộ tối thiểu. Vì vậy, giai đoạn kế tiếp nên chuyển trọng tâm sang phần lõi của hệ thống RAG thay vì tiếp tục mở rộng utility xung quanh.

Track `core` được tạo ra để làm đúng việc đó.

## Mục tiêu

- nâng chất lượng retrieval trên benchmark hiện có
- nâng chất lượng grounding và citation của generation
- giảm các quyết định heuristic quá mong manh trong phần lõi
- chuẩn bị đường đi cho backend retrieval/store bền hơn nếu benchmark chứng minh cần thiết

## Phạm vi

Các hạng mục phù hợp với track này gồm:

- ranking, filtering, chunk selection và retrieval policy
- cải thiện prompt grounding hoặc cách chọn context cho generation
- thay hoặc mở rộng adapter storage/retrieval để phục vụ mục tiêu chất lượng hoặc hiệu năng lõi
- benchmark và regression mới gắn trực tiếp với behavior lõi

## Ngoài phạm vi mặc định

Các hạng mục sau không nên là ưu tiên mặc định của track `core`:

- endpoint HTTP công khai mới
- giao diện người dùng
- workflow quản trị
- parser file mới chỉ vì tiện ích vận hành
- utility CLI nhỏ lẻ không tác động trực tiếp đến retrieval hoặc generation quality

## Workstream đề xuất

Track `core` ban đầu nên được chia thành các workstream sau:

1. `retrieval_core_hardening`
2. `generation_core_hardening`
3. `retrieval_backend_upgrade` nếu benchmark chứng minh adapter hiện tại là bottleneck thật

Nhịp đầu tiên được đề xuất là `retrieval_core_hardening`.

## Acceptance criteria của track

Một nhịp trong `core` chỉ được coi là done khi:

- có spec và decision rõ cho behavior mới
- có benchmark hoặc regression thể hiện thay đổi ở phần lõi
- không làm lệch public contract nếu chưa có decision mới
- tài liệu phản ánh đúng implementation thật
