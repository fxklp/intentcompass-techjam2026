"""Fresh-process RC2 equivalence check; unchanged scoring and strict provenance."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

from tests.core.check_adaptive import ROOT, non_regression, sha256, write_json
from tests.core.check_final import inventory
VARIANTS = ("rc2",)

CONFIRMATION_SEED = "intentcompass-task008-final-20260831"


def run(variant, split, pin=False):
    from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl
    from scripts.benchmark_runtime import percentile
    from scripts.release_check import activate_preset, validate_payload
    from experiments.retrieval.evaluate import peak_rss_bytes
    from starter.agent import Agent
    if pin:
        from tests.core.check_final import pin_first_cpu
        affinity = pin_first_cpu()
    else:
        affinity = None
    activate_preset()
    if variant == "baseline":
        os.environ["INTENTCOMPASS_CATEGORY_ORDER"] = "off"
    identifiers, categories, products = catalog_index(ROOT / "data/catalog.jsonl")
    samples = load_jsonl(ROOT / "data/public_set.jsonl")
    split_metadata = {"seed": None, "public_target_overlap": len(samples)}
    if split != "public":
        from scripts.shadow_evaluator import SEED, build_samples, select_targets
        public_targets = {str(s["ground_truth"]["parent_asin"]) for s in samples}
        original = select_targets(identifiers, public_targets, 200, SEED)
        if split == "shadow":
            samples = build_samples(original, SEED)
            split_metadata = {"seed": SEED, "public_target_overlap": 0}
        else:
            targets = select_targets(identifiers, public_targets | set(original), 800, CONFIRMATION_SEED)
            if len(set(targets)) != 800 or set(targets) & (public_targets | set(original)):
                raise RuntimeError("invalid confirmation split")
            split_metadata = {"seed": CONFIRMATION_SEED, "public_target_overlap": 0, "original_shadow_target_overlap": 0}
            samples = []
            for block in range(4):
                batch = build_samples(targets[block*200:(block+1)*200], f"{CONFIRMATION_SEED}:{block}")
                for item in batch:
                    item["sample_id"] = f"confirmation_{block}_{item['sample_id']}"
                samples.extend(batch)
    split_metadata["target_ids_sha256"] = hashlib.sha256(('\n'.join(str(s["ground_truth"]["parent_asin"]) for s in samples) + '\n').encode()).hexdigest()
    before = inventory()
    times = []
    attempts = []

    def deny(*args, **kwargs):
        attempts.append(1)
        raise OSError("network disabled during research proof")

    with patch.object(socket.socket, "connect", deny), patch.object(socket.socket, "connect_ex", deny):
        started = time.perf_counter()
        agent = Agent(ROOT / "data/catalog.jsonl")
        initialization = time.perf_counter() - started

        class Observed:
            def reset(self, *args):
                agent.reset(*args)

            def respond(self, *args):
                start = time.perf_counter()
                response = agent.respond(*args)
                times.append((time.perf_counter() - start) * 1000)
                validate_payload(response, identifiers, args[-1])
                return response

        try:
            result = evaluate(Observed(), samples, identifiers, categories, products)
        finally:
            agent.close()
    if attempts or before != inventory():
        raise RuntimeError("network attempted or protected files mutated")
    metrics = {k: v for k, v in result.items() if k != "sessions"}
    report = {
        "variant": variant, "split": split, "metrics": metrics,
        "split_metadata": split_metadata, "cpu_affinity_mask": affinity,
        "source_sha256": before, "sources_unchanged": True, "network_attempts": 0,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "timing": {"initialization_s": initialization, "response_count": len(times),
                   "total_response_ms": sum(times),
                   "p50_ms": percentile(times, .5), "p95_ms": percentile(times, .95), "p99_ms": percentile(times, .99)},
        "peak_memory_bytes": peak_rss_bytes(), "pid": os.getpid(),
        "commit": subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_dirty": bool(subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "scope": "Public development or synthetic aggregate validation, not official hidden evaluation",
    }
    if split == "public":
        report["sessions"] = result["sessions"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("baseline", *VARIANTS), default="rc2")
    parser.add_argument("--split", choices=("public", "shadow", "confirmation"), default="public")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--expected-report", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--pin-first-cpu", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(run(args.variant, args.split, args.pin_first_cpu)))
        return
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("use a new reports/generated JSON file")
    reference = args.reference_root.resolve() if args.reference_root else ROOT
    if args.reference_root and args.variant != "baseline":
        parser.error("reference root is only for the unchanged RC1 baseline")
    before = inventory(reference)
    environment = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
    environment.update(PYTHONHASHSEED="0", PYTHONUTF8="1")
    command = [sys.executable, "-B", "-m", "tests.core.check_rc2", "--worker", "--variant", args.variant, "--split", args.split, "--output", str(output)]
    if args.pin_first_cpu:
        command.append("--pin-first-cpu")
    if args.reference_root:
        # Same observation function, but import only the untouched reference
        # checkout's Agent/evaluator. No module replacement or reference writes.
        setup = ("import hashlib,json,os,platform,socket,subprocess,time\n"
                 "from pathlib import Path\nfrom unittest.mock import patch\n"
                 "from tests.core.check_final import inventory\nROOT=Path.cwd()\n"
                 f"CONFIRMATION_SEED={CONFIRMATION_SEED!r}\n")
        code = setup + inspect.getsource(run) + f"\nprint(json.dumps(run('baseline', {args.split!r}, {args.pin_first_cpu!r})))"
        command = [sys.executable, "-B", "-c", code]
    completed = subprocess.run(command, cwd=reference, env=environment, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError("research worker failed:\n" + completed.stderr)
    report = json.loads(completed.stdout)
    if before != inventory(reference):
        raise RuntimeError("source changed while worker ran")
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if baseline["split"] != args.split:
            raise ValueError("incomparable splits")
        if baseline.get("split_metadata", {}).get("target_ids_sha256") not in (None, report["split_metadata"]["target_ids_sha256"]):
            raise ValueError("incomparable target manifests")
        report["regressions"] = non_regression(baseline["metrics"], report["metrics"])
    report["runner_sha256"] = sha256(Path(__file__))
    if args.expected_report:
        expected = json.loads(args.expected_report.read_text(encoding="utf-8"))
        if report["metrics"] != expected["metrics"] or report.get("sessions") != expected.get("sessions"):
            raise RuntimeError("RC2 differs from its frozen research candidate")
        report["equivalent_to_frozen_candidate"] = True
        report["expected_report_sha256"] = sha256(args.expected_report)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(json.dumps({k: report[k] for k in ("variant", "split", "metrics", "timing", "peak_memory_bytes", "regressions") if k in report}, indent=2))
    print("sha256=" + sha256(output))


if __name__ == "__main__":
    main()
