"""Candidate-only evaluator for TASK-306; never changes official data or scoring."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REFERENCES = {
    "public": {"hit_rate_at_10": .98, "mrr": .696861, "mttc": 3.755},
    "shadow": {"hit_rate_at_10": .965, "mrr": .703615, "mttc": 3.545},
    "confirm_a": {"hit_rate_at_10": .95625, "mrr": .695408, "mttc": 3.45375},
    "confirm_b": {"hit_rate_at_10": .95625, "mrr": .698810, "mttc": 3.515},
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=tuple(REFERENCES), required=True)
    parser.add_argument("--semantic", choices=("off", "local"), default="local")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("use a new output under reports/generated")
    output.parent.mkdir(parents=True, exist_ok=True)

    from scripts.release_check import activate_preset as activate_rc3
    from starter.agent import Agent as RealAgent
    from tests.core import check_terminal
    from tests.core.check_adaptive import sha256, write_json
    from tests.core.check_final_policy import reproduction_dataset

    counters = Counter()
    original_dataset = check_terminal.dataset

    def candidate_preset() -> None:
        activate_rc3()
        os.environ.update({
            "INTENTCOMPASS_RETRIEVAL": "capability",
            "INTENTCOMPASS_SEMANTIC": args.semantic,
            "INTENTCOMPASS_SEMANTIC_ASSETS": str((ROOT / "artifacts/semantic").resolve()),
            "INTENTCOMPASS_LLM_ALLOW_NETWORK": "0",
        })

    def dataset(split, identifiers):
        return reproduction_dataset(split, identifiers) if split.startswith("confirm_") else original_dataset(split, identifiers)

    class ObservedAgent:
        def __init__(self, *items, **kwargs):
            self.inner = RealAgent(*items, **kwargs)
            self._core = self.inner._core

        def reset(self, *items):
            return self.inner.reset(*items)

        def close(self):
            return self.inner.close()

        def respond(self, *items):
            response = self.inner.respond(*items)
            trace = self._core._adaptive.sessions[str(items[0])].last_trace
            counters["responses"] += 1
            counters["route:" + trace["intent_route"]] += 1
            counters["workflow:" + trace["workflow"]] += 1
            for route in trace["retrieval"]["routes"]:
                counters["retrieval:" + route] += 1
            for reason in trace["retrieval"]["reason_codes"]:
                counters["reason:" + reason.split(":", 1)[0]] += 1
            counters["semantic:" + trace["semantic"]["reason"]] += 1
            return response

    with patch("scripts.release_check.activate_preset", candidate_preset), \
            patch.object(check_terminal, "dataset", dataset), \
            patch("starter.agent.Agent", ObservedAgent):
        report = check_terminal.run("default", args.split)

    metrics = report["metrics"]
    reference = REFERENCES[args.split]
    report.update({
        "task": "TASK-306",
        "configuration": {
            "mode": "integrated", "retrieval": "capability", "semantic": args.semantic,
            "network": False, "semantic_assets": "artifacts/semantic",
        },
        "capability_events": dict(sorted(counters.items())),
        "reference_rc3": reference,
        "delta_vs_rc3": {key: round(metrics[key] - reference[key], 6) for key in reference},
        "tolerance_pass": {
            "hit_rate_at_10": metrics["hit_rate_at_10"] >= reference["hit_rate_at_10"] - .005,
            "mrr": metrics["mrr"] >= reference["mrr"] - .005,
            "mttc": metrics["mttc"] <= reference["mttc"] + .10,
        },
        "purpose": "target-blind candidate evaluation; TASK-014 sets are prior-used reproductions, not holdouts",
    })
    write_json(output, report)
    print(json.dumps({
        "split": args.split, "metrics": metrics, "delta_vs_rc3": report["delta_vs_rc3"],
        "tolerance_pass": report["tolerance_pass"], "timing": report["timing"],
        "capability_events": report["capability_events"], "sha256": sha256(output),
    }, indent=2))


if __name__ == "__main__":
    main()
