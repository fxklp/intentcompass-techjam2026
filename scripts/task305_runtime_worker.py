"""Fresh-process runtime worker for paired RC3/TASK-305 measurements."""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import platform
import statistics
import sys
import time
from pathlib import Path


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def peak_rss_bytes() -> int | None:
    if sys.platform != "win32":
        return None
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.argtypes = []
    get_current_process.restype = ctypes.c_void_p
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    get_memory.restype = ctypes.c_int
    ok = get_memory(get_current_process(), ctypes.byref(counters), counters.cb)
    return int(counters.PeakWorkingSetSize) if ok else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--preset", choices=("rc3", "candidate"), required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.resolve()
    sys.path.insert(0, str(root))
    if args.preset == "rc3":
        from scripts.release_check import activate_preset
        activate_preset()
    else:
        from scripts.task305_evaluate import PRESET
        os.environ.update(PRESET)
        os.environ.update(
            INTENTCOMPASS_SEMANTIC="local",
            INTENTCOMPASS_LLM_ALLOW_NETWORK="0",
            INTENTCOMPASS_SEMANTIC_ASSETS=str(root / "artifacts/semantic"),
        )
    from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl
    from starter.agent import Agent

    load_started = time.perf_counter()
    samples = load_jsonl(args.dataset)
    identifiers, categories, products = catalog_index(args.catalog)
    harness_load = time.perf_counter() - load_started
    init_started = time.perf_counter()
    agent = Agent(args.catalog)
    initialization = time.perf_counter() - init_started
    latencies: list[float] = []
    original = agent.respond
    def timed(*call_args, **call_kwargs):
        started = time.perf_counter()
        try:
            return original(*call_args, **call_kwargs)
        finally:
            latencies.append((time.perf_counter() - started) * 1000)
    agent.respond = timed
    evaluation_started = time.perf_counter()
    try:
        metrics = evaluate(agent, samples, identifiers, categories, products)
        evidence = dict(getattr(getattr(agent._core, "_adaptive", None), "evidence_counts", {}))
    finally:
        agent.close()
    evaluation_seconds = time.perf_counter() - evaluation_started
    report = {
        "schema_version": 1,
        "preset": args.preset,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_root_name": root.name,
        "workload": {"sessions": len(samples), "responses": len(latencies)},
        "timing": {
            "harness_load_seconds": round(harness_load, 6),
            "initialization_seconds": round(initialization, 6),
            "evaluation_seconds": round(evaluation_seconds, 6),
            "total_seconds": round(harness_load + initialization + evaluation_seconds, 6),
            "response_ms": {
                "p50": round(percentile(latencies, .50), 6),
                "p95": round(percentile(latencies, .95), 6),
                "p99": round(percentile(latencies, .99), 6),
                "max": round(max(latencies), 6),
            },
        },
        "peak_rss_bytes": peak_rss_bytes(),
        "capability_evidence": dict(sorted(evidence.items())),
        "metrics": {key: value for key, value in metrics.items() if key != "sessions"},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
