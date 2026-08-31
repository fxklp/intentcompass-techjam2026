from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl  # noqa: E402
from experiments.retrieval.agent import RetrievalExperimentAgent  # noqa: E402
from scripts.shadow_evaluator import (  # noqa: E402
    SCENARIO_COUNTS,
    SEED,
    build_samples,
    select_targets,
)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return round(ordered[index], 6)


def peak_rss_bytes() -> int:
    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        from ctypes import wintypes

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        get_memory_info = kernel32.K32GetProcessMemoryInfo
        get_memory_info.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        )
        get_memory_info.restype = wintypes.BOOL
        handle = kernel32.GetCurrentProcess()
        if get_memory_info(
            handle, ctypes.byref(counters), counters.cb
        ):
            return int(counters.PeakWorkingSetSize)
        return 0
    import resource

    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == "darwin" else raw * 1024)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def samples_for_dataset(
    dataset: str,
    catalog_ids: set[str],
    public_samples: list[dict],
) -> list[dict]:
    if dataset == "public":
        return public_samples
    public_targets = {
        str(item["ground_truth"]["parent_asin"])
        for item in public_samples
    }
    targets = select_targets(
        catalog_ids,
        public_targets,
        sum(SCENARIO_COUNTS.values()),
        SEED,
    )
    return build_samples(targets, SEED)


def candidate_recall(samples: list[dict], audits: list[dict[str, object]]) -> dict[str, float | int]:
    first_turn_hits = 0
    any_turn_hits = 0
    observed_turns = 0
    target_observations = 0
    for sample, audit in zip(samples, audits):
        target = str(sample["ground_truth"]["parent_asin"])
        turns = audit.get("turns", [])
        assert isinstance(turns, list)
        hit_flags = []
        for turn in turns:
            candidate_ids = turn.get("candidate_ids", [])
            hit = target in candidate_ids
            hit_flags.append(hit)
            observed_turns += 1
            target_observations += int(hit)
        first_turn_hits += int(bool(hit_flags and hit_flags[0]))
        any_turn_hits += int(any(hit_flags))
    count = len(samples)
    return {
        "pool_size": 50,
        "session_first_turn_recall": round(first_turn_hits / count, 6) if count else 0.0,
        "session_any_turn_recall": round(any_turn_hits / count, 6) if count else 0.0,
        "turn_level_recall": round(target_observations / observed_turns, 6) if observed_turns else 0.0,
        "observed_turns": observed_turns,
    }


def technical_metrics(summary: dict[str, object]) -> dict[str, float]:
    """Apply the official formula to one overall or scenario metric summary."""
    mttc = summary.get("mttc")
    efficiency = (
        0.0
        if mttc is None
        else max(0.0, min(1.0, (11.0 - float(mttc)) / 10.0))
    )
    score = (
        0.50 * float(summary["hit_rate_at_10"])
        + 0.30 * float(summary["mrr"])
        + 0.20 * efficiency
    )
    return {
        "efficiency": round(efficiency, 6),
        "recommended_technical_score": round(score, 6),
    }


def add_scenario_technical_scores(metrics: dict[str, object]) -> None:
    """Enrich raw evaluator JSON so scenario scores are evidence, not prose."""
    scenario_metrics = metrics.get("scenario_metrics")
    if not isinstance(scenario_metrics, dict):
        raise ValueError("scenario_metrics must be an object")
    for summary in scenario_metrics.values():
        if not isinstance(summary, dict):
            raise ValueError("each scenario metric must be an object")
        summary.update(technical_metrics(summary))


def assert_scenario_consistency(metrics: dict[str, object], tolerance: float = 2e-6) -> None:
    """Check that scenario summaries aggregate back to the overall metrics."""
    scenario_metrics = metrics.get("scenario_metrics")
    if not isinstance(scenario_metrics, dict) or not scenario_metrics:
        raise ValueError("scenario_metrics must be a non-empty object")
    total = sum(int(summary["sample_count"]) for summary in scenario_metrics.values())
    if total != int(metrics["sample_count"]):
        raise ValueError(f"scenario sample count {total} != overall {metrics['sample_count']}")
    for key in (
        "hit_rate_at_10",
        "mrr",
        "mttc",
        "efficiency",
        "recommended_technical_score",
    ):
        weighted = sum(
            int(summary["sample_count"]) * float(summary[key])
            for summary in scenario_metrics.values()
        ) / total
        if abs(weighted - float(metrics[key])) > tolerance:
            raise ValueError(
                f"scenario-weighted {key} {weighted:.9f} != overall {metrics[key]}"
            )


