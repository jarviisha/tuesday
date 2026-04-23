# Core Track

Track này chứa các spec sau khi chương `post-mvp` đã đóng.

Mục tiêu của `core` là tập trung vào phần lõi của hệ thống RAG:

- retrieval quality
- generation quality và grounding
- context selection và ranking
- storage/retrieval backend phục vụ cải thiện lõi

Tài liệu hiện có:

- `55-core-track-overview.md`
- `56-spec-retrieval-core-hardening-v1.md`
- `57-spec-provider-integration-and-runtime-lifecycle-v1.md`
- `58-spec-real-vector-store-adapter-v1.md`
- `59-spec-generation-context-policy-v1.md`
- `60-spec-provider-runtime-implementation-v1.md`

Thứ tự ưu tiên hiện tại của track này là:

1. provider thật và env-based selection trong container
2. vector store thật thay cho adapter demo hiện tại
3. chuyển container wiring vào app lifespan
4. đặc tả lại logic `sufficient_context`
5. khóa rõ phụ thuộc `pdftotext` và startup check tùy chọn

`56-spec-retrieval-core-hardening-v1.md` vẫn còn giá trị, nhưng không còn là nhịp implementation đầu tiên của track `core`.
