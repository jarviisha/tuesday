# 59. Spec Generation Context Policy v1

## Trạng thái

`proposed`

## Mục lục

- Mục tiêu
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Quyết định cần khóa
- Success criteria
- Verification mong muốn

## Mục tiêu

Thay heuristic `_has_sufficient_context` bằng một policy được đặc tả rõ, kiểm chứng được và phù hợp hơn với lúc hệ thống đã có provider thật.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- logic `sufficient_context` đang dựa nhiều vào heuristic token overlap
- heuristic này hữu ích ở giai đoạn đầu nhưng chưa đủ rõ để coi là policy dài hạn
- khi có provider thật, hệ thống có thể cân nhắc delegate một phần quyết định này vào prompt/LLM thay vì tự suy luận bằng heuristic mỏng

## Phạm vi v1

Nhịp này nên ưu tiên:

- mô tả rõ policy `insufficient_context` mong muốn ở level behavior
- quyết định xem policy này là deterministic rule, LLM-assisted rule, hay hybrid
- giữ nguyên public contract của `/generate`
- giữ traceability giữa `used_chunks`, `grounded`, `insufficient_context` và `citations`
- thêm regression cases cho nhánh “context có vẻ liên quan nhưng chưa đủ”

## Ngoài phạm vi v1

- thay đổi response schema công khai
- mở streaming
- prompt redesign toàn diện ngoài phần liên quan context sufficiency

## Quyết định cần khóa

- điều kiện nào khiến app trả `insufficient_context` trước khi gọi LLM
- nếu dùng LLM-assisted check, prompt và output contract của bước check là gì
- khi LLM nói context không đủ thì `used_chunks` có vẫn được trả về như hiện tại không
- policy mới có cần phụ thuộc vào loại provider hay phải thống nhất toàn cục

## Success criteria

- có decision rõ policy `sufficient_context` được chọn
- có spec implementation đủ cụ thể để code
- có regression test cho các nhánh dễ sai nhất
- không làm lệch semantics `citations` và `insufficient_context` đã khóa trước đó

## Verification mong muốn

- regression suite cho generation context policy
- smoke test hiện có vẫn pass
- benchmark trước/sau trên golden cases nhạy với insufficient context
