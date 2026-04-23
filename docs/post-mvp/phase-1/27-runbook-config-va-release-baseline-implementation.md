# 27. Runbook, Config Và Release Baseline Implementation

## Migration Note

Runbook này phản ánh baseline Phase 1 trước migration package ngày `2026-04-23`.

Áp dụng vào repo hiện tại cần đổi như sau:

- app entrypoint hiện tại là `python -m uvicorn tuesday.api.app:app --reload`
- runtime config hiện tại ưu tiên env prefix `TUESDAY_`
- default file persistence path hiện tại là `.tuesday/vector_store.json`

## Mục tiêu

Khóa baseline vận hành tối thiểu của Phase 1 cho local và môi trường staging-like, đồng thời chốt mốc release nội bộ cho bản stabilize.

## Runbook local

Điều kiện trước khi chạy:

- Cài Python `3.12+`.
- Có `pip`.
- Tạo hoặc dùng sẵn virtual environment.

Luồng chạy chuẩn:

1. Tạo virtual environment:
   `python -m venv .venv`
2. Kích hoạt virtual environment:
   `source .venv/bin/activate`
3. Cài dependency dev:
   `pip install -e '.[dev]'`
4. Chạy lint:
   `ruff check .`
5. Chạy test:
   `pytest`
6. Chạy API local:
   `python -m uvicorn tuesday_rag.api.app:app --reload`

Health check:

- Endpoint: `GET /health`
- Kết quả mong đợi: `{"status":"ok"}`

Nếu app không lên, kiểm tra theo thứ tự:

1. Có đang dùng Python `3.12+` không.
2. Virtual environment đã được kích hoạt chưa.
3. Dependency dev đã được cài bằng `pip install -e '.[dev]'` chưa.
4. `ruff check .` và `pytest` có đang fail không.
5. Có env override nào làm `RuntimeConfig.from_env()` fail validation không.

## Runbook staging-like

Phase 1 chưa định nghĩa production deployment hoàn chỉnh. Với môi trường staging-like, baseline tối thiểu là:

1. Checkout đúng revision cần kiểm tra.
2. Cài dependency bằng cùng command chuẩn:
   `pip install -e '.[dev]'`
3. Chạy `ruff check .` và `pytest` trước khi coi revision là hợp lệ.
4. Chạy API bằng:
   `python -m uvicorn tuesday_rag.api.app:app`
5. Gọi `GET /health` để xác nhận app lên thành công.

Guardrail của staging-like:

- Chỉ dùng các env override đã liệt kê bên dưới.
- Không đổi public API contract.
- Không đổi semantics `insufficient_context`, `citations`, `tags = contains-any`.

## Runtime config đang được đọc

`RuntimeConfig.from_env()` hiện đọc mọi field của `RuntimeConfig` qua prefix `TUESDAY_RAG_`.

