# Phase 3: Quality Evaluation

## Migration Note

Artefact path trong tài liệu này phản ánh layout trước migration package ngày `2026-04-23`.

Khi đọc ở trạng thái repo hiện tại, path chuẩn cần ưu tiên là:

- `../../../src/tuesday/rag/evaluation/golden_cases.py`
- `../../../scripts/benchmark_quality.py`
- `../../../tests/regression/test_quality_regression.py`

## Mục lục
- Mục tiêu phase
- Danh sách spec con
- Thứ tự đọc
- Điều kiện done

## Mục tiêu phase

Phase 3 nhằm khóa baseline định lượng cho chất lượng RAG của bản sau hardening, để mọi thay đổi tiếp theo được so sánh bằng dữ liệu thay vì cảm giác.

Phase này tập trung vào fixture chung, benchmark nhỏ nhưng lặp lại được, regression suite cho các behavior nhạy cảm, và nơi lưu kết quả baseline ban đầu. Phase này không mở rộng public API contract.

## Danh sách spec con

- `34-phase-3-overview.md`
- `35-spec-fixtures-va-golden-cases.md`
- `36-spec-benchmark-va-baseline-metrics.md`
- `37-spec-regression-suite-va-luu-ket-qua.md`
- `38-checklist-phase-3-quality-evaluation.md`

## Artefact triển khai

- `39-runbook-benchmark-va-regression-baseline.md`
- `../../../scripts/benchmark_quality.py`
- `../../../src/tuesday_rag/evaluation/golden_cases.py`
- `../../../tests/regression/test_quality_regression.py`
- `../../../benchmarks/phase-3/initial-baseline.json`

## Thứ tự đọc

1. `34-phase-3-overview.md`
2. `35-spec-fixtures-va-golden-cases.md`
3. `36-spec-benchmark-va-baseline-metrics.md`
4. `37-spec-regression-suite-va-luu-ket-qua.md`
5. `38-checklist-phase-3-quality-evaluation.md`

## Điều kiện done

- Có bộ fixture/golden cases sau MVP được khóa và dùng chung.
- Có benchmark nhỏ nhưng chạy lặp lại được trên cùng quy trình.
- Có baseline tối thiểu cho retrieval quality, grounding/citation correctness và latency.
- Có regression suite cho các case nhạy cảm trước khi bước sang feature expansion.
- Có nơi lưu baseline benchmark ban đầu để so sánh về sau.
- Không đổi public API contract hoặc semantics lõi của MVP nếu chưa có decision mới.
