# 40. Spec Quyết Định Migration Cấu Trúc `src`

## Mục lục
- Mục tiêu
- Quyết định hiện tại
- Lý do chấp nhận full migration
- Phạm vi migration
- Lộ trình migration
- Guardrails
- Verification

## Mục tiêu

Khóa rõ quyết định kiến trúc sau post-MVP về việc migrate cấu trúc `src/tuesday_rag` sang layout capability-based, để team có một hướng refactor thống nhất trước khi mở rộng feature sâu hơn.

## Quyết định hiện tại

Tại thời điểm sau Phase 3:

- **thực hiện full migration** cấu trúc `src/tuesday_rag`
- migration này được coi là một phần của bước vào `feature_expansion`
- feature expansion đầu tiên phải bám theo layout mới hoặc được thực hiện cùng nhịp migration
- mọi bước migrate phải bám theo guardrail và verification trong tài liệu này

Quyết định này áp dụng cho giai đoạn chuyển từ `quality_evaluation` sang `feature_expansion`.

## Lý do chấp nhận full migration

Ở thời điểm hiện tại repo đã có:

- baseline vận hành ổn định
- hardening tối thiểu
- benchmark và regression baseline đầu tiên

Team chấp nhận rằng ở mốc này full migration cấu trúc đem lại giá trị dài hạn lớn hơn chi phí refactor, vì roadmap tiếp theo cần một layout scale tốt hơn cho capability ownership và feature growth.

Lợi ích mong đợi của full migration:

- giảm việc một capability bị rải ra quá nhiều layer kỹ thuật
- chuẩn bị sẵn chỗ cho retrieval/index/generation phát triển mạnh hơn
- giảm ma sát khi thêm adapter, strategy và orchestration về sau
- giúp feature đầu tiên sau post-MVP không phải tiếp tục chồng lên layout chuyển tiếp hiện tại

Rủi ro đã được chấp nhận:

- chi phí delivery ngắn hạn tăng lên trong một nhịp
- nhiều file bị ảnh hưởng cùng lúc ở code, test và docs
- nguy cơ regress contract hoặc semantics nếu migration không có guardrail đủ chặt

## Phạm vi migration

Migration này bao gồm:

- thay đổi layout bên trong `src/tuesday_rag`
- gom code theo capability nhiều hơn thay vì chỉ theo layer kỹ thuật
- cập nhật import graph, dependency wiring, test path và docs liên quan
- giữ nguyên public API contract và semantics lõi trong suốt migration

Mục tiêu capability tối thiểu phải có trong layout mới:

- `ingestion`
- `index`
- `retrieval`
- `generation`
- `observability`

Phần có thể vẫn tạm hoãn hoặc chỉ tạo placeholder nếu chưa có implementation thật:

- thêm `tenant` như một module độc lập
- thêm `pipeline` như một orchestration layer độc lập

## Lộ trình migration

Migration phải đi theo trình tự:

1. khóa target layout mới ở mức package và boundary
2. migrate composition root và wiring mà không đổi contract HTTP
3. migrate capability theo thứ tự ưu tiên
4. sửa test, smoke test, benchmark và regression để chạy trên layout mới
5. chỉ bắt đầu feature expansion đầu tiên sau khi baseline verification của migration pass

Lộ trình gợi ý:

1. `retrieval`
2. `generation`
3. `index`
4. `ingestion`
5. `observability`

`tenant` và `pipeline` chỉ nên được hiện thực đầy đủ sau khi có use case thật hoặc feature spec riêng.

## Guardrails

- Không dùng migration cấu trúc như cái cớ để lén đổi behavior nghiệp vụ.
- Không mở thêm public endpoint chỉ vì layout mới thuận hơn.
- Không đổi public API contract hoặc semantics lõi chỉ vì layout mới thuận tay hơn.
- Mọi bước migration phải có benchmark/regression chạy lại.
- Nếu trong lúc migrate phát sinh thay đổi boundary lớn ngoài spec này, phải ghi decision mới trước hoặc cùng lúc với code.

## Verification

- Review target layout mới trước khi move file hàng loạt.
- Chạy smoke test, regression suite và benchmark baseline sau các mốc migrate chính.
- Xác nhận import graph mới không làm rò object framework/provider vào application/domain.
- Chỉ coi migration hoàn tất khi feature expansion đầu tiên có thể phát triển trên layout mới mà không cần rollback cấu trúc.
