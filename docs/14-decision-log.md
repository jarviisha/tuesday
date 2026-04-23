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
| `DL-002` | `accepted` | `Indexer`, `Retriever`, `Generator` là service nội bộ gần với capability, không phải port lõi | Tránh over-engineer abstraction quá sớm | capability packages, `docs/04-ports-va-adapters.md` |
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
| `DL-015` | `accepted` | Phase 1 `stabilize` được tách thành 3 workstream: `dev_setup_and_commands`, `ci_baseline`, `runbook_config_and_release_baseline` | Giúp chia việc và review implementation sau MVP theo đơn vị nhỏ, kiểm chứng được | docs post-MVP, phase 1 implementation planning, checklist |
| `DL-016` | `accepted` | Phase 2 `operational_hardening` được tách thành 3 workstream: `persistence_and_runtime_wiring`, `integration_resilience_and_error_mapping`, `observability_and_smoke_test` | Giúp Phase 2 bám đúng hardening scope, giao việc rõ và tránh trộn persistence, resilience, observability thành một khối mơ hồ | docs post-MVP, phase 2 planning, checklist |
| `DL-017` | `accepted` | Phase 3 `quality_evaluation` được tách thành 3 workstream: `fixtures_and_golden_cases`, `benchmark_and_baseline_metrics`, `regression_suite_and_result_storage` | Giúp Phase 3 khóa rõ dữ liệu, benchmark và regression thay vì gom chung thành một phase đánh giá mơ hồ | docs post-MVP, phase 3 planning, checklist |
| `DL-018` | `superseded` | Sau post-MVP, full migration cấu trúc `src/tuesday_rag` được **trì hoãn**; chỉ cho phép migration tăng dần khi có trigger kỹ thuật hoặc roadmap rõ ràng | Tránh refactor lớn theo cảm giác khi chưa có bằng chứng lợi ích lớn hơn chi phí delivery | feature expansion planning, architecture migration review, benchmark/regression recheck |
| `DL-019` | `accepted` | Sau Phase 3, repo **chấp nhận full migration** cấu trúc `src/tuesday_rag` theo hướng capability-oriented để scale ownership và mở rộng feature dễ hơn; migration này phải đi trước hoặc cùng lúc với feature expansion đầu tiên, nhưng phải bám boundary thực tế của codebase thay vì ép tách cơ học mọi concern thành module độc lập | Team đã có baseline vận hành, hardening và benchmark đủ để đo regress, nên chi phí migration lớn nay được chấp nhận để đổi lấy khả năng scale cấu trúc dài hạn mà vẫn giữ refactor trong biên an toàn của contract và coupling hiện có | feature expansion planning, architecture migration, benchmark/regression recheck, docs post-MVP |
| `DL-020` | `accepted` | Feature đầu tiên của Phase 4 là `internal file ingestion` qua entrypoint nội bộ, triển khai cùng nhịp hoàn tất migration capability-oriented hiện tại; không mở endpoint HTTP công khai mới trong nhịp này | Đây là hướng mở rộng có giá trị cao nhất nhưng vẫn bám ưu tiên mặc định sau MVP, tận dụng boundary `DocumentParser` đã có và mở rộng ingestion mà không làm lệch contract công khai của MVP | phase 4 planning, ingestion capability, migration verification, runbook và test |
| `DL-021` | `accepted` | Sau khi `internal file ingestion v1` ổn định với `.txt` và `.md`, nhịp mở rộng nhỏ kế tiếp của cùng capability là hỗ trợ `.html` bằng parser hạ tầng tối giản; vẫn không mở endpoint HTTP mới và không thêm dependency parsing nặng | Mở rộng parser theo từng loại file nhỏ giúp tăng giá trị ingestion nội bộ mà vẫn giữ boundary, tránh nhảy sang batching/async hay upload HTTP quá sớm | phase 4 planning, file parser adapters, runbook, tests |
| `DL-022` | `accepted` | Nhịp mở rộng nhỏ kế tiếp sau parser `.html` là batch ingestion nội bộ cho local directory qua script riêng, chỉ xử lý các extension đã hỗ trợ và tiếp tục qua từng file lỗi thay vì fail toàn batch ngay lập tức | Cách này tăng tính hữu dụng vận hành cho ingestion nội bộ mà không kéo scope sang queue, async orchestration hay endpoint công khai mới | phase 4 planning, scripts, runbook, CLI tests |
| `DL-023` | `accepted` | Batch ingestion nội bộ hỗ trợ `--recursive` theo kiểu opt-in; mặc định vẫn chỉ quét level hiện tại để giữ behavior cũ ổn định | Cho phép mở rộng utility theo local directory tree mà không làm đổi semantics command hiện có hoặc làm người dùng bất ngờ khi bật batch trên thư mục lớn | phase 4 planning, scripts, recursive CLI tests, runbook |
| `DL-024` | `accepted` | Parser `.pdf` cho internal ingestion dùng `pdftotext` của hệ thống qua subprocess adapter; nếu tool thiếu hoặc parse thất bại thì map về `DOCUMENT_PARSE_ERROR` | Tận dụng dependency hệ thống có sẵn để thêm giá trị ingestion thực tế mà không kéo thêm thư viện Python hoặc parser layout phức tạp vào repo | phase 4 planning, file parser adapters, runbook, tests |
| `DL-025` | `accepted` | Batch ingestion nội bộ hỗ trợ `--output` để lưu summary JSON ra file; command vẫn tiếp tục in summary ra `stdout` để giữ backward compatibility | Giữ trải nghiệm CLI cũ ổn định nhưng bổ sung artifact hữu ích cho review batch run, debugging và lưu kết quả thủ công | phase 4 planning, scripts, runbook, CLI tests |
| `DL-026` | `accepted` | Batch ingestion nội bộ hỗ trợ `--include` và `--exclude` theo glob pattern trên relative path; filter `exclude` thắng cuối cùng | Giúp người vận hành khoanh đúng tập file cần index mà không phải đổi cấu trúc thư mục hay tạo script ad-hoc, đồng thời giữ batch utility ở mức đơn giản | phase 4 planning, scripts, runbook, CLI tests |
| `DL-027` | `accepted` | Batch ingestion nội bộ hỗ trợ `--dry-run` để preview candidate files và `document_id` mà không ghi vào vector store | Giúp người vận hành kiểm tra trước phạm vi batch, pattern filter và document id mapping với chi phí thấp, không tạo side effect | phase 4 planning, scripts, runbook, CLI tests |
| `DL-028` | `accepted` | Chương `post-mvp` được coi là đã hoàn tất sau khi đủ 4 phase nền và nhịp đầu tiên của `feature_expansion`; các spec tiếp theo phải chuyển sang một track tài liệu mới thay vì tiếp tục mở rộng `docs/post-mvp/` | Giữ ranh giới roadmap rõ, tránh kéo dài vô hạn chương post-MVP và buộc các nhịp tiếp theo phải có mục tiêu mới tập trung hơn vào phần lõi của hệ thống | planning, decision log, closeout docs, track `core` |

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
