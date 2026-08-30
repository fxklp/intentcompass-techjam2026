from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.retrieval.evaluate import peak_rss_bytes, percentile  # noqa: E402
from solution.retrieval import (  # noqa: E402
    BaselineFTS5Retriever,
    DualRouteInMemoryRetriever,
    RetrievalConstraint,
    RetrievalRequest,
)


REQUESTS = (
    RetrievalRequest("comfortable black running shoes", 50),
    RetrievalRequest(
        "men cotton shirt under 30",
        50,
        category="men shirts",
        constraints=(
            RetrievalConstraint("material", ("cotton",)),
            RetrievalConstraint("budget", ("under $30",)),
        ),
    ),
    RetrievalRequest(
        "something lightweight for travel",
        50,
        category="travel clothing",
        constraints=(RetrievalConstraint("use_case", ("travel",)),),
        route_hint="browsing",
    ),
)


def benchmark(catalog: Path, mode: str, iterations: int) -> dict[str, object]:
    started = time.perf_counter()
    retriever = (
        BaselineFTS5Retriever(catalog)
        if mode == "baseline"
        else DualRouteInMemoryRetriever(catalog)
    )
    startup = time.perf_counter() - started
    timings: list[float] = []
    digests: list[list[str]] = []
    try:
        for iteration in range(iterations):
            for request in REQUESTS:
                call_started = time.perf_counter()
                result = retriever.search(request)
                timings.append((time.perf_counter() - call_started) * 1000.0)
                if iteration == 0:
                    digests.append([item.parent_asin for item in result.candidates[:10]])
        return {
            "mode": mode,
            "iterations": iterations,
            "cold_start_seconds": round(startup, 6),
            "retrieval_ms_mean": round(statistics.fmean(timings), 6),
            "retrieval_ms_p50": percentile(timings, 0.50),
            "retrieval_ms_p95": percentile(timings, 0.95),
            "peak_rss_bytes": peak_rss_bytes(),
            "deterministic_top10_samples": digests,
        }
    finally:
        retriever.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark TASK-303 candidate retrieval")
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {
        mode: benchmark(args.catalog.resolve(), mode, max(1, args.iterations))
        for mode in ("baseline", "candidate")
    }
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
