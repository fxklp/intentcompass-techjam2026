"""Offline proof runner, deliberately outside the production import tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def non_regression(baseline: dict, candidate: dict) -> list[str]:
    failures = []
    groups = [("overall", baseline, candidate)]
    for name, metrics in baseline["scenario_metrics"].items():
        other = candidate.get("scenario_metrics", {}).get(name)
        if other is None:
            failures.append(f"{name}: missing scenario")
        else:
            groups.append((name, metrics, other))
    for name, old, new in groups:
        for metric, direction in (("hit_rate_at_10", 1), ("mrr", 1), ("mttc", -1)):
            if (new[metric] - old[metric]) * direction < -1e-6:
                failures.append(f"{name}.{metric}: {old[metric]} -> {new[metric]}")
    return failures


def worker(split: str) -> dict:
    # These are unchanged team wrappers around the unchanged official evaluator.
    if split == "public":
        from scripts.benchmark_runtime import run_benchmark

        report = run_benchmark(ROOT / "data/catalog.jsonl", ROOT / "data/public_set.jsonl")
        report["metrics"] = report.pop("official_metrics")
        return report
    from scripts.shadow_evaluator import evaluate_shadow

    report = evaluate_shadow(ROOT / "data/catalog.jsonl", ROOT / "data/public_set.jsonl")
    # Do not hand shadow target records to the algorithm lane.
    report["metrics"].pop("sessions", None)
    return report


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def source_inventory() -> list[Path]:
    return [
        *sorted((ROOT / "solution").rglob("*.py")),
        *sorted((ROOT / "starter").glob("*.py")),
        *sorted((ROOT / "tests/core").glob("*.py")),
        ROOT / "scripts/benchmark_runtime.py",
        ROOT / "scripts/shadow_evaluator.py",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/generated/task003"))
    parser.add_argument("--worker", choices=("public", "shadow"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker)))
        return
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports/generated").resolve()):
        raise ValueError("proof output must be under reports/generated")
    output.mkdir(parents=True, exist_ok=False)
    protected = [ROOT / "data/catalog.jsonl", ROOT / "data/public_set.jsonl", *sorted((ROOT / "evaluator").glob("*.py"))]
    source = source_inventory()
    hashes_before = {path.relative_to(ROOT).as_posix(): sha256(path) for path in [*protected, *source]}
    evidence = {}
    for mode in ("baseline", "adaptive"):
        for split in ("public", "shadow"):
            key = f"{mode}-{split}"
            command = [sys.executable, "-m", "tests.core.check_adaptive", "--worker", split]
            environment = dict(os.environ, INTENTCOMPASS_AGENT_MODE=mode, INTENTCOMPASS_RETRIEVAL="baseline", INTENTCOMPASS_SEMANTIC="off", INTENTCOMPASS_LLM_ALLOW_NETWORK="0", PYTHONHASHSEED="0")
            started = time.perf_counter()
            print(f"Running {key} in an isolated process...", flush=True)
            completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
            report = json.loads(completed.stdout)
            report["core_mode"] = mode
            report["retrieval_backend"] = "baseline"
            report["wall_seconds"] = round(time.perf_counter() - started, 6)
            report["command"] = f"INTENTCOMPASS_AGENT_MODE={mode} INTENTCOMPASS_RETRIEVAL=baseline INTENTCOMPASS_SEMANTIC=off INTENTCOMPASS_LLM_ALLOW_NETWORK=0 python -m tests.core.check_adaptive --worker {split}"
            write_json(output / f"{key}.json", report)
            evidence[key] = report
            print(json.dumps({"run": key, "metrics": report["metrics"]}), flush=True)
    hashes_after = {path.relative_to(ROOT).as_posix(): sha256(path) for path in [*protected, *source_inventory()]}
    if hashes_before != hashes_after:
        raise RuntimeError("source/data changed during proof run; evidence is not promotable")
    regressions = {split: non_regression(evidence[f"baseline-{split}"]["metrics"], evidence[f"adaptive-{split}"]["metrics"]) for split in ("public", "shadow")}
    manifest = {
        "schema_version": 1,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_sha256": hashes_before,
        "outputs_sha256": {path.name: sha256(path) for path in sorted(output.glob("*.json"))},
        "regressions": regressions,
        "promotion": "eligible_for_independent_review" if not any(regressions.values()) else "retain_baseline",
        "limits": ["Lexical core only, not dense retrieval or learned semantic reranking", "Shadow is a synthetic local robustness set, not the organizer private set", "No automatic default switch or merge"],
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"promotion": manifest["promotion"], "regressions": regressions}, indent=2))


if __name__ == "__main__":
    main()
