# 35. Spec Fixtures Và Golden Cases

## Mục lục
- Mục tiêu
- Phạm vi
- Deliverable
- Baseline cần có
- Acceptance criteria
- Verification
- Guardrails

## Mục tiêu

Khóa bộ fixture và golden cases sau MVP để mọi benchmark, regression và review đều dựa trên cùng một tập dữ liệu nhỏ nhưng đủ đại diện.

## Phạm vi

- rà bộ fixture hiện có của repo
- chốt bộ golden cases sau MVP cho retrieval và generation
- bổ sung case còn thiếu nếu có regression quan trọng chưa được phủ
- giữ fixture deterministic và ưu tiên tiếng Việt

## Deliverable

- danh sách fixture/golden cases được khóa cho Phase 3
- tài liệu mô tả input, kỳ vọng và lý do giữ từng case
- mapping giữa golden case và endpoint hoặc behavior cần bảo vệ

## Baseline cần có

Phase 3 tối thiểu phải khóa:

- ít nhất một fixture retrieval match tốt
- ít nhất một fixture retrieval no-match
- ít nhất một fixture generation grounded có citation hợp lệ
- ít nhất một fixture generation `insufficient_context`
- ít nhất một fixture liên quan chunking hoặc nhiều chunk để tránh benchmark chỉ xoay quanh happy path quá ngắn

Golden cases phải chỉ rõ:

- phần behavior nào phải ổn định tuyệt đối
- phần nào có thể biến thiên nếu provider thật được bật sau này
- phần nào là contract/API invariant chứ không chỉ là output text mẫu

## Acceptance criteria

- Có một bộ fixture nhỏ dùng chung cho benchmark và regression.
- Golden case bám đúng contract hiện tại của `/documents/index`, `/retrieve`, `/generate`.
- Nếu có case mới, lý do thêm case được mô tả rõ thay vì thêm dữ liệu tràn lan.
- Bộ fixture đủ đại diện cho câu hỏi tiếng Việt và semantics lõi hiện tại.

## Verification

- Đối chiếu fixture/golden cases với docs hiện có và test hiện có.
- Rà từng golden case để chắc expected behavior không mâu thuẫn contract hiện tại.
- Kiểm tra mỗi case đều có mục đích rõ và không trùng lặp vô nghĩa.

## Guardrails

- Không biến fixture Phase 3 thành bộ dữ liệu lớn khó review.
- Không khóa expected text quá chi tiết nếu implementation/provider thật có biến thiên hợp lý.
- Không thêm case chỉ để phục vụ feature chưa thuộc scope.
