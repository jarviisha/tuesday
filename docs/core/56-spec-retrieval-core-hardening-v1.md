# 56. Spec Retrieval Core Hardening v1

## Trạng thái

`accepted` (`2026-04-23`)

## Mục lục

- Mục tiêu
- Vị trí trong backlog
- Lý do ưu tiên
- Phạm vi v1
- Ngoài phạm vi v1
- Giả thuyết kỹ thuật
- Success criteria
- Verification mong muốn

## Mục tiêu

Xác định nhịp đầu tiên để cải thiện phần lõi retrieval của hệ thống trên baseline hiện tại, trước khi mở thêm capability lớn hoặc thay toàn bộ framework.

## Vị trí trong backlog

Tài liệu này vẫn còn hiệu lực, nhưng **không còn là nhịp implementation đầu tiên của track `core`**.

Theo thứ tự ưu tiên mới, `retrieval_core_hardening` nên đi sau:

1. provider thật + env-based selection
2. vector store thật
3. container lifecycle qua lifespan
4. context-sufficiency policy rõ hơn

Lý do là các bước trên sẽ tạo nền thực tế hơn để đo retrieval quality, thay vì tối ưu retrieval trên adapter demo và runtime wiring tạm thời.

## Lý do ưu tiên

Ở trạng thái hiện tại:

- ingestion nội bộ đã đủ dùng cho việc đưa dữ liệu thật vào hệ thống
- benchmark và regression đã tồn tại để đo tác động của thay đổi
- retrieval hiện vẫn còn khá tối giản, nên đây là nơi có tiềm năng tăng giá trị lớn cho chất lượng đầu ra
- tuy nhiên, việc triển khai provider/store thật hiện được ưu tiên trước để tránh tối ưu sai mặt bằng kỹ thuật

## Phạm vi v1

Nhịp `v1` của `retrieval_core_hardening` khóa một cải tiến nhỏ nhưng đo được ở application layer:

- giữ nguyên vector query ở từng adapter store hiện có
- thêm post-retrieval reranking trong `RetrieverService` theo lexical coverage của query trên `chunk.text`
- nếu có ít nhất một candidate có overlap meaningful tokens với query, loại các candidate overlap bằng `0`
- sắp xếp candidate còn lại theo `overlap_count`, rồi `overlap_ratio`, rồi mới đến `raw vector score`
- thêm unit/regression test để khóa failure mode "score vector dương nhưng chunk không thực sự bám query"

## Ngoài phạm vi v1

- rewrite toàn bộ core sang framework khác
- hybrid retrieval đầy đủ nếu chưa có benchmark chứng minh cần
- reranker phụ thuộc model ngoài nếu chưa có baseline cho vấn đề đang gặp
- thay semantics filter hoặc đổi public API
- thay prompt generation để bù cho retrieval

## Giả thuyết kỹ thuật

Giả thuyết đã được chốt cho v1:

- với backend vector thật hoặc demo, vẫn có thể xuất hiện candidate có `score > 0` nhưng không chứa từ khóa hữu ích của câu hỏi
- một lớp rerank/filter deterministic ở `RetrieverService` là đủ nhỏ để áp dụng thống nhất cho mọi backend hiện có
- lexical coverage là tín hiệu an toàn hơn việc tăng complexity sang hybrid/BM25/reranker model ngay trong nhịp đầu

## Success criteria

- có decision mới khóa hướng retrieval đầu tiên được chọn
- `RetrieverService` áp dụng post-retrieval ranking policy provider-independent
- có unit test chứng minh chunk overlap tốt hơn được ưu tiên hơn chunk chỉ có raw score cao
- có regression test chứng minh candidate zero-overlap bị loại khi đã có candidate bám query
- smoke test hiện có không đổi contract

## Verification mong muốn

- unit test cho ranking policy và integration của `RetrieverService`
- regression test cho failure mode retrieval vừa được nhắm tới
- smoke test hiện có vẫn pass
