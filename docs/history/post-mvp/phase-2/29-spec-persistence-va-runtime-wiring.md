# 29. Spec Persistence Và Runtime Wiring

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Baseline cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Loại bỏ phụ thuộc tuyệt đối vào `InMemoryVectorStore` trong môi trường vận hành và khóa cách wiring adapter theo runtime config.

## Phạm vi

- thêm ít nhất một storage/index adapter có persistence
- giữ nguyên protocol `VectorStore` ở application/domain
- xác định cách chọn adapter theo runtime config hoặc environment
- khóa hành vi tối thiểu của storage mới đối với policy `replace-by-document_id-within-index_name`
- tài liệu hóa rõ local/staging dùng adapter nào và cách bật persistence

## Deliverable

- adapter persistence-backed hoặc storage thật đủ dùng cho phase này
- runtime wiring chọn được giữa adapter demo và adapter bền hơn
- tài liệu config theo môi trường cho storage
- integration test chứng minh policy re-index vẫn đúng trên storage mới

## Baseline cần có

Phase 2 không bắt buộc chốt vendor ngay trong spec. Tuy nhiên implementation phải khóa rõ:

- adapter nào là mặc định cho local development
- adapter nào được dùng cho staging-like khi cần persistence
- env hoặc config nào quyết định lựa chọn adapter
- vị trí dữ liệu được persist trong local/staging-like
- hành vi khi storage chưa sẵn sàng hoặc config storage không hợp lệ

Storage mới tối thiểu phải giữ được:

- tách biệt theo `index_name`
- policy `replace-by-document_id-within-index_name`
- retrieval filter semantics hiện tại, đặc biệt `tags = contains-any`
- kết quả query không làm lệch public contract hiện tại

## Acceptance criteria

- Khi bật persistence, restart process không làm mất toàn bộ index đã được ghi trước đó.
- Runtime wiring không yêu cầu sửa code để đổi giữa adapter demo và adapter bền hơn.
- Lỗi cấu hình hoặc lỗi khởi tạo storage được fail fast ở startup hoặc được log rõ ràng.
- Storage mới không làm rò rỉ object framework/provider vào application/domain.
- Quyết định storage không làm đổi semantics re-index đã chốt trong decision log.

## Verification

- Chạy integration test cho adapter persistence-backed hoặc storage thật tối thiểu.
- Chạy scenario ghi document, restart process, rồi retrieve lại trên cùng `index_name`.
- Kiểm tra policy `replace-by-document_id-within-index_name` vẫn đúng trên storage mới.
- Đối chiếu runtime wiring với runbook/config theo môi trường.

## Guardrails

- Không dùng persistence như lý do để đổi contract HTTP hoặc response schema.
- Không thêm abstraction mới ở application/domain nếu protocol hiện tại đã đủ.
- Không hard-code adapter thật vào use case hoặc service layer.
- Không coi “có file dữ liệu trên disk” là đủ nếu chưa chứng minh được retrieval sau restart.