| Env var | Default | Override local/staging | Ghi chú |
| --- | --- | --- | --- |
| `TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT` | `5` | Có | Phải nằm trong `1..20`. |
| `TUESDAY_RAG_RETRIEVAL_TOP_K_MIN` | `1` | Không khuyến khích | Thay đổi bound nội bộ, không cần cho baseline Phase 1. |
| `TUESDAY_RAG_RETRIEVAL_TOP_K_MAX` | `20` | Không khuyến khích | Thay đổi bound nội bộ, không cần cho baseline Phase 1. |
| `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_DEFAULT` | `5` | Có | Phải nằm trong `1..10`. |
| `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_MIN` | `1` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_MAX` | `10` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_DEFAULT` | `1000` | Có | Phải nằm trong `300..2000`. |
| `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_MIN` | `300` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_MAX` | `2000` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_DEFAULT` | `150` | Có | Phải nằm trong `0..300` và nhỏ hơn chunk size. |
| `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_MIN` | `0` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_MAX` | `300` | Không khuyến khích | Không cần đổi để chạy baseline. |
| `TUESDAY_RAG_INGESTION_CHUNK_COUNT_MAX` | `200` | Có, thận trọng | Giới hạn cứng tổng số chunk sinh ra từ một document. |
| `TUESDAY_RAG_CONTENT_LENGTH_MIN` | `1` | Không khuyến khích | Thay đổi validation boundary. |
| `TUESDAY_RAG_CONTENT_LENGTH_MAX` | `100000` | Có, thận trọng | Không được làm lệch contract request body hiện tại. |
| `TUESDAY_RAG_QUERY_LENGTH_MIN` | `1` | Không khuyến khích | Thay đổi validation boundary. |
| `TUESDAY_RAG_QUERY_LENGTH_MAX` | `2000` | Có, thận trọng | Không được làm lệch expectation của API hiện tại. |
| `TUESDAY_RAG_QUESTION_LENGTH_MIN` | `1` | Không khuyến khích | Thay đổi validation boundary. |
| `TUESDAY_RAG_QUESTION_LENGTH_MAX` | `2000` | Có, thận trọng | Không được làm lệch expectation của API hiện tại. |
| `TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER` | `Không đủ dữ liệu trong ngữ cảnh hiện có để trả lời chắc chắn.` | Có | Chỉ đổi message fallback, không đổi semantics `insufficient_context=true`. |

## Default config và override hợp lệ

Default hiện tại là baseline chuẩn của repo. Override chỉ được coi là hợp lệ trong Phase 1 nếu:

- không làm `RuntimeConfig.validate()` fail
- không đổi public API contract
- không đổi semantics `insufficient_context`
- không đổi semantics `citations`
- không đổi semantics `tags = contains-any`

Override nên ưu tiên cho tuning cục bộ hoặc staging-like:

- `TUESDAY_RAG_RETRIEVAL_TOP_K_DEFAULT`
- `TUESDAY_RAG_GENERATION_MAX_CONTEXT_CHUNKS_DEFAULT`
- `TUESDAY_RAG_INGESTION_CHUNK_SIZE_CHARS_DEFAULT`
- `TUESDAY_RAG_INGESTION_CHUNK_OVERLAP_CHARS_DEFAULT`
- `TUESDAY_RAG_INSUFFICIENT_CONTEXT_ANSWER`

## Logging baseline

Logging tối thiểu của Phase 1 đã có trong API middleware và error handler.

Field phải có:

- `request_id`
- `use_case`
- `error_code`
- `latency_ms`

Guardrail logging:

- Không log raw content của tài liệu hoặc câu hỏi.
- Không log dữ liệu nhạy cảm ngoài mức tối thiểu cần để phân loại lỗi request.

## Release baseline

Mốc release nội bộ của Phase 1:

- `v0.1-internal-stabilize`

Điều kiện hoàn tất mốc này:

1. Repo có hướng dẫn setup dev và command chuẩn.
2. Repo có CI baseline chạy `ruff check .` và `pytest`.
3. Runbook local/staging-like và baseline config đã được ghi lại.
4. Logging tối thiểu giữ đủ `request_id`, `use_case`, `error_code`, `latency_ms`.
5. Không có thay đổi public API contract hoặc semantics lõi của MVP.

## CI pass/fail baseline

Pipeline CI Phase 1 được coi là `pass` khi:

- job `lint` pass với command `ruff check .`
- job `test` pass với command `pytest`

Pipeline CI Phase 1 được coi là `fail` khi:

- job `lint` fail
- job `test` fail
- dependency không cài được bằng `pip install -e '.[dev]'`
- repo không setup được Python `3.12` như yêu cầu của `pyproject.toml`

Ý nghĩa baseline này:

- Nếu `lint` fail, lỗi nằm ở chuẩn code hoặc import/order theo cấu hình hiện tại của repo.
- Nếu `test` fail, lỗi nằm ở hành vi hoặc wiring đang được test.
- Không coi trạng thái warning-only là pass cho baseline review nội bộ của Phase 1.
