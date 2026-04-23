# 55. Core Track Overview

## Mục lục

- Bối cảnh
- Mục tiêu
- Phạm vi
- Ngoài phạm vi mặc định
- Ưu tiên triển khai hiện tại
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

## Ưu tiên triển khai hiện tại

Sau khi rà lại codebase hiện tại, track `core` ưu tiên theo thứ tự sau:

1. thêm provider thật cho `EmbeddingProvider` và `LLMProvider`, với chọn adapter theo env trong container
2. thay vector store demo hiện tại bằng adapter thật như `Qdrant` hoặc `pgvector`, nhưng phải khóa semantics `filters`, `score ordering` và `replace-by-document_id`
3. chuyển container vào app lifespan thay vì khởi tạo ở import-time
4. thay heuristic `_has_sufficient_context` bằng logic được đặc tả rõ hoặc delegate sang prompt/LLM khi đã có provider thật
5. khóa rõ phụ thuộc hệ thống `pdftotext` trong README và cân nhắc startup check tùy chọn cho PDF ingestion

Lý do của thứ tự này là:

- contract và boundary chính của hệ thống đã sẵn sàng cho adapter thật
- tốc độ và tính thực dụng của hệ thống hiện tại bị chặn nhiều hơn bởi adapter demo và wiring runtime, không chỉ bởi heuristic retrieval
- việc nâng retrieval quality sâu hơn sẽ đáng tin hơn sau khi runtime/provider/store đã sát production hơn

## Workstream đề xuất

Track `core` ban đầu nên được chia thành các workstream sau:

1. `provider_integration_and_runtime_lifecycle`
2. `real_vector_store_adapter`
3. `generation_context_policy`
4. `retrieval_core_hardening`

Nhịp đầu tiên được đề xuất là `provider_integration_and_runtime_lifecycle`, sau đó là `real_vector_store_adapter`.

## Acceptance criteria của track

Một nhịp trong `core` chỉ được coi là done khi:

- có spec và decision rõ cho behavior mới
- có benchmark hoặc regression thể hiện thay đổi ở phần lõi
- không làm lệch public contract nếu chưa có decision mới
- tài liệu phản ánh đúng implementation thật
