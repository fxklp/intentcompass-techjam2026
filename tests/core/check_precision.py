"""Immutable pure-ranking comparisons with two disjoint synthetic confirmations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

from tests.core import check_terminal
from tests.core.check_adaptive import ROOT, non_regression, sha256, write_json
from solution.precision_order import VARIANTS


def fresh_dataset(split, identifiers):
    from evaluator.local_evaluator import load_jsonl
    from scripts.shadow_evaluator import SEED, build_samples, select_targets
    excluded = {s["ground_truth"]["parent_asin"] for s in load_jsonl(ROOT / "data/public_set.jsonl")}
    for count, seed in ((200, SEED), (800, "intentcompass-task008-final-20260831"),
                        (800, "intentcompass-task010-final-20260831"),
                        (800, "intentcompass-task011-final-20260831"),
                        (800, "intentcompass-task012-final-20260831")):
        excluded |= set(select_targets(identifiers, excluded, count, seed))
    seed = "intentcompass-task013-confirm-a-20260831"
    targets = select_targets(identifiers, excluded, 800, seed)
    if split == "confirm_b":
        excluded |= set(targets)
        seed = "intentcompass-task013-confirm-b-20260831"
        targets = select_targets(identifiers, excluded, 800, seed)
    elif split != "confirm_a":
        raise ValueError("invalid confirmation split")
    assert len(set(targets)) == 800 and not set(targets) & excluded
    samples = []
    for block in range(4):
        batch = build_samples(targets[block*200:(block+1)*200], f"{seed}:{block}")
        for sample in batch:
            sample["sample_id"] = f"task013_{split}_{block}_{sample['sample_id']}"
        samples.extend(batch)
    digest = hashlib.sha256(("\n".join(s["ground_truth"]["parent_asin"] for s in samples)+"\n").encode()).hexdigest()
    return samples, digest


def run(variant, split, pin=False):
    from scripts.release_check import activate_preset
    from starter.agent import Agent
    original_dataset = check_terminal.dataset
    instances = []

    def dataset(which, identifiers):
        return fresh_dataset(which, identifiers) if which.startswith("confirm_") else original_dataset(which, identifiers)

    def preset():
        activate_preset()
        if variant != "default":
            os.environ["INTENTCOMPASS_PRECISION_ORDER"] = variant

    def make_agent(*args, **kwargs):
        result = Agent(*args, **kwargs)
        instances.append(result)
        return result

    with patch("scripts.release_check.activate_preset", preset), patch.object(check_terminal, "dataset", dataset), patch("starter.agent.Agent", make_agent):
        report = check_terminal.run("default", split, pin)
    report["variant"] = variant
    component = instances[0]._core._adaptive.precision
    report["policy_events"] = {"rank_changes": component.rank_changes if component else 0, "question_changes": 0}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=(*VARIANTS, "default"), required=True)
    parser.add_argument("--split", choices=("public", "shadow", "confirm_a", "confirm_b"), default="public")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--pin", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("use a new output under reports/generated")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = run(args.variant, args.split, args.pin)
    if report["working_tree_dirty"]:
        raise RuntimeError("freeze source before evaluation")
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if baseline["split_target_sha256"] != report["split_target_sha256"]:
            raise ValueError("incomparable split manifests")
        report["regressions"] = non_regression(baseline["metrics"], report["metrics"])
    if args.expected:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        assert report["metrics"] == expected["metrics"] and report.get("sessions") == expected.get("sessions")
        report["equivalent_to_expected"] = sha256(args.expected)
    write_json(output, report)
    print(json.dumps({k: report[k] for k in ("variant", "split", "metrics", "timing", "policy_events", "regressions") if k in report}, indent=2))
    print("sha256=" + sha256(output))


if __name__ == "__main__":
    main()
