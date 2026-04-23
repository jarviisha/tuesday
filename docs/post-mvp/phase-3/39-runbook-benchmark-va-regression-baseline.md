# 39. Runbook Benchmark Và Regression Baseline

## Migration Note

Tài liệu này vẫn đúng về intent benchmark/regression, nhưng một số path bên dưới thuộc trạng thái trước migration package ngày `2026-04-23`.

Ở repo hiện tại:

- golden cases source-of-truth nằm ở `src/tuesday/rag/evaluation/golden_cases.py`
- `src/tuesday_rag/evaluation/golden_cases.py` không còn tồn tại; mọi nhắc đến path này bên dưới là historical reference

## Mục tiêu

Ghi lại cách chạy benchmark Phase 3, cách chạy regression suite, và nơi lưu baseline benchmark đầu tiên.

## Golden cases dùng chung

Phase 3 dùng chung:

- fixture từ `tests/fixtures.py`
- golden cases từ `src/tuesday_rag/evaluation/golden_cases.py`

Các behavior chính đang được khóa:

- retrieval match
- retrieval no-match
- grounded generation với citation hợp lệ
- `insufficient_context`
- semantics re-index
- semantics `tags = contains-any`

## Benchmark command

Command chuẩn:

```bash
python scripts/benchmark_quality.py
```

Command có thể đổi số vòng và output:

```bash
python scripts/benchmark_quality.py --iterations 5 --output benchmarks/phase-3/initial-baseline.json
```

Chỉ số benchmark hiện tại phải có:

- `retrieval_hit_rate`
- `insufficient_context_rate`
- `citation_valid_rate`
- latency `p50/p95` cho `index`, `retrieve`, `generate`

## Regression suite command

Target regression suite:

```bash
pytest tests/regression
```

Regression suite này đủ ngắn để chạy lại trước các thay đổi retrieval/generation quan trọng.

## Nơi lưu baseline

Baseline benchmark đầu tiên được lưu tại:

`benchmarks/phase-3/initial-baseline.json`

Format lưu phải:

- dễ diff
- dễ đọc bằng mắt
- có snapshot config tối thiểu
- có metadata về số iteration và số case

## Khi cập nhật baseline

Chỉ cập nhật baseline khi:

- benchmark script thay đổi có chủ đích
- fixture/golden case thay đổi có chủ đích
- semantics thay đổi đã được chốt bằng decision mới

Không cập nhật baseline lặng lẽ chỉ vì muốn “cho xanh”.
