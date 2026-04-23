# History Archive

Thư mục này lưu **hồ sơ quá trình triển khai** — spec, checklist, runbook, implementation summary và journey docs đã hoàn tất nhiệm vụ của chúng. Không phải nguồn sự thật cho hành vi hiện tại của hệ thống.

## Khi nào đọc các file ở đây

- Khi cần biết **vì sao** một quyết định đã được chốt trong quá khứ (bổ sung cho `docs/14-decision-log.md`).
- Khi cần tham chiếu implementation path của một phase đã đóng để so sánh hoặc tái sử dụng.
- Khi cần verification baseline của một deliverable đã ship (checklist, runbook, test coverage lịch sử).

## Khi nào **không** đọc các file ở đây

- Khi muốn biết hệ thống hiện tại hoạt động ra sao — dùng `docs/00-core-brief.md` và `docs/01..09, 11, 15, 16`.
- Khi đang triển khai task hiện tại — nguồn rule hiện hành ở `docs/` root và `docs/core/`.
- Để lấy path/command/env var hiện tại — README và `docs/00-core-brief.md` là canonical.

## Nguyên tắc chỉnh sửa

- Chỉ sửa khi cần đính chính sai sót hoặc làm rõ lịch sử.
- Không dùng nơi này để mở rộng spec mới — spec mới đi vào `docs/core/` hoặc `docs/` root.
- Không đổi path của các file ở đây tuỳ tiện; nhiều decision log entry và commit reference vào đúng tên file.

## Nội dung

### Journey MVP core

- `10-ke-hoach-trien-khai-theo-sprint.md` — kế hoạch sprint 1/2/3 cho MVP
- `12-review-tong-hop.md` — review chéo bộ tài liệu trước khi code
- `13-checklist-truoc-khi-code.md` — checklist tiền triển khai MVP

### Journey post-MVP

- `54-closeout-post-mvp.md` — chốt đóng chương post-MVP
- `post-mvp/17..21` — overview, spec, checklist post-MVP
- `post-mvp/40, 41` — migration structure spec (đã hoàn tất)
- `post-mvp/phase-1/` — stabilize
- `post-mvp/phase-2/` — operational hardening
- `post-mvp/phase-3/` — quality evaluation
- `post-mvp/phase-4/` — feature expansion (internal file ingestion)

## Trỏ về track hiện hành

- Entry point cho session hiện tại: [`../00-core-brief.md`](../00-core-brief.md)
- Decision log (sống chung với spec hiện hành): [`../14-decision-log.md`](../14-decision-log.md)
- Track đang mở: [`../core/`](../core/)
