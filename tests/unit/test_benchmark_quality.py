from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_benchmark_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_quality.py"
    spec = spec_from_file_location("benchmark_quality", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_benchmark_records_errors_by_group_endpoint_and_code() -> None:
    benchmark_quality = _load_benchmark_module()
    summary = benchmark_quality._empty_error_summary()

    benchmark_quality._record_error(
        summary,
        endpoint="/generate",
        status_code=502,
        error_code="GENERATION_ERROR",
    )
    benchmark_quality._record_error(
        summary,
        endpoint="/generate",
        status_code=502,
        error_code=None,
    )

    assert summary["count"] == 2
    assert summary["by_group"] == {"provider": 1, "unknown": 1}
    assert summary["by_endpoint"] == {"/generate": 2}
    assert summary["by_status"] == {"502": 2}
    assert summary["by_error_code"] == {"GENERATION_ERROR": 1, "UNKNOWN_ERROR": 1}
