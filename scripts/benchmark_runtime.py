from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl  # noqa: E402
from starter.agent import Agent  # noqa: E402


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("cannot calculate a percentile of an empty sample")
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def git_state() -> tuple[str, bool]:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip(), bool(status.stdout.strip())


class TimedAgent:
    def __init__(self, catalog_path: Path) -> None:
        start = time.perf_counter()
        self.agent = Agent(catalog_path)
        self.initialization_seconds = time.perf_counter() - start
        self.response_seconds: list[float] = []

    def reset(self, session_id: str, user_profile: dict) -> None:
        self.agent.reset(session_id, user_profile)

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        start = time.perf_counter()
        try:
            return self.agent.respond(session_id, user_message, turn, top_k)
        finally:
            self.response_seconds.append(time.perf_counter() - start)

    def close(self) -> None:
        self.agent.close()


def run_benchmark(catalog_path: Path, dataset_path: Path) -> dict:
    load_start = time.perf_counter()
    samples = load_jsonl(dataset_path)
    catalog_ids, categories, products = catalog_index(catalog_path)
    harness_load_seconds = time.perf_counter() - load_start

    agent = TimedAgent(catalog_path)
    try:
        evaluation_start = time.perf_counter()
        result = evaluate(agent, samples, catalog_ids, categories, products)
        evaluation_seconds = time.perf_counter() - evaluation_start
    finally:
        agent.close()

    latencies_ms = [duration * 1000 for duration in agent.response_seconds]
    metrics = {key: value for key, value in result.items() if key != "sessions"}
    commit, working_tree_dirty = git_state()
    return {
        "schema_version": 1,
        "commit": commit,
        "working_tree_dirty": working_tree_dirty,
        "command": "python scripts/benchmark_runtime.py",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "network_required": False,
        },
        "workload": {
            "sessions": len(samples),
            "respond_calls": len(latencies_ms),
            "catalog_products": len(catalog_ids),
        },
        "timing": {
            "official_harness_load_seconds": round(harness_load_seconds, 6),
            "agent_initialization_seconds": round(agent.initialization_seconds, 6),
            "evaluation_seconds": round(evaluation_seconds, 6),
            "respond_latency_ms": {
                "mean": round(statistics.fmean(latencies_ms), 6),
                "p50": round(percentile(latencies_ms, 0.50), 6),
                "p95": round(percentile(latencies_ms, 0.95), 6),
                "p99": round(percentile(latencies_ms, 0.99), 6),
                "max": round(max(latencies_ms), 6),
            },
        },
        "official_metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the real Agent in the official harness")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--dataset", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/runtime-benchmark.json"),
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run_benchmark(args.catalog.resolve(), args.dataset.resolve())
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
