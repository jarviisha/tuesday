# 19. Spec Đánh Giá Chất Lượng Và Mở Rộng

## Mục lục
- Phase 3: Quality evaluation
- Phase 4: Feature expansion
- Điều kiện vào phase

## Phase 3: Quality evaluation

### Mục tiêu

Thiết lập baseline định lượng cho chất lượng RAG để mọi thay đổi tiếp theo được đánh giá bằng dữ liệu thay vì cảm giác.

### Phạm vi

- khóa fixture/golden cases đủ đại diện cho câu hỏi tiếng Việt
- đo retrieval quality ở mức tối thiểu
- đo grounding/citation correctness ở mức ứng dụng
- đo latency cơ bản cho các luồng chính
- nếu có provider thật, đo thêm chi phí mỗi request ở mức gần đúng

### Chỉ số tối thiểu

- retrieval hit rate trên bộ fixture đã khóa
- tỷ lệ `insufficient_context`
- tỷ lệ citation hợp lệ theo rule `citations subset of used_chunks`
- latency `p50` và `p95` cho `index`, `retrieve`, `generate`
- tỷ lệ request lỗi theo nhóm lỗi chính

### Deliverable

- bộ fixture/golden cases sau MVP
- tài liệu benchmark nhỏ nhưng deterministic nhất có thể
- regression suite cho các case quan trọng
- baseline metric được chốt làm mốc so sánh

### Acceptance criteria

- Có ít nhất một bộ dữ liệu nhỏ dùng chung cho review, regression và benchmark.
- Có thể chạy lại benchmark theo cùng một quy trình.
- Mọi thay đổi liên quan chunking, retrieval hoặc generation có thể so sánh với baseline.
- Khi adapter/provider thật tạo ra biến thiên, spec vẫn khóa phần behavior phải ổn định ở application/API.

### Verification

- Chạy benchmark hoặc regression suite trên bộ fixture đã khóa.
- Lưu lại kết quả baseline theo định dạng mà team đọc được.
- Rà các golden case để bảo đảm chúng vẫn phản ánh contract hiện tại.

## Phase 4: Feature expansion

### Mục tiêu

Mở rộng khả năng của hệ thống sau khi đã có nền ổn định và baseline chất lượng đủ để đánh giá trade-off.

### Danh mục ưu tiên mặc định

1. ingestion từ file hoặc nguồn nội bộ thực tế
2. async ingestion hoặc background job nếu tải ingestion tăng
3. cải thiện retrieval quality nếu benchmark chưa đạt
4. streaming response nếu có nhu cầu UX rõ
5. auth/RBAC nếu xuất hiện nhu cầu chia quyền thật

### Điều không mặc định ưu tiên

- mở thêm endpoint công khai mới
- hybrid retrieval
- reranker
- bộ nhớ hội thoại dài hạn
- workflow orchestration phân tán quy mô lớn

### Acceptance criteria

- Mỗi feature mới phải có spec riêng nếu làm đổi behavior, contract hoặc boundary.
- Mỗi feature mới phải chỉ rõ vì sao không thể trì hoãn sau phase hiện tại.
- Feature mới phải có golden case hoặc benchmark tương ứng nếu nó tác động chất lượng retrieval/generation.
- Không dùng feature mới để bù cho thiếu sót của observability hoặc baseline đánh giá.

### Verification

- Review spec riêng của feature trước khi code.
- Có test hoặc benchmark chứng minh giá trị của feature đó.
- Có đánh giá rủi ro về coupling, chi phí vận hành và độ phức tạp triển khai.

## Điều kiện vào phase

- Chỉ vào `quality_evaluation` khi `stabilize` đã xong ở mức đủ chạy lặp lại.
- Chỉ vào `feature_expansion` khi đã có baseline tối thiểu từ `quality_evaluation`, trừ khi có yêu cầu nghiệp vụ khẩn cấp được chấp nhận rõ ràng.

## Ghi chú kiến trúc sau post-MVP

- Full migration cấu trúc `src/tuesday_rag` được chấp nhận như một phần của bước vào `feature_expansion`.
- Migration này ưu tiên layout capability-oriented nhưng phải bám boundary thực tế của codebase hiện tại, không ép tách cơ học mọi concern thành module độc lập.
- Migration này phải bám theo decision và guardrail trong `40-spec-quyet-dinh-migration-cau-truc-src.md`.
