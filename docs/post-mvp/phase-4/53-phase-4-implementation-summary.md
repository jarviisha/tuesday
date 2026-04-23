# 53. Phase 4 Implementation Summary

## Mục tiêu

Chốt lại nhịp đầu tiên của Phase 4 theo trạng thái implementation thật, để team có một điểm dừng rõ trước khi mở nhịp feature tiếp theo.

## Kết quả đã hoàn tất

- bỏ compatibility shim không còn cần thiết ở `api/dependencies.py`
- giữ layout capability-oriented hiện tại làm nền chính thức cho feature mới
- thêm internal file ingestion qua `scripts/index_file.py`
- hỗ trợ parser:
  - `.txt`
  - `.md`
  - `.html`
  - `.pdf` qua `pdftotext`
- thêm batch ingestion qua `scripts/index_directory.py`
- harden batch CLI với:
  - `--recursive`
  - `--output`
  - `--include`
  - `--exclude`
  - `--dry-run`
- thêm example assets trong `examples/`
- cập nhật README và runbook để chạy lại toàn bộ flow nội bộ

## Boundary đã giữ nguyên

- không mở endpoint HTTP công khai mới
- không đổi contract của `/documents/index`, `/retrieve`, `/generate`
- không đổi semantics `insufficient_context`, `citations`, `tags = contains-any`
- không làm rò object parser/tool-specific lên application/domain

## Verification đã có

- unit test cho parser, CLI và use case nội bộ
- integration test cho các luồng:
  - `index md -> retrieve -> generate`
  - `index html -> retrieve -> generate`
  - `index pdf -> retrieve -> generate`
- smoke test hiện có vẫn pass
- regression suite hiện có vẫn pass
- benchmark baseline Phase 3 vẫn chạy lại được sau các nhịp cleanup chính

## Định nghĩa done cho Phase 4 nhịp đầu

Phase 4 được coi là đã done ở nhịp đầu tiên khi:

- feature mở rộng đầu tiên đã ship ở mức nội bộ có kiểm soát
- feature đó có giá trị vận hành thực tế, không chỉ là refactor cấu trúc
- codebase vẫn bám guardrail và public contract cũ
- docs, runbook và checklist đã phản ánh đúng implementation hiện tại

Trạng thái hiện tại: **đã đạt mức done cho nhịp đầu Phase 4**.

## Gợi ý cho nhịp tiếp theo

Các hướng tiếp theo nên được tách sang decision/spec mới thay vì tiếp tục mở rộng lẻ trong cùng nhịp:

- parser nâng cao hơn như OCR hoặc layout-aware PDF
- include/exclude semantics phong phú hơn nếu cần thật
- dry-run hoặc reporting cho single-file command
- feature expansion ngoài ingestion, ví dụ retrieval quality hoặc capability mới
