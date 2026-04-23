# 20. Kế Hoạch Triển Khai Sau MVP

## Mục lục

- Thứ tự triển khai
- Phase 1
- Phase 2
- Phase 3
- Phase 4
- Deliverable theo phase
- Rủi ro
- Cách giảm rủi ro

## Thứ tự triển khai

Thứ tự đề xuất:

1. Khóa baseline vận hành và test của bản MVP hiện tại.
2. Tăng độ bền vận hành trước khi tăng độ rộng tính năng.
3. Thiết lập baseline chất lượng retrieval/generation.
4. Chỉ sau đó mới mở rộng feature theo nhu cầu thật.

## Phase 1

Mục tiêu:

- hoàn tất `stabilize`

Phạm vi:

- chuẩn hóa setup dev
- chuẩn hóa lint/test/run commands
- thêm CI tối thiểu
- viết runbook local/staging
- kiểm tra lại logging và runtime config

Deliverable:

- baseline nội bộ chạy được lặp lại
- CI xanh cho lint và test cốt lõi
- tài liệu setup/running ngắn gọn

## Phase 2

Mục tiêu:

- hoàn tất `operational_hardening`

Phạm vi:

- thay dần adapter demo bằng thành phần bền hơn
- bổ sung persistence
- thêm timeout/retry/error handling
- tăng observability cho failure path
- thêm smoke test cho luồng chính

Workstreams:

1. `persistence_and_runtime_wiring`
2. `integration_resilience_and_error_mapping`
3. `observability_and_smoke_test`

Deliverable:

- hệ thống không còn phụ thuộc hoàn toàn vào in-memory state
- có smoke test `index -> retrieve -> generate`
- có tài liệu cấu hình theo môi trường

## Phase 3

Mục tiêu:

- hoàn tất `quality_evaluation`

Phạm vi:

- khóa fixture/golden cases sau MVP
- tạo benchmark nhỏ
- đo retrieval quality, grounding, citation correctness
- đo latency cơ bản

Deliverable:

- baseline metric đầu tiên
- regression suite cho behavior nhạy cảm
- tài liệu benchmark và kết quả gốc

## Phase 4

Mục tiêu:

- mở rộng feature theo nhu cầu thật trên layout đã migrate

Phạm vi:

- hoàn tất migration theo `40-spec-quyet-dinh-migration-cau-truc-src.md` và `41-spec-target-layout-migration-phase-4.md` ở mức đủ làm nền cho nhịp feature đầu tiên
- triển khai feature đầu tiên đã được ưu tiên: `internal file ingestion` qua entrypoint nội bộ
- giữ nguyên 3 endpoint HTTP hiện tại và không mở thêm public contract mới trong nhịp này
- viết verification cho migration và feature mới mà không phá baseline hiện có

Deliverable:

- feature `internal file ingestion` đầu tiên sau MVP được ship có kiểm soát
- benchmark hoặc test chứng minh feature không làm regress behavior lõi
- layout `src/tuesday_rag` mới đủ ổn để feature đầu tiên có thể phát triển tiếp trên đó mà vẫn bám guardrail và boundary thực tế của codebase

Trạng thái hiện tại:

- Phase 4 nhịp đầu đã hoàn tất với `internal file ingestion` nội bộ cho `.txt`, `.md`, `.html`, `.pdf`
- batch CLI nội bộ đã có `--recursive`, `--output`, `--include`, `--exclude`, `--dry-run`
- verification đã được khóa bằng unit test, integration test, smoke test và regression suite

## Deliverable theo phase

| Phase | Deliverable chính                                   |
| ----- | --------------------------------------------------- |
| 1     | Baseline dev/test/release nội bộ ổn định            |
| 2     | Persistence + hardening + smoke test vận hành       |
| 3     | Baseline chất lượng và regression suite             |
| 4     | Feature mở rộng đầu tiên có spec và benchmark riêng |

## Rủi ro

| Rủi ro                                      | Tác động                                                  |
| ------------------------------------------- | --------------------------------------------------------- |
| Mở rộng feature quá sớm                     | đội mất tập trung, khó xác định lỗi do nền hay do feature |
| Thay adapter thật nhưng không có smoke test | lỗi tích hợp lọt qua review                               |
| Không có baseline benchmark                 | tuning theo cảm giác, dễ regress retrieval/generation     |
| Logging/metrics yếu                         | khó phân biệt lỗi dữ liệu, lỗi provider, lỗi ứng dụng     |
| Persistence mới làm lệch semantics cũ       | vi phạm contract hoặc policy re-index                     |

## Cách giảm rủi ro

- Khóa rõ thứ tự phase và chỉ lệch khi có decision mới.
- Mọi thay đổi adapter phải có integration test hoặc smoke test tương ứng.
- Thiết lập benchmark nhỏ sớm thay vì chờ đủ dữ liệu lớn.
- Giữ nguyên semantics cốt lõi của MVP trừ khi có quyết định mới.
- Review riêng các thay đổi liên quan persistence, retry, timeout và error mapping.
