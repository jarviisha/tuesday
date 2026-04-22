# 14. Decision Log

## Mục lục
- Mục đích
- Cách dùng
- Trạng thái quyết định
- Quyết định đã chốt cho MVP
- Mẫu ghi quyết định mới

## Mục đích

Tài liệu này dùng để khóa các quyết định triển khai có khả năng làm lệch behavior, contract hoặc boundary của hệ thống trong lúc code.

Decision log không thay thế các tài liệu spec chính. Nó chỉ ghi lại:

- quyết định nào đã được chốt
- vì sao chốt như vậy
- quyết định đó ảnh hưởng đến đâu
- khi nào cần cập nhật test hoặc docs liên quan

## Cách dùng

- Mỗi khi phát sinh một quyết định có thể làm thay đổi behavior hoặc cách implement, phải ghi vào đây trước hoặc cùng lúc với code.
- Chỉ ghi các quyết định đủ cụ thể để team khác đọc vào có thể implement giống nhau.
- Nếu một quyết định làm thay đổi API contract, domain semantics, config bounds hoặc adapter boundary, phải cập nhật thêm tài liệu gốc liên quan.
- Không dùng file này để ghi todo mơ hồ hoặc ý tưởng chưa chốt.

## Trạng thái quyết định

| Trạng thái | Ý nghĩa |
|---|---|
| `proposed` | Đang cân nhắc, chưa được coi là spec |
| `accepted` | Đã chốt, team phải bám theo |
| `superseded` | Đã bị thay bởi quyết định mới |

## Quyết định đã chốt cho MVP

| ID | Trạng thái | Quyết định | Lý do | Ảnh hưởng |
|---|---|---|---|---|
| `DL-001` | `accepted` | Re-index policy là `replace-by-document_id-within-index_name` | Giữ semantics đơn giản và deterministic cho MVP | `ingestion`, `VectorStore`, API `/documents/index`, test idempotency |
| `DL-002` | `accepted` | `Indexer`, `Retriever`, `Generator` là composite service ở application, không phải port lõi | Tránh over-engineer abstraction quá sớm | `application/services`, `docs/04-ports-va-adapters.md` |
| `DL-003` | `accepted` | `tags` dùng semantics `contains-any` | Đủ cho MVP và dễ map sang adapter thật hoặc fake | `retrieval`, filter validation, adapter contract test |
| `DL-004` | `accepted` | Khi không có context phù hợp thì application trả `insufficient_context` trực tiếp và không gọi `LLMProvider` | Giữ behavior kiểm soát được, tránh hallucination không cần thiết | `generation`, test nhánh không gọi LLM, API `/generate` |
| `DL-005` | `accepted` | Citation chuẩn tham chiếu theo `chunk_id` và chỉ lấy từ tập `retrieved_chunks` thực tế đã dùng | Giữ traceability rõ và tránh citation bịa | generation output, response schema, test grounding |
| `DL-006` | `accepted` | Chunking MVP dùng cấu hình theo ký tự với `chunk_size = 1000`, `chunk_overlap = 150` trong biên spec | Tránh coupling vào tokenizer hoặc model cụ thể quá sớm | `config`, `chunking`, use case ingestion, tests |
| `DL-007` | `accepted` | Config runtime được nạp một lần khi ứng dụng khởi động và chỉ override trong biên spec | Giữ deploy behavior nhất quán trong từng phiên bản chạy | `config.py`, dependency wiring, runtime validation |
| `DL-008` | `accepted` | Public API MVP chỉ khóa ingestion mode JSON text chuẩn hóa; parser file chỉ là hướng nội bộ hoặc phase sau | Tránh parser file trở thành blocker của sprint đầu | API `/documents/index`, adapter scope, sprint planning |
| `DL-009` | `accepted` | Không log raw content ngoài mức tối thiểu cần cho debug | Giảm rủi ro lộ dữ liệu nhạy cảm | logging, observability, adapter/provider integration |
| `DL-010` | `accepted` | `PARTIAL_INDEXED` không thuộc public MVP hiện tại; adapter MVP mặc định fail toàn phần khi vector store ghi lỗi | Giữ contract HTTP đơn giản, tránh mở rộng orchestration ngoài phạm vi MVP | ingestion, API `/documents/index`, checklist, tests |
| `DL-011` | `accepted` | Invariant có thể được khóa bằng unit test ở domain model và model nội bộ, không bắt buộc phải có layer domain behavior riêng | Codebase hiện dùng dataclass + use case orchestration, nên cần chứng minh invariant bằng test đúng chỗ thay vì ép thêm abstraction | `docs/03`, `docs/09`, checklist, tests |
| `DL-012` | `accepted` | Public MVP được coi là đã đóng scope khi hoàn tất 3 endpoint HTTP, behavior cốt lõi, test contract/use case/integration tối thiểu và logging cơ bản; parser nội bộ, `PARTIAL_INDEXED`, adapter thật là phase sau | Tránh kéo dài vô hạn phạm vi MVP và giúp team chuyển sang phase kế tiếp với ranh giới rõ | sprint plan, checklist, review docs, phase planning |
| `DL-013` | `accepted` | Thứ tự ưu tiên sau MVP là `stabilize -> operational_hardening -> quality_evaluation -> feature_expansion` | Giữ team tập trung vào độ ổn định, khả năng vận hành và baseline đánh giá trước khi mở rộng tính năng | planning sau MVP, checklist, phase specs |
| `DL-014` | `accepted` | Feature mới sau MVP không mặc định là blocker; chỉ được ưu tiên sớm khi có yêu cầu nghiệp vụ hoặc dữ liệu benchmark rõ ràng | Tránh scope creep và tránh dùng feature mới để che vấn đề vận hành/chất lượng chưa được giải quyết | planning sau MVP, spec feature mới, review phạm vi |

## Mẫu ghi quyết định mới

Khi có quyết định mới, ghi theo mẫu:

```md
| `DL-010` | `accepted` | Regex `document_id` là `^[a-zA-Z0-9._-]{1,128}$` | Giảm nhập liệu mơ hồ và dễ dùng làm key kỹ thuật | validator, API contract, tests |
```

Gợi ý những quyết định có thể cần ghi tiếp trong lúc triển khai:

- regex hợp lệ cho `document_id`
- regex hợp lệ cho `index_name`
- source_type whitelist cụ thể cho MVP
- strategy kỹ thuật để adapter vector store thực thi replace policy
- literal mặc định cho response `insufficient_context`
