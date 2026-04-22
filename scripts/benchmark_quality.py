import argparse
import asyncio
import json
import os
import statistics
import time
from pathlib import Path

import httpx

from tuesday_rag.evaluation.golden_cases import (
    GENERATION_GOLDEN_CASES,
    ONBOARDING_DOCUMENT,
    REFUND_DOCUMENT,
    RETRIEVAL_GOLDEN_CASES,
)

DEFAULT_OUTPUT = "benchmarks/phase-3/initial-baseline.json"


async def _run_benchmark(iterations: int) -> dict:
    from tuesday_rag.api.app import app
    from tuesday_rag.api.dependencies import container

    container.vector_store.reset()
    transport = httpx.ASGITransport(app=app)
    retrieval_successes = 0
    retrieval_total = 0
    generation_total = 0
    insufficient_context_count = 0
    citation_valid_count = 0
    latency_samples = {
        "index": [],
        "retrieve": [],
        "generate": [],
    }

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for _ in range(iterations):
            container.vector_store.reset()
            await _timed_post(
                client,
                "/documents/index",
                REFUND_DOCUMENT,
                latency_samples["index"],
            )
            await _timed_post(
                client,
                "/documents/index",
                ONBOARDING_DOCUMENT,
                latency_samples["index"],
            )

            for case in RETRIEVAL_GOLDEN_CASES:
                retrieval_total += 1
                response = await _timed_post(
                    client,
                    "/retrieve",
                    {
                        "query": case.query,
                        "index_name": case.index_name,
                        "filters": case.filters,
                    },
                    latency_samples["retrieve"],
                )
                chunks = response.json()["chunks"]
                if case.expected_empty and chunks == []:
                    retrieval_successes += 1
                elif not case.expected_empty:
                    returned_ids = {chunk["document_id"] for chunk in chunks}
                    if returned_ids.issuperset(case.expected_document_ids):
                        retrieval_successes += 1

            for case in GENERATION_GOLDEN_CASES:
                generation_total += 1
                response = await _timed_post(
                    client,
                    "/generate",
                    {
                        "question": case.question,
                        "index_name": case.index_name,
                        "retrieval_request": case.retrieval_request,
                    },
                    latency_samples["generate"],
                )
                body = response.json()
                if body["insufficient_context"]:
                    insufficient_context_count += 1
                if set(body["citations"]).issubset(
                    {chunk["chunk_id"] for chunk in body["used_chunks"]}
                ):
                    citation_valid_count += 1

    config_snapshot = {
        "vector_store_backend": container.config.vector_store_backend,
        "embedding_timeout_ms": container.config.embedding_timeout_ms,
        "generation_timeout_ms": container.config.generation_timeout_ms,
        "vector_store_timeout_ms": container.config.vector_store_timeout_ms,
    }
    return {
        "phase": "quality_evaluation",
        "run_mode": "in_process",
        "iterations": iterations,
        "config": config_snapshot,
        "dataset": {
            "documents": 2,
            "retrieval_cases": len(RETRIEVAL_GOLDEN_CASES),
            "generation_cases": len(GENERATION_GOLDEN_CASES),
        },
        "metrics": {
            "retrieval_hit_rate": retrieval_successes / retrieval_total,
            "insufficient_context_rate": insufficient_context_count / generation_total,
            "citation_valid_rate": citation_valid_count / generation_total,
            "latency_ms": {
                endpoint: _latency_summary(values) for endpoint, values in latency_samples.items()
            },
        },
    }


async def _timed_post(
    client: httpx.AsyncClient,
    path: str,
    payload: dict,
    samples: list[float],
) -> httpx.Response:
    started_at = time.perf_counter()
    response = await client.post(path, json=payload)
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 3)
    samples.append(elapsed_ms)
    response.raise_for_status()
    return response


def _latency_summary(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "count": len(samples),
        "p50": round(statistics.median(ordered), 3),
        "p95": round(_percentile(ordered, 0.95), 3),
    }


def _percentile(samples: list[float], percentile: float) -> float:
    if len(samples) == 1:
        return samples[0]
    index = (len(samples) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(samples) - 1)
    fraction = index - lower
    return samples[lower] + (samples[upper] - samples[lower]) * fraction


def _write_output(output_path: str, result: dict) -> None:
    path = Path(output_path)
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(f"{json.dumps(result, indent=2)}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = asyncio.run(_run_benchmark(args.iterations))
    _write_output(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
