# 44. Checklist Phase 4 Feature Expansion

## Checklist định hướng

- [x] Đã chốt feature đầu tiên của Phase 4 là `internal file ingestion`.
- [x] Đã chốt nhịp đầu không mở endpoint HTTP công khai mới.
- [x] Đã gắn feature đầu tiên với migration docs `40` và `41`.
- [x] Đã mở rộng phạm vi Phase 4 từ `txt/md` ban đầu sang bộ file ingestion nội bộ hoàn chỉnh hơn mà vẫn không đổi public API.

## Checklist migration completion

- [x] Composition root và runtime wiring không còn phụ thuộc shim dài hạn không cần thiết.
- [x] Import graph của feature mới bám đúng `runtime/` và capability packages.
- [x] Không có object parser/framework-specific rò lên application/domain.
- [x] Regression và benchmark quan trọng đã được chạy lại sau cleanup chính.

## Checklist internal file ingestion

- [x] Có entrypoint nội bộ rõ ràng để index file.
- [x] Có parser `.txt`.
- [x] Có parser `.md`.
- [x] Có parser `.html` theo spec mở rộng đã chốt.
- [x] Có parser `.pdf` theo spec mở rộng đã chốt.
- [x] Có batch entrypoint cho local directory.
- [x] Có batch CLI với `--recursive`.
- [x] Có batch CLI với `--output`.
- [x] Có batch CLI với `--include` và `--exclude`.
- [x] Có batch CLI với `--dry-run`.
- [x] Có validation cho file không tồn tại hoặc extension không hỗ trợ.
- [x] Có semantics re-index giống ingestion hiện tại.
- [x] Không đổi contract của `/documents/index`.

## Checklist verification

- [x] Có unit test cho parser và use case nội bộ.
- [x] Có integration test cho luồng `index file -> retrieve -> generate`.
- [x] Smoke test hiện có vẫn pass.
- [x] Regression suite hiện có vẫn pass.
- [x] Runbook hoặc command example đã được cập nhật.

## Điều kiện done của nhịp đầu Phase 4

- [x] Team có thể index file `.txt`, `.md`, `.html`, `.pdf` qua entrypoint nội bộ bằng quy trình được tài liệu hóa.
- [x] Layout capability-oriented hiện tại đủ ổn để tiếp tục phát triển feature tiếp theo mà không cần rollback shim cũ.
- [x] Không có decision mới nào buộc phải đổi public API contract của MVP.
- [x] Phase 4 đã có tài liệu tổng hợp implementation và verification để đóng nhịp đầu tiên.
