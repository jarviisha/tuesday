# 60. Spec Provider Runtime Implementation v1

## Migration Note

Tài liệu này mô tả implementation target trước khi hoàn tất migration package ngày `2026-04-23`.

Khi đọc tài liệu này ở trạng thái repo hiện tại, cần quy chiếu như sau:

- app shell hiện tại nằm ở `src/tuesday/api/`
- runtime/config hiện tại nằm ở `src/tuesday/runtime/`
- capability `rag` hiện tại nằm ở `src/tuesday/rag/`
- lệnh chạy API hiện tại là `python -m uvicorn tuesday.api.app:app --reload`
- env prefix hiện tại là `TUESDAY_`
- `src/tuesday_rag/` đã bị loại bỏ khỏi codebase; mọi nhắc đến path này bên dưới là historical reference

## Trạng thái

`proposed`

## Mục lục

- Mục tiêu
- Bối cảnh hiện tại
- Quyết định implementation cần khóa
- Thiết kế runtime mục tiêu
- Thiết kế config/env mục tiêu
- Thiết kế provider adapter v1
- Thiết kế API/lifespan v1
- Thiết kế script/runtime factory v1
- Kế hoạch rollout nhỏ
- Verification bắt buộc
- Ngoài phạm vi v1

## Mục tiêu

Biến `57-spec-provider-integration-and-runtime-lifecycle-v1.md` thành một implementation spec đủ cụ thể để có thể code trực tiếp mà không còn phải đoán về:

- env names
- cách chọn provider
- cách khởi tạo container
- cách HTTP app và internal scripts dùng chung runtime factory
- mức kiểm tra `pdftotext` trong nhịp đầu

## Bối cảnh hiện tại

Codebase hiện đang có các đặc điểm sau:

- `EmbeddingProvider` và `LLMProvider` protocol đã tồn tại ở `src/tuesday_rag/domain/ports.py`
- `Container` hiện tự đọc `RuntimeConfig.from_env()` trong `__init__`
- module `src/tuesday_rag/runtime/container.py` đang export singleton `container = Container()`
- `src/tuesday_rag/api/app.py` và nhiều script/test đang import trực tiếp singleton này
- provider hiện tại vẫn là adapter demo:
  - `HashEmbeddingProvider`
  - `DeterministicLLMProvider`

Điểm nghẽn implementation hiện tại:

- app wiring xảy ra tại import-time
- test override env và monkeypatch dễ phụ thuộc trạng thái module đã import trước đó
- internal scripts và benchmark cũng đang dính trực tiếp vào singleton

## Quyết định implementation cần khóa

### 1. Runtime không còn export singleton khởi tạo sẵn tại import-time

`src/tuesday_rag/runtime/container.py` không nên tiếp tục là nơi tạo `container = Container()` ngay khi import module.

Thay vào đó, runtime layer nên cung cấp:

- `build_container(config: RuntimeConfig | None = None) -> Container`
- `build_config_from_env() -> RuntimeConfig`
- nếu cần, thêm `build_runtime_from_env() -> Container` như một convenience function

Mục tiêu là:

- HTTP app tự tạo container trong lifespan
- internal scripts tự gọi runtime factory khi chạy
- test có thể tạo runtime riêng theo config/env của từng case

### 2. App nên chuyển từ module-level app singleton sang app factory rõ ràng

`src/tuesday_rag/api/app.py` nên có:

- `create_app() -> FastAPI`
- một `lifespan` function gắn container vào `app.state.container`

Có thể vẫn giữ `app = create_app()` ở cuối module để lệnh `uvicorn tuesday_rag.api.app:app` tiếp tục hoạt động, nhưng container bên trong app phải được tạo ở lifespan, không phải ở import-time.

### 3. Request handlers không dùng global `container`

Các route trong API nên lấy runtime từ:

- `request.app.state.container`

Điều này làm rõ lifetime của dependency và giúp test override app/runtime dễ hơn.

### 4. Internal scripts dùng chung một runtime factory, không import singleton

Các script sau nên dừng import `container` trực tiếp:

- `scripts/index_file.py`
- `scripts/index_directory.py`
- `scripts/benchmark_quality.py`
- `scripts/smoke_test.py` nếu có dependency tương tự trong implementation thực tế

