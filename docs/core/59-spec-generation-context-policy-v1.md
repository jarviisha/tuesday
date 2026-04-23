# 59. Spec Generation Context Policy v1

## Trạng thái

`accepted` (`2026-04-23`)

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

- app dùng **deterministic rule** trước khi gọi LLM; v1 không dùng LLM-assisted check
- nếu `used_chunks` rỗng thì trả `insufficient_context` ngay như semantics hiện có
- nếu question có meaningful-token overlap quá thấp với context thì trả `insufficient_context`
- nếu question là loại hỏi chi tiết định lượng/thời gian (`bao lau`, `bao nhieu`, `khi nao`, `muc phi`, `gia bao nhieu`) nhưng context không có signal hỗ trợ tương ứng thì trả `insufficient_context`
- khi policy trả context không đủ, `used_chunks` vẫn được trả về như hiện tại để giữ traceability
- policy thống nhất toàn cục, không phụ thuộc provider cụ thể trong v1

## Success criteria

- có decision rõ policy `sufficient_context` được chọn
- policy được tách khỏi heuristic inline và mô tả được bằng rule kiểm chứng được
- có regression test cho các nhánh dễ sai nhất
- không làm lệch semantics `citations` và `insufficient_context` đã khóa trước đó

## Verification mong muốn

- regression suite cho generation context policy
- smoke test hiện có vẫn pass
- benchmark trước/sau trên golden cases nhạy với insufficient context
