# 07. Use Case Generation

## Mục lục
- Mục tiêu
- Input / output
- Luồng xử lý
- Quy tắc build prompt
- Quy tắc grounding
- Quy tắc citations
- Hành vi khi context không đủ
- Error cases
- Definition of done
- Acceptance criteria
- Test cases mức use case

## Mục tiêu use case generation

Sinh câu trả lời cho người dùng dựa trên retrieved context, có grounding rõ ràng và citation theo `chunk_id`.

## Input / output

### Input

`GenerationRequest`

### Output

`GeneratedAnswer`

## Luồng xử lý chi tiết

1. Validate `question`.
2. Xác định nguồn context:
   - nếu có `retrieved_chunks`, dùng trực tiếp
   - nếu chưa có, gọi retrieval qua `retrieval_request`
3. Kiểm tra danh sách context sau cùng.
4. Nếu danh sách context rỗng, trả trực tiếp `GeneratedAnswer` với `insufficient_context = true`, `grounded = false`, `citations = []`, `used_chunks = []` theo policy MVP.
5. Nếu có context, chọn tối đa `max_context_chunks` để build prompt.
6. Gọi composite service `Generator`.
7. Bên trong `Generator`:
   - build prompt theo template nội bộ
   - chèn context theo format ổn định, có `chunk_id`
   - gọi `LLMProvider`
   - hậu xử lý kết quả thành `GeneratedAnswer`
8. Trả về answer cùng citations.

## Quy tắc build prompt

Prompt phải chứa tối thiểu:

- Vai trò hệ thống: trả lời dựa trên context được cung cấp.
- Câu hỏi người dùng.
- Danh sách context đã đánh số hoặc gắn rõ `chunk_id`.
- Chỉ dẫn hành vi khi thiếu dữ liệu.
- Yêu cầu citation theo `chunk_id`.

Nguyên tắc:

- Không đưa dữ liệu ngoài retrieved context vào prompt như một sự thật hệ thống.
- Không để prompt phụ thuộc format riêng của LlamaIndex.
- Prompt phải deterministic ở cấu trúc, để dễ test.

## Quy tắc grounding

- Chỉ trả lời dựa trên retrieved context.
- Không được bịa giá, chính sách, SLA, cam kết, thời hạn, hoặc thông tin không xuất hiện trong context.
- Nếu câu hỏi vượt quá dữ liệu có sẵn, phải nói rõ là không đủ dữ liệu.
- Không suy diễn thành sự thật chắc chắn khi context chỉ gợi ý một phần.

## Quy tắc citations

- Citations phải tham chiếu bằng `chunk_id`.
- Mỗi citation trong output phải tồn tại trong `used_chunks`.
- Không phát sinh citation giả không có trong context.
- Nếu câu trả lời có nhiều ý độc lập, output nên viện dẫn tất cả chunk liên quan đã dùng.

## Hành vi khi context không đủ

- Nếu retrieval trả về rỗng:
  - `insufficient_context = true`
  - `grounded = false`
  - answer phải nói rõ không đủ dữ liệu để trả lời chắc chắn
  - application layer phải trả lời theo template nội bộ cố định hoặc format tương đương mà không gọi LLM
- Nếu retrieval có chunk nhưng không đủ để trả lời đầy đủ:
  - answer phải nêu phần nào có căn cứ, phần nào chưa đủ dữ liệu
  - không được bịa phần thiếu

## Error cases

| Mã lỗi gợi ý | Tình huống |
|---|---|
| `INVALID_INPUT` | Câu hỏi rỗng hoặc thiếu cả retrieval request lẫn retrieved chunks |
| `RETRIEVAL_ERROR` | Cần retrieval nhưng retrieval thất bại |
| `PROMPT_BUILD_ERROR` | Không build được prompt hợp lệ |
| `GENERATION_ERROR` | LLM provider lỗi |
| `INVALID_GENERATION_OUTPUT` | Output không map được về contract nội bộ |

## Definition of done

- Hệ thống sinh được `GeneratedAnswer` đúng schema.
- Answer có grounding theo context.
- Citation hợp lệ theo `chunk_id`.
- Khi thiếu dữ liệu, câu trả lời nêu rõ giới hạn.
- Không phụ thuộc object LlamaIndex trong output.

## Acceptance criteria

- Nếu có context đủ mạnh, câu trả lời phải chỉ dựa trên context đó.
- Nếu không đủ dữ liệu, câu trả lời phải nói rõ không đủ dữ liệu.
- `citations` chỉ chứa `chunk_id` thuộc `used_chunks`.
- Khi `retrieved_chunks` đã được truyền vào, use case không được tự ý gọi retrieval lại.
- Khi `retrieved_chunks` được truyền vào nhưng rỗng, hệ thống vẫn xử lý hợp lệ theo nhánh `insufficient_context`.
- Chỉ khi thiếu cả `retrieval_request` lẫn `retrieved_chunks` thì request mới bị từ chối.
- Khi không có context khả dụng, use case phải hoàn tất mà không gọi `LLMProvider`.

## Test cases mức use case

| ID | Kịch bản | Input chính | Kỳ vọng |
|---|---|---|---|
| GEN-01 | Generation với retrieved chunks có sẵn | Question + 2 chunk | Trả answer grounded, citations hợp lệ |
| GEN-02 | Generation tự gọi retrieval | Question + retrieval request | Gọi retrieval rồi sinh answer |
| GEN-03 | Thiếu toàn bộ context input | Chỉ có question | Lỗi `INVALID_INPUT` |
| GEN-04 | Retrieved chunks rỗng | Question + `[]` | Answer nêu không đủ dữ liệu, `insufficient_context = true` |
| GEN-05 | LLM provider lỗi | Context hợp lệ | Lỗi `GENERATION_ERROR` |
| GEN-06 | Output viện dẫn chunk không tồn tại | LLM trả citation sai | Lỗi `INVALID_GENERATION_OUTPUT` hoặc hậu xử lý loại bỏ citation sai theo policy |
| GEN-07 | Câu hỏi yêu cầu thông tin không có trong context | Context không chứa giá/chính sách | Answer từ chối suy đoán, nêu không đủ dữ liệu |