Thay vào đó, mỗi script nên:

- gọi `build_runtime_from_env()`
- giữ runtime trong `main()`
- truyền runtime xuống các helper nếu cần

### 5. Provider demo vẫn được giữ cho test/local fallback trong v1

Nhịp này chưa nên xóa adapter demo.

Adapter demo vẫn cần tồn tại để:

- chạy test unit nhanh
- chạy benchmark/regression nội bộ không cần credential thật
- giữ local setup tối giản khi người dùng chưa cấu hình provider thật

Nhưng provider demo không còn là con đường runtime duy nhất.

## Thiết kế runtime mục tiêu

### RuntimeConfig

`RuntimeConfig` tiếp tục là nơi giữ cấu hình runtime đã validate.

V1 nên mở rộng thêm các field sau:

- `embedding_provider_backend`
- `generation_provider_backend`
- `openai_api_key`
- `openai_base_url` nếu cần
- `openai_embedding_model`
- `openai_generation_model`
- `gemini_api_key`
- `gemini_embedding_model`
- `gemini_generation_model`
- `azure_openai_api_key`
- `azure_openai_endpoint`
- `azure_openai_api_version`
- `azure_openai_embedding_deployment`
- `azure_openai_generation_deployment`
- `pdf_startup_check_mode`

Tên field có thể tinh chỉnh, nhưng logic nên tách rõ:

- backend selector
- credentials
- model/deployment names
- startup check policy

### Container

`Container` vẫn là composition root object, nhưng constructor nên nhận `config` từ bên ngoài:

```python
class Container:
    def __init__(self, config: RuntimeConfig) -> None:
        ...
```

Điều này giúp:

- test inject config trực tiếp
- app lifecycle kiểm soát thời điểm load env
- scripts dùng cùng một đường khởi tạo

## Thiết kế config/env mục tiêu

### Env selectors cần khóa

V1 nên dùng hai selector riêng:

- `TUESDAY_RAG_EMBEDDING_PROVIDER_BACKEND`
- `TUESDAY_RAG_GENERATION_PROVIDER_BACKEND`

Giá trị hợp lệ của mỗi selector:

- `demo`
- `openai`
- `gemini`
- `azure_openai`

Lý do tách đôi:

- embedding và generation có thể dùng backend khác nhau
- tránh phải tạo một matrix config khó mở rộng về sau

### Env keys đề xuất

#### OpenAI

- `TUESDAY_RAG_OPENAI_API_KEY`
- `TUESDAY_RAG_OPENAI_BASE_URL`
- `TUESDAY_RAG_OPENAI_EMBEDDING_MODEL`
- `TUESDAY_RAG_OPENAI_GENERATION_MODEL`

#### Gemini

- `TUESDAY_RAG_GEMINI_API_KEY`
- `TUESDAY_RAG_GEMINI_EMBEDDING_MODEL`
- `TUESDAY_RAG_GEMINI_GENERATION_MODEL`

#### Azure OpenAI

