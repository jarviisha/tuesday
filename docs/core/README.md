# Core Track

Track này chứa các spec sau khi chương `post-mvp` đã đóng.

Mục tiêu của `core` là tập trung vào phần lõi của hệ thống RAG:

- retrieval quality
- generation quality và grounding
- context selection và ranking
- storage/retrieval backend phục vụ cải thiện lõi

Tài liệu hiện có:

- `55-core-track-overview.md`
- `56-spec-retrieval-core-hardening-v1.md` — `proposed`
- `57-spec-provider-integration-and-runtime-lifecycle-v1.md` — `accepted` (`2026-04-23`)
- `58-spec-real-vector-store-adapter-v1.md` — `accepted` (`2026-04-23`), nhịp đang mở (`Qdrant` + selective LlamaIndex adoption trong `infrastructure/`)
- `59-spec-generation-context-policy-v1.md` — `proposed`
- `60-spec-provider-runtime-implementation-v1.md` — `accepted` (`2026-04-23`)

Thứ tự ưu tiên hiện tại của track này là:

1. ~~provider thật và env-based selection trong container~~ — đã xong
2. vector store thật `Qdrant` thay cho adapter demo hiện tại, với selective LlamaIndex adoption trong `infrastructure/` — đang mở
3. ~~chuyển container wiring vào app lifespan~~ — đã xong
4. đặc tả lại logic `sufficient_context`
5. ~~khóa rõ phụ thuộc `pdftotext` và startup check tùy chọn~~ — đã xong

`56-spec-retrieval-core-hardening-v1.md` vẫn còn giá trị, nhưng đứng sau `58` và `59` trong thứ tự nhịp core.