def worker(mode: str, dataset: str, catalog_path: Path, public_path: Path) -> dict:
    public_samples = load_jsonl(public_path)
    catalog_ids, categories, products = catalog_index(catalog_path)
    samples = samples_for_dataset(dataset, catalog_ids, public_samples)
    agent = RetrievalExperimentAgent(catalog_path, mode)
    try:
        metrics = evaluate(agent, samples, catalog_ids, categories, products)
        add_scenario_technical_scores(metrics)
        assert_scenario_consistency(metrics)
        metrics.pop("sessions", None)
        traces = []
        for sample, audit in zip(samples[:8], agent.session_audits[:8]):
            turns = audit.get("turns", [])
            assert isinstance(turns, list)
            traces.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "turns": [
                        {
                            "turn": turn["turn"],
                            "trace": turn["trace"],
                        }
                        for turn in turns
                    ],
                }
            )
        return {
            "mode": mode,
            "dataset": dataset,
            "metrics": metrics,
            "candidate_recall": candidate_recall(samples, agent.session_audits),
            "performance": {
                "cold_start_seconds": round(agent.startup_seconds, 6),
                "retrieval_calls": len(agent.retrieval_latencies_ms),
                "retrieval_ms_p50": percentile(agent.retrieval_latencies_ms, 0.50),
                "retrieval_ms_p95": percentile(agent.retrieval_latencies_ms, 0.95),
                "respond_ms_p50": percentile(agent.respond_latencies_ms, 0.50),
                "respond_ms_p95": percentile(agent.respond_latencies_ms, 0.95),
                "retrieval_ms_mean": round(
                    statistics.fmean(agent.retrieval_latencies_ms), 6
                ),
                "peak_rss_bytes": peak_rss_bytes(),
            },
            "trace_examples": traces,
        }
    finally:
        agent.close()


def run_worker(
    mode: str,
    dataset: str,
    catalog_path: Path,
    public_path: Path,
    directory: Path,
) -> dict:
    output = directory / f"{mode}-{dataset}.json"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--mode",
        mode,
        "--dataset",
        dataset,
        "--catalog",
        str(catalog_path),
        "--public-set",
        str(public_path),
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"worker failed ({mode}/{dataset}):\n{completed.stdout}\n{completed.stderr}"
        )
    return json.loads(output.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="TASK-303 isolated retrieval comparison")
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--public-set", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--mode", choices=("baseline", "candidate"))
    parser.add_argument("--dataset", choices=("public", "shadow"))
    args = parser.parse_args()
    catalog_path = args.catalog.resolve()
    public_path = args.public_set.resolve()
    if args.worker:
        if not args.mode or not args.dataset:
            parser.error("--worker requires --mode and --dataset")
        result = worker(args.mode, args.dataset, catalog_path, public_path)
    else:
        with tempfile.TemporaryDirectory(prefix="task303-") as temporary:
            directory = Path(temporary)
            runs = {
                f"{mode}_{dataset}": run_worker(
                    mode, dataset, catalog_path, public_path, directory
                )
                for dataset in ("public", "shadow")
                for mode in ("baseline", "candidate")
            }
        result = {
            "schema_version": 1,
            "task": "TASK-303-dual-route-inmemory",
            "code_commit": git_commit(),
            "environment": {
                "python": sys.version.split()[0],
                "platform": sys.platform,
            },
            "catalog": {
                "sha256": sha256(catalog_path),
                "input_bytes": catalog_path.stat().st_size,
                "generated_asset_bytes": 0,
            },
            "dense_retrieval": {
                "implemented": False,
                "reason": "No vetted embedding asset was required for this lightweight experiment.",
            },
            "offline_command": (
                "python experiments/retrieval/evaluate.py --catalog <catalog.jsonl> "
                "--output reports/experiments/TASK-303-results.json"
            ),
            "runs": runs,
        }
        candidate_public = runs["candidate_public"]["metrics"]
        candidate_shadow = runs["candidate_shadow"]["metrics"]
        result["integration_thresholds"] = {
            "public_hit_rate_at_10_gte_0_91": candidate_public["hit_rate_at_10"] >= 0.91,
            "public_technical_score_gte_0_777107": (
                candidate_public["recommended_technical_score"] >= 0.777107
            ),
            "shadow_hit_rate_at_10_gte_0_895": candidate_shadow["hit_rate_at_10"] >= 0.895,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not args.worker:
        summary = {
            key: {
                "metrics": value["metrics"],
                "candidate_recall": value["candidate_recall"],
                "performance": value["performance"],
            }
            for key, value in result["runs"].items()
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