- `TUESDAY_RAG_AZURE_OPENAI_API_KEY`
- `TUESDAY_RAG_AZURE_OPENAI_ENDPOINT`
- `TUESDAY_RAG_AZURE_OPENAI_API_VERSION`
- `TUESDAY_RAG_AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `TUESDAY_RAG_AZURE_OPENAI_GENERATION_DEPLOYMENT`

#### PDF startup check

- `TUESDAY_RAG_PDF_STARTUP_CHECK_MODE`

Giá trị hợp lệ:

- `off`
- `warn`
- `strict`

Mặc định của v1 nên là `off`.

### Validation rules v1

- nếu backend là `demo`, không yêu cầu credential
- nếu backend là `openai`, phải có API key và model tương ứng với capability được chọn
- nếu backend là `gemini`, phải có API key và model tương ứng
- nếu backend là `azure_openai`, phải có endpoint, API key, API version và deployment tương ứng
- `pdf_startup_check_mode` phải nằm trong `off|warn|strict`

Validation failure nên xảy ra khi build runtime/config, không trì hoãn đến request đầu tiên.

## Thiết kế provider adapter v1

### Scope adapter

V1 chỉ cần map vào 2 protocol hiện có:

- `EmbeddingProvider`
- `LLMProvider`

Không cần đưa SDK-specific object vượt qua `infrastructure/`.

### Module layout đề xuất

V1 có thể thêm:

- `src/tuesday_rag/infrastructure/providers_openai.py`
- `src/tuesday_rag/infrastructure/providers_gemini.py`
- `src/tuesday_rag/infrastructure/providers_azure_openai.py`

Hoặc gom vào ít file hơn nếu code ngắn. Điều quan trọng là:

- boundary provider-specific nằm trong `infrastructure/`
- `runtime/container.py` chỉ chọn adapter, không chứa logic HTTP client chi tiết

### Semantics v1

- `embed_texts` và `embed_query` phải trả về `list[list[float]]` và `list[float]` đúng với protocol hiện có
- `generate_text` phải map output về `LLMGenerationResult`
- parsing citations ở v1 có thể vẫn dùng format prompt/output hiện có nếu chưa thay generation policy

## Thiết kế API/lifespan v1

### App state

Trong lifespan:

- build config từ env
- build container từ config
- gắn vào `app.state.container`

Khi shutdown:

- không bắt buộc close resource trong v1 nếu adapter chưa cần cleanup
- nhưng nên giữ chỗ cho cleanup hook khi vector DB/client thật xuất hiện

### Health endpoint

`GET /health` vẫn giữ contract hiện tại.

V1 không cần thêm readiness detail vào response nếu chưa có decision mới.

### Startup check cho `pdftotext`

Nếu `pdf_startup_check_mode = warn`:

- app startup vẫn thành công
- log warning nếu không tìm thấy `pdftotext`

Nếu `pdf_startup_check_mode = strict`:

- build app/runtime phải fail fast nếu thiếu `pdftotext`

Nếu `off`:

- không kiểm tra khi startup
- PDF parsing chỉ fail tại thời điểm ingestion như hiện tại

## Thiết kế script/runtime factory v1

### Shared factory

Runtime layer nên có một entrypoint rõ dùng chung cho app và script, ví dụ:

```python
def build_runtime_from_env() -> Container:
    return build_container(build_config_from_env())
```

### Script changes v1

Các script hiện có nên chuyển sang pattern:

```python
def main() -> int:
    container = build_runtime_from_env()
    ...
```

Không nên giữ module-level singleton trong script vì điều đó làm env override trong test trở nên khó kiểm soát.

### Test changes v1

`tests/conftest.py` và các test đang import singleton `container` sẽ cần đổi sang một trong hai hướng:

- dùng app/runtime fixture tạo mới theo từng test
- hoặc monkeypatch runtime factory nếu test thật sự cần global path

Hướng ưu tiên là fixture-based.

## Kế hoạch rollout nhỏ

Để tránh scope nở quá nhanh, nhịp này nên làm theo thứ tự:

1. refactor runtime factory + `Container(config)` + app lifespan
2. cập nhật API tests, script tests và fixtures theo runtime mới
3. thêm config/env selector cho provider backends
4. giữ `demo` backend làm mặc định để không phá local flow hiện tại
5. thêm adapter thật đầu tiên với ít nhất một backend chạy được end-to-end
6. sau đó mới mở rộng thêm các backend còn lại

Khuyến nghị thực dụng:

- ở nhịp code đầu tiên, có thể implement runtime/lifespan + selector framework trước
- adapter thật có thể vào theo thứ tự `OpenAI` trước, rồi `Gemini`, rồi `Azure OpenAI`

Spec này vẫn giữ chỗ cho cả ba backend, nhưng implementation có thể đi theo rollout đó nếu cần giữ scope gọn.

## Verification bắt buộc

- unit test cho `RuntimeConfig` với backend selectors và required env
- unit test cho runtime factory chọn đúng provider adapter
- API test chứng minh app không còn phụ thuộc import-time singleton
- script test chứng minh mỗi script tự build runtime trong `main()`
- regression/smoke test hiện có vẫn pass với `demo` backend mặc định
- kiểm tra manual cho `pdf_startup_check_mode=warn|strict`

## Ngoài phạm vi v1

- streaming generation
- readiness endpoint mới
- pooling/async client tối ưu cho provider SDK
- vector store thật
- generation context policy mới
- thay đổi response contract công khai
