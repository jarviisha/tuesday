# 54. Closeout Giai Đoạn Post-MVP

## Mục lục

- Mục tiêu
- Trạng thái đóng
- Tóm tắt những gì đã hoàn tất
- Những gì không còn thuộc `post-mvp`
- Nguyên tắc chuyển sang giai đoạn mới
- Tài liệu tham chiếu chính

## Mục tiêu

Tài liệu này chốt lại rằng chương `post-mvp` đã hoàn thành đủ phạm vi đã định, để team có thể chuyển sang bộ spec mới mà không tiếp tục nhồi thêm công việc mới vào cùng một roadmap cũ.

## Trạng thái đóng

Trạng thái hiện tại của `post-mvp`: **đã hoàn tất và có thể đóng như một chương roadmap**.

Điều này có nghĩa là:

- các phase đã định ban đầu đã đi đến trạng thái done đủ dùng
- các checklist chính đã được khóa
- các deliverable nền tảng đã có implementation thật thay vì chỉ còn trên giấy
- các nhịp tiếp theo không cần tiếp tục được mô tả như phần nối dài của `post-mvp`

`post-mvp` vẫn được giữ lại trong repo như hồ sơ lịch sử quyết định, implementation path và verification baseline.

## Tóm tắt những gì đã hoàn tất

### Phase 1: `stabilize`

- đã chuẩn hóa setup dev, lệnh lint, lệnh test và cách chạy API local
- đã có baseline CI hoặc automation tương đương
- đã có runbook cấu hình và release baseline

### Phase 2: `operational_hardening`

- đã thay trạng thái index chỉ-in-memory bằng lựa chọn bền hơn
- đã thêm timeout, retry và error mapping cho các tích hợp chính
- đã có smoke test cho luồng `index -> retrieve -> generate`
- đã tăng observability cho failure path

### Phase 3: `quality_evaluation`

- đã khóa golden cases và benchmark nhỏ
- đã có baseline cho retrieval quality, grounding, citation correctness và latency
- đã có regression suite cho các case quan trọng

### Phase 4: `feature_expansion` nhịp đầu

- đã hoàn tất migration capability-oriented đủ dùng cho nhịp feature đầu tiên
- đã ship `internal file ingestion` nội bộ
- đã hỗ trợ `.txt`, `.md`, `.html`, `.pdf`
- đã có batch CLI với `--recursive`, `--output`, `--include`, `--exclude`, `--dry-run`
- đã khóa verification bằng unit test, integration test, smoke test và regression suite

## Những gì không còn thuộc `post-mvp`

Kể từ mốc này, các hạng mục sau không nên tiếp tục được viết như một phần mở rộng của `docs/post-mvp/`:

- nâng chất lượng lõi của retrieval
- nâng chất lượng lõi của generation và grounding
- thay vector store hoặc retrieval backend để tăng hiệu năng thật
- capability mới không còn mang tính “mở rộng đầu tiên sau MVP”
- roadmap dài hạn sau khi các phase nền đã hoàn tất

Các công việc trên nên đi vào một track tài liệu mới, với mục tiêu, scope và decision riêng.

## Nguyên tắc chuyển sang giai đoạn mới

- Không xóa hoặc làm mờ giá trị của `docs/post-mvp/`; đây là baseline lịch sử đã hoàn tất.
- Chỉ sửa `docs/post-mvp/` khi cần đính chính sai sót hoặc làm rõ lịch sử implementation.
- Mọi spec mới từ đây nên nằm ở track tài liệu mới, thay vì tiếp tục tăng số phase trong `post-mvp`.
- Track mới nên tập trung vào phần lõi của hệ thống RAG, không quay lại pattern “hardening nền + mở rộng tiện ích nhỏ”.

## Tài liệu tham chiếu chính

- `docs/post-mvp/20-ke-hoach-trien-khai-sau-mvp.md`
- `docs/post-mvp/21-checklist-giai-doan-sau-mvp.md`
- `docs/post-mvp/phase-4/53-phase-4-implementation-summary.md`
- `docs/14-decision-log.md`
