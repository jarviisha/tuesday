# 33. Runbook Persistence, Resilience Và Smoke Test

## Migration Note

Runbook này mô tả trạng thái Phase 2 trước migration package ngày `2026-04-23`.

Trong repo hiện tại, khi áp dụng hướng dẫn bên dưới cần quy đổi:

- `TUESDAY_RAG_*` thành `TUESDAY_*` cho env mới
- `.tuesday-rag/vector_store.json` thành `.tuesday/vector_store.json`
- `python -m uvicorn tuesday_rag.api.app:app --reload` thành `python -m uvicorn tuesday.api.app:app --reload`

## Mục tiêu

Ghi lại baseline triển khai thực tế của Phase 2 để local và staging-like có thể bật persistence, chạy smoke test và đọc tín hiệu lỗi chính mà không cần suy đoán.

## Runtime wiring

Phase 2 hiện hỗ trợ 2 chế độ vector store:

- `memory`
- `file`

Env điều khiển:

- `TUESDAY_RAG_VECTOR_STORE_BACKEND`
- `TUESDAY_RAG_VECTOR_STORE_FILE_PATH`

Giá trị mặc định:

- `TUESDAY_RAG_VECTOR_STORE_BACKEND=memory`
- `TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/vector_store.json`

Khuyến nghị theo môi trường:

- local development mặc định: `memory`
- local cần kiểm tra persistence: `file`
- staging-like: `file` hoặc adapter bền hơn tương đương, nhưng phải giữ cùng semantics hiện tại

Ví dụ bật persistence ở local hoặc staging-like:

```bash
export TUESDAY_RAG_VECTOR_STORE_BACKEND=file
export TUESDAY_RAG_VECTOR_STORE_FILE_PATH=.tuesday-rag/vector_store.json
python -m uvicorn tuesday_rag.api.app:app --reload
```

## Resilience config

Phase 2 khóa timeout và retry tối thiểu qua env:

- `TUESDAY_RAG_EMBEDDING_TIMEOUT_MS`
- `TUESDAY_RAG_EMBEDDING_MAX_RETRIES`
- `TUESDAY_RAG_GENERATION_TIMEOUT_MS`
- `TUESDAY_RAG_GENERATION_MAX_RETRIES`
- `TUESDAY_RAG_VECTOR_STORE_TIMEOUT_MS`
- `TUESDAY_RAG_VECTOR_STORE_MAX_RETRIES`

Giá trị mặc định:

- timeout: `1000ms`
- retry: `0`

Nguyên tắc vận hành:

- timeout luôn hữu hạn
- retry chỉ là bounded retry
- không retry lỗi input hoặc config sai
- public API contract không đổi khi failure hạ tầng xảy ra

## Observability baseline

Logging của Phase 2 giữ các field từ Phase 1:

- `request_id`
- `use_case`
- `error_code`
- `latency_ms`

Và bổ sung:

- `failure_group`
- `failure_component`
- `failure_mode`
- `retry_count`
- `timeout_ms`

Các nhóm lỗi chính hiện được phân biệt:

- `application`
- `provider`
- `storage`

## Smoke test

Command smoke test in-process:

```bash
python scripts/smoke_test.py
```

Command smoke test với API đang chạy:

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

Smoke test kiểm chứng chuỗi:

1. `POST /documents/index`
2. `POST /retrieve`
3. `POST /generate`

## Khi smoke test fail

Kiểm tra theo thứ tự:

1. API có đang dùng config backend đúng như mong đợi không.
2. Nếu dùng `file`, đường dẫn trong `TUESDAY_RAG_VECTOR_STORE_FILE_PATH` có ghi được không.
3. Timeout/retry env có đang quá thấp hoặc sai so với môi trường hiện tại không.
4. Log `request.failed` đang báo `failure_group` nào.
5. `failure_component` là `embedding_provider`, `generation_provider`, `vector_store` hay `request_validation`.

## Checklist done của implementation Phase 2

- Có file-backed vector store để giữ dữ liệu qua restart process.
- Có runtime wiring chọn `memory` hoặc `file` qua env.
- Có timeout/retry wrapper cho embedding provider, generation provider và vector store.
- Có smoke test command rõ ràng.
- Có logging đủ để phân biệt nhóm lỗi chính mà không log raw content.
