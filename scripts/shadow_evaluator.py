from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl  # noqa: E402
from scripts.benchmark_runtime import git_state  # noqa: E402
from starter.agent import Agent  # noqa: E402


SEED = "intentcompass-shadow-v1"
SCENARIO_COUNTS = {
    "buying": 80,
    "browsing": 80,
    "intent_override": 30,
    "boundary": 10,
}
MIN_HIT_RATE_AT_10 = 0.70


def select_targets(
    catalog_ids: set[str],
    public_target_ids: set[str],
    count: int,
    seed: str = SEED,
) -> list[str]:
    candidates = sorted(catalog_ids - public_target_ids)
    if len(candidates) < count:
        raise ValueError(f"need {count} non-public targets; found {len(candidates)}")
    random.Random(seed).shuffle(candidates)
    return candidates[:count]


def scenario_sequence(seed: str = SEED) -> list[str]:
    scenarios = [
        scenario
        for scenario, count in SCENARIO_COUNTS.items()
        for _ in range(count)
    ]
    random.Random(f"{seed}:scenarios").shuffle(scenarios)
    return scenarios


def build_samples(targets: list[str], seed: str = SEED) -> list[dict]:
    scenarios = scenario_sequence(seed)
    if len(targets) != len(scenarios):
        raise ValueError(f"expected {len(scenarios)} targets; got {len(targets)}")
    return [
        {
            "sample_id": f"shadow_{index:04d}",
            "scenario_type": scenario,
            "ground_truth": {"parent_asin": target},
            "user_profile": {
                "purchase_frequency": "shadow holdout",
                "average_prior_rating": None,
                "rating_style": "unknown",
                "preference_tags": [],
                "summary": "Deterministic non-public-target robustness session.",
            },
        }
        for index, (target, scenario) in enumerate(zip(targets, scenarios), start=1)
    ]


def evaluate_shadow(catalog_path: Path, public_path: Path, seed: str = SEED) -> dict:
    public_samples = load_jsonl(public_path)
    public_target_ids = {
        str(sample["ground_truth"]["parent_asin"])
        for sample in public_samples
    }
    catalog_ids, categories, products = catalog_index(catalog_path)
    targets = select_targets(catalog_ids, public_target_ids, sum(SCENARIO_COUNTS.values()), seed)
    if set(targets) & public_target_ids:
        raise RuntimeError("shadow target selection overlaps public targets")
    samples = build_samples(targets, seed)

    agent = Agent(catalog_path)
    try:
        result = evaluate(agent, samples, catalog_ids, categories, products)
    finally:
        agent.close()

    target_digest = hashlib.sha256(("\n".join(targets) + "\n").encode()).hexdigest()
    actual_scenarios = dict(sorted(Counter(item["scenario_type"] for item in samples).items()))
    commit, working_tree_dirty = git_state()
    return {
        "schema_version": 1,
        "commit": commit,
        "working_tree_dirty": working_tree_dirty,
        "method": "official deterministic simulator over catalog targets excluded from public_set",
        "seed": seed,
        "target_ids_sha256": target_digest,
        "public_target_overlap": 0,
        "scenario_counts": actual_scenarios,
        "metrics": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic non-public-target shadow evaluation")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--public-set", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/shadow-results.json"),
    )
    parser.add_argument("--seed", default=SEED)
    args = parser.parse_args()

    result = evaluate_shadow(args.catalog.resolve(), args.public_set.resolve(), args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = {key: value for key, value in result.items() if key != "metrics"}
    summary["metrics"] = {
        key: value for key, value in result["metrics"].items() if key != "sessions"
    }
    print(json.dumps(summary, indent=2))
    hit_rate = result["metrics"].get("hit_rate_at_10")
    if not isinstance(hit_rate, (int, float)) or hit_rate < MIN_HIT_RATE_AT_10:
        print(
            f"SHADOW GATE FAILED: HitRate@10 must be >= {MIN_HIT_RATE_AT_10:.2f}; "
            f"got {hit_rate!r}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
