# 16. Implementation Guardrails

## Mục lục
- Mục tiêu
- Guardrails về scope MVP
- Guardrails về boundary kiến trúc
- Guardrails về behavior
- Guardrails về test và tài liệu
- Dấu hiệu đang lệch khỏi đường ray

## Mục tiêu

Tài liệu này là hàng rào triển khai để giữ team bám đúng spec MVP, tránh hai kiểu lệch phổ biến:

- thêm tính năng ngoài phạm vi khi code
- làm sai boundary khiến việc thay engine hoặc giữ behavior ổn định trở nên khó

Nếu một thay đổi vi phạm guardrail, mặc định phải dừng lại và ghi quyết định mới vào decision log trước khi tiếp tục.

## Guardrails về scope MVP

- Không thêm `reranker` vào sprint đầu.
- Không thêm hybrid retrieval vào sprint đầu.
- Không thêm async ingestion, queue hoặc batch orchestration nếu chưa có nhu cầu thật từ runtime hiện tại.
- Không thêm streaming response cho `/generate` trong MVP.
- Không thêm multi-tenant, RBAC hoặc workflow quản trị người dùng.
- Không biến parser file thành blocker của public API MVP; public contract vẫn là JSON text chuẩn hóa.

## Guardrails về boundary kiến trúc

- Domain và orchestration/capability layer không được phụ thuộc trực tiếp vào object model của LlamaIndex.
- Domain và orchestration/capability layer không được trả hoặc nhận object SDK của vector store, embedding provider hoặc LLM provider.
- Mọi object framework-specific phải được map về model nội bộ trước khi đi vào orchestration/capability layer.
- `Indexer`, `Retriever`, `Generator` phải giữ vai trò service nội bộ gần capability, không bị đẩy xuống thành adapter hoặc kéo lên thành public framework abstraction.
- API layer chỉ làm nhiệm vụ nhận request, map schema, gọi use case, map response và lỗi.
- Business rules, validation nghiệp vụ và semantics của `insufficient_context`, `grounded`, `citations` phải nằm ở orchestration/domain, không nằm rải trong adapter.

## Guardrails về behavior

- Re-index phải bám đúng policy `replace-by-document_id-within-index_name`.
- `tags` phải giữ semantics `contains-any` trừ khi có quyết định mới được ghi rõ.
- Khi không có context phù hợp, orchestration/capability layer phải trả `insufficient_context` và không gọi `LLMProvider`.
- Citation chỉ được tham chiếu theo `chunk_id` và chỉ lấy từ tập `retrieved_chunks` thực tế đã dùng.
- Runtime defaults chỉ được override trong biên spec đã khóa; không để config làm thay đổi public contract ngầm.
- Không log raw content hoặc dữ liệu nhạy cảm ngoài mức tối thiểu cần cho debug.

## Guardrails về test và tài liệu

- Mọi thay đổi behavior đều phải đi cùng test thể hiện behavior đó.
- Mọi thay đổi liên quan contract, config bounds hoặc semantics đều phải cập nhật tài liệu gốc tương ứng.
- Nếu fix bug nhưng bug đó chưa có golden case, phải bổ sung golden case.
- Ưu tiên fake port ở unit/use case test; chỉ dùng integration test cho wiring hoặc adapter-specific behavior.
- Không chấp nhận một thay đổi “tạm thời” làm sai boundary mà không có issue và quyết định rõ ràng.

## Dấu hiệu đang lệch khỏi đường ray

- Code ở orchestration/capability layer bắt đầu dùng trực tiếp object của engine hoặc provider.
- Adapter bắt đầu quyết định output schema, citation format hoặc prompt contract thay cho orchestration.
- Một endpoint mới xuất hiện nhưng không có spec và không nằm trong sprint plan.
- Config được dùng để mở rộng phạm vi behavior thay vì chỉ override trong biên đã khóa.
- Test phải sửa hàng loạt chỉ vì semantics chưa được khóa rõ.
- Team bắt đầu nói “cứ dựng trước cho tương lai” đối với các hạng mục không thuộc MVP.
