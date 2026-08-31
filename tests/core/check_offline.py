"""Isolated TASK-006 ablations and locked aggregate confirmation."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from tests.core.check_adaptive import ROOT, sha256, worker, write_json
from tests.core.check_final import inventory, pin_first_cpu

POLICIES = ("baseline", "constraints", "field_bonus", "field_groups", "field_top10", "field_dominance")
CONFIRMATION_SEED = "intentcompass-task006-confirmation-20260831"
BASELINE_COMMIT = "2181f9952763a01d4b6d99b1a4166a5218c77401"


def load_frozen_runtime():
    """Load the two modified runtime modules from the pre-experiment commit.

    This read-only, process-local substitution includes their original hot-path
    cost. Nothing is checked out or written into the worktree.
    """
    hashes = {}
    for name in ("solution.ranker", "solution.adaptive"):
        path = name.replace(".", "/") + ".py"
        source = subprocess.check_output(["git", "show", f"{BASELINE_COMMIT}:{path}"], cwd=ROOT)
        module = importlib.import_module(name)
        exec(compile(source, f"{BASELINE_COMMIT}:{path}", "exec"), module.__dict__)
        hashes[path] = hashlib.sha256(source).hexdigest()
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=POLICIES, default="baseline")
    parser.add_argument("--split", choices=("public","shadow","confirmation"), default="public")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--pin-first-cpu", action="store_true")
    parser.add_argument("--frozen-baseline", action="store_true")
    args = parser.parse_args()
    if args.frozen_baseline and args.policy != "baseline":
        parser.error("frozen runtime can only be used with baseline policy")
    if args.worker:
        from experiments.retrieval.evaluate import peak_rss_bytes
        affinity = pin_first_cpu() if args.pin_first_cpu else None
        reference = load_frozen_runtime() if args.frozen_baseline else None
        if args.split == "confirmation":
            from scripts.shadow_evaluator import evaluate_shadow
            result = evaluate_shadow(ROOT/"data/catalog.jsonl", ROOT/"data/public_set.jsonl", seed=CONFIRMATION_SEED)
            result["metrics"].pop("sessions", None)
        else:
            result = worker(args.split)
        result.update(pid=os.getpid(), peak_memory_bytes=peak_rss_bytes(), cpu_affinity_mask=affinity)
        result["reference_source_sha256"] = reference
        print(json.dumps(result))
        return
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT/"reports/generated").resolve()):
        parser.error("use a NEW file under reports/generated")
    before = inventory()
    env = {k:v for k,v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
    env.update(INTENTCOMPASS_AGENT_MODE="integrated", INTENTCOMPASS_RETRIEVAL="baseline", INTENTCOMPASS_SEMANTIC="off", INTENTCOMPASS_LLM_ALLOW_NETWORK="0", INTENTCOMPASS_OFFLINE_RANKING=args.policy, PYTHONHASHSEED="0")
    command = [sys.executable,"-m","tests.core.check_offline","--worker","--policy",args.policy,"--split",args.split,"--output",str(output)]
    if args.pin_first_cpu:
        command.append("--pin-first-cpu")
    if args.frozen_baseline:
        command.append("--frozen-baseline")
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", check=True)
    result = json.loads(completed.stdout)
    result.update(configuration={"policy":args.policy,"split":args.split,"network":False,"pin_first_cpu":args.pin_first_cpu,"frozen_baseline_commit":BASELINE_COMMIT if args.frozen_baseline else None}, source_sha256=before, sources_unchanged=before==inventory(), python=platform.python_version())
    output.parent.mkdir(parents=True,exist_ok=True)
    write_json(output,result)
    print(json.dumps({k:result.get(k) for k in ("configuration","metrics","timing","peak_memory_bytes","sources_unchanged")},indent=2))
    print("sha256="+sha256(output))
    if not result["sources_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
