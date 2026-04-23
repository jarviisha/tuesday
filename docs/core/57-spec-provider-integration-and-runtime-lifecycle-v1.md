# 57. Spec Provider Integration And Runtime Lifecycle v1

## Migration Note

Tài liệu này mô tả hướng ưu tiên của workstream runtime/provider trước khi migration package hoàn tất ngày `2026-04-23`.

Khi đọc tài liệu này ở trạng thái repo hiện tại, cần quy chiếu như sau:

- app shell hiện tại nằm ở `src/tuesday/api/`
- runtime/config hiện tại nằm ở `src/tuesday/runtime/`
- capability `rag` hiện tại nằm ở `src/tuesday/rag/`
- app entrypoint hiện tại là `python -m uvicorn tuesday.api.app:app --reload`
- env prefix hiện tại là `TUESDAY_`
- `src/tuesday_rag/` đã bị loại bỏ khỏi codebase; mọi nhắc đến path này bên dưới là historical reference

## Trạng thái

`proposed`

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Quyết định thiết kế cần khóa
- Success criteria
- Verification mong muốn

## Mục tiêu

Thiết lập nền runtime đủ gần production để các nhịp core tiếp theo không tiếp tục dựa trên provider demo và container wiring khởi tạo quá sớm.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- contract `EmbeddingProvider`, `LLMProvider` và boundary adapter đã sẵn sàng
- container hiện là nơi hợp lý để chọn adapter theo env
- app wiring ở import-time làm test và override env dễ bị bẩn ngữ cảnh hơn mức cần thiết

Vì vậy, nhịp đầu tiên của track `core` nên khóa đường đi cho provider thật và app lifecycle rõ ràng.

## Phạm vi v1

Nhịp này nên ưu tiên:

- thêm adapter thật cho `OpenAI`, `Gemini`, `Azure`
- chọn provider theo env-based selection trong container/runtime wiring
- giữ provider demo/fake cho test và local benchmark khi cần
- chuyển container creation vào FastAPI lifespan thay vì khởi tạo tại import-time
- giữ boundary hiện có giữa `api`, `runtime`, `domain` và `infrastructure`
- đảm bảo internal scripts vẫn có entrypoint rõ để tạo runtime/container ngoài HTTP app
- document rõ phụ thuộc hệ thống `pdftotext` trong README
- cân nhắc startup check tùy chọn cho `pdftotext` khi cấu hình ingestion PDF được dùng

## Ngoài phạm vi v1

- đổi public API
- rewrite toàn bộ app bootstrap
- tối ưu retrieval ranking sâu
- thay vector store thật trong cùng nhịp nếu điều đó làm scope implementation quá lớn

## Quyết định thiết kế cần khóa

- env key nào quyết định provider embedding và provider generation
- demo provider còn tồn tại như fallback mặc định hay chỉ cho test
- startup check `pdftotext` là warning, fail-fast, hay opt-in theo env
- internal scripts dùng cùng runtime factory nào với HTTP app

## Success criteria

- có spec implementation cụ thể cho provider selection và app lifespan wiring
- có mapping env rõ cho ít nhất `OpenAI`, `Gemini`, `Azure`
- có test chứng minh app/test không còn phụ thuộc import-time container state
- README nêu rõ dependency `pdftotext` và behavior hiện tại nếu tool thiếu

Implementation detail ban đầu của nhịp này được tiếp tục ở:

- `60-spec-provider-runtime-implementation-v1.md`

## Verification mong muốn

- unit test cho runtime/container selection
- API test chứng minh app wiring qua lifespan vẫn hoạt động
- smoke test hiện có vẫn pass
- kiểm tra manual cho case thiếu `pdftotext` nếu startup check được bật
