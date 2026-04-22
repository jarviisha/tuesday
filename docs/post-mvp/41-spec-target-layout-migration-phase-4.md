# 41. Spec Target Layout Migration Phase 4

## Mục tiêu

Khóa target layout tối thiểu cho nhịp migration đầu của Phase 4, để team có một package map đủ rõ trước khi move file theo capability.

## Success Criteria

- Có package trung lập cho composition root và runtime wiring, không neo trực tiếp vào `api/`.
- Có đích package rõ cho các capability sẽ được migrate trước: `retrieval`, `generation`, `ingestion`.
- Trong suốt migration, public HTTP contract và semantics hiện tại không đổi.
- Các import tương thích tạm thời được giữ đủ ngắn để smoke/regression vẫn pass trong từng nhịp nhỏ.

## Target Layout

```text
src/tuesday_rag/
  api/
  runtime/
  shared/
  ingestion/
  retrieval/
  generation/
  domain/
  infrastructure/
  evaluation/
  config.py
```

## Boundary Notes

- `runtime/` chứa composition root, runtime wiring và bootstrap concern dùng chung.
- `shared/` chứa helper dùng chung mức nhỏ, không mang orchestration riêng của capability.
- `api/` chỉ giữ HTTP transport, schema, error mapping và request-level observability.
- `retrieval/` và `generation/` là hai capability ưu tiên migrate trước vì đang có coupling trực tiếp.
- `ingestion/` được migrate sau, đi cùng phần nội bộ `index` thay vì tách `index` thành capability riêng ngay từ đầu.
- `domain/` và `infrastructure/` được giữ ổn định trong nhịp đầu để tránh tăng scope refactor.

## Migration Order

1. Tách composition root khỏi `api/` sang `runtime/`.
2. Migrate cụm `retrieval + generation`.
3. Migrate cụm `ingestion + index` nội bộ.
4. Chỉ tách thêm concern khác khi có use case hoặc boundary rõ hơn.

## Compatibility Rule

- Trong giai đoạn chuyển tiếp, `api.dependencies` có thể tồn tại như compatibility shim trỏ sang runtime container mới.
- Không giữ shim lâu hơn cần thiết sau khi import graph chính đã được chuyển xong.
