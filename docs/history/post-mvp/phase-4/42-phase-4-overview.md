# 42. Phase 4 Overview

## Mục lục
- Mục tiêu
- Phạm vi
- Ngoài phạm vi
- Workstreams
- Tiêu chí thành công

## Mục tiêu

Khóa nhịp mở rộng đầu tiên sau Phase 3 theo hướng thực dụng:

- dùng layout capability-oriented hiện tại làm nền chính thức cho thay đổi tiếp theo
- bổ sung giá trị thực cho ingestion mà không mở thêm public endpoint
- giữ nguyên baseline contract, regression và benchmark đã có

## Phạm vi

Phase 4 hiện tại bao gồm 3 workstream:

1. `migration_completion_and_compatibility_cleanup`
2. `internal_file_ingestion_v1`
3. `verification_and_rollout_readiness`

Phạm vi đã hoàn tất trong nhịp này:

- internal file ingestion qua entrypoint nội bộ cho `.txt`, `.md`, `.html`, `.pdf`
- batch ingestion nội bộ cho local directory
- hardening cho batch CLI gồm `--recursive`, `--output`, `--include`, `--exclude`, `--dry-run`
- example assets và runbook đủ để team chạy lại trong local

## Ngoài phạm vi

- endpoint HTTP công khai mới cho upload file
- async ingestion, queue hoặc background orchestration
- recursive sync từ nguồn ngoài hệ thống
- OCR hoặc parse layout phức tạp
- hybrid retrieval, reranker, streaming response, auth/RBAC

## Workstreams

### 1. Migration completion and compatibility cleanup

Rà lại các shim chuyển tiếp còn tồn tại, đặc biệt ở composition root và import graph, để bảo đảm feature mới phát triển trên layout đã migrate thay vì tiếp tục kéo dài trạng thái chuyển tiếp.

### 2. Internal file ingestion v1

Thêm đường vào nội bộ để index file cục bộ hoặc nguồn nội bộ tương đương thông qua `DocumentParser`, giữ public API `/documents/index` ở mode JSON text như hiện tại.

Nhịp thực thi hiện tại đã mở rộng từ scope nhỏ ban đầu sang một bộ ingestion nội bộ thực dụng hơn:

- parser `.txt` và `.md`
- parser `.html` tối giản
- parser `.pdf` qua tool hệ thống
- batch local directory với lọc pattern và dry-run
- normalize metadata ở mức đủ dùng cho retrieval/citation hiện tại
- tái sử dụng semantics `replace-by-document_id-within-index_name` đang có

### 3. Verification and rollout readiness

Bổ sung kiểm chứng đủ để chứng minh nhịp migration + feature đầu tiên không làm regress baseline hiện có, đồng thời đủ tài liệu để team chạy lại trong local/staging.

## Tiêu chí thành công

- Team có một feature expansion đầu tiên đủ nhỏ để ship nhưng đủ thực tế để chứng minh layout mới dùng được.
- `internal file ingestion` chạy qua entrypoint nội bộ mà không làm thay đổi contract của 3 endpoint hiện tại.
- Regression, smoke test và benchmark quan trọng vẫn pass sau nhịp migration + feature này.
- Sau nhịp này, các mở rộng tiếp theo có thể bám trên layout mới mà không cần kéo dài compatibility shim ngoài mức cần thiết.
- Trạng thái hiện tại: các tiêu chí trên đã đạt ở mức đủ để coi nhịp Phase 4 đầu tiên là hoàn tất.
