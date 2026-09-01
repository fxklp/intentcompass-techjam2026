"""Frozen offline recovery evaluation with immutable sources and disjoint splits."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import time
from unittest.mock import patch

from tests.core.check_adaptive import ROOT, non_regression, sha256, write_json
from tests.core.check_final import inventory, pin_first_cpu


def dataset(split, identifiers):
    from evaluator.local_evaluator import load_jsonl
    from scripts.shadow_evaluator import SEED, build_samples, select_targets
    from tests.core.check_rc2 import CONFIRMATION_SEED
    samples = load_jsonl(ROOT / "data/public_set.jsonl")
    public = {s["ground_truth"]["parent_asin"] for s in samples}
    if split != "public":
        original = select_targets(identifiers, public, 200, SEED)
        if split == "shadow":
            samples = build_samples(original, SEED)
        else:
            excluded = public | set(original)
            excluded |= set(select_targets(identifiers, excluded, 800, CONFIRMATION_SEED))
            seed010 = "intentcompass-task010-final-20260831"
            old = select_targets(identifiers, excluded, 800, seed010)
            if split == "confirmation010":
                seed, targets, prefix = seed010, old, "task010"
            else:
                excluded |= set(old)
                seed, prefix = "intentcompass-task011-final-20260831", "task011"
                targets = select_targets(identifiers, excluded, 800, seed)
            assert not set(targets) & excluded and len(set(targets)) == 800
            samples = []
            for block in range(4):
                batch = build_samples(targets[block*200:(block+1)*200], f"{seed}:{block}")
                for s in batch:
                    s["sample_id"] = f"{prefix}_{block}_{s['sample_id']}"
                samples.extend(batch)
    digest = hashlib.sha256(("\n".join(s["ground_truth"]["parent_asin"] for s in samples)+"\n").encode()).hexdigest()
    return samples, digest


def run(variant, split, pin=False):
    from evaluator.local_evaluator import catalog_index, evaluate
    from scripts.release_check import activate_preset, validate_payload
    from scripts.benchmark_runtime import percentile
    from experiments.retrieval.evaluate import peak_rss_bytes
    from starter.agent import Agent
    activate_preset()
    if variant != "default":
        os.environ["INTENTCOMPASS_TERMINAL_RECOVERY"] = "off" if variant == "rc2" else variant
    affinity = pin_first_cpu() if pin else None
    identifiers, categories, products = catalog_index(ROOT / "data/catalog.jsonl")
    samples, split_hash = dataset(split, identifiers)
    before = inventory()
    timings, errors, attempts, recoveries = [], [], [], []

    def deny(*a, **kw):
        attempts.append(1)
        raise OSError("network disabled")

    with patch.object(socket.socket, "connect", deny), patch.object(socket.socket, "connect_ex", deny):
        started = time.perf_counter()
        agent = Agent(ROOT / "data/catalog.jsonl")
        initialization = time.perf_counter()-started

        class Observed:
            def reset(self, *args):
                agent.reset(*args)

            def respond(self, *args):
                try:
                    start = time.perf_counter()
                    response = agent.respond(*args)
                    timings.append((time.perf_counter()-start)*1000)
                    validate_payload(response, identifiers, args[-1])
                    controller = agent._core._adaptive.terminal
                    if controller and controller.last_active:
                        recoveries.append(args[2])
                    return response
                except Exception as exc:
                    errors.append(type(exc).__name__ + ": " + str(exc))
                    raise
        try:
            result = evaluate(Observed(), samples, identifiers, categories, products)
        finally:
            agent.close()
    if errors or attempts or before != inventory():
        raise RuntimeError(f"invalid run: errors={errors[:3]}, network={len(attempts)}")
    sessions = result.pop("sessions")
    report = {"variant": variant, "split": split, "metrics": result,
              "split_target_sha256": split_hash, "source_sha256": before,
              "network_attempts": len(attempts), "runtime_errors": errors,
              "recovery_response_count": len(recoveries), "cpu_affinity_mask": affinity,
              "timing": {"initialization_s": initialization, "response_count": len(timings),
                         "p50_ms": percentile(timings, .5), "p95_ms": percentile(timings, .95),
                         "p99_ms": percentile(timings, .99)},
              "peak_memory_bytes": peak_rss_bytes(), "pid": os.getpid(),
              "environment": {"python": platform.python_version(), "platform": platform.platform()},
              "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())}
    if split == "public":
        report["sessions"] = sessions
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("rc2", "terminal", "lastchance", "default"), default="default")
    parser.add_argument("--split", choices=("public", "shadow", "confirmation010", "confirmation"), default="public")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--pin", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("use a new output under reports/generated")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = run(args.variant, args.split, args.pin)
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if baseline.get("split_target_sha256", report["split_target_sha256"]) != report["split_target_sha256"]:
            raise ValueError("incomparable sample manifest")
        report["regressions"] = non_regression(baseline["metrics"], report["metrics"])
        if args.split == "public":
            old = {s["sample_id"]: s for s in baseline["sessions"] if s["hit"]}
            report["previous_hits_unchanged"] = all(s == old[s["sample_id"]] for s in report["sessions"] if s["sample_id"] in old)
    if args.expected:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        assert report["metrics"] == expected["metrics"] and report.get("sessions") == expected.get("sessions"), "extraction changed behavior"
        report["equivalent_to_expected"] = sha256(args.expected)
    write_json(output, report)
    print(json.dumps({k: report[k] for k in ("variant", "split", "metrics", "timing", "regressions", "previous_hits_unchanged") if k in report}, indent=2))
    print("sha256=" + sha256(output))


if __name__ == "__main__":
    main()
