"""Materialize deterministic historical evaluator inputs under ignored reports/."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import catalog_index, load_jsonl
from scripts.shadow_evaluator import SCENARIO_COUNTS, SEED, build_samples, select_targets


def build(name: str, catalog: Path) -> tuple[list[dict], str]:
    identifiers, _, _ = catalog_index(catalog)
    public = load_jsonl(ROOT / "data/public_set.jsonl")
    if name == "public":
        samples = public
    elif name == "shadow":
        excluded = {str(item["ground_truth"]["parent_asin"]) for item in public}
        targets = select_targets(identifiers, excluded, sum(SCENARIO_COUNTS.values()), SEED)
        samples = build_samples(targets, SEED)
    else:
        from tests.core.check_final_policy import reproduction_dataset
        samples, _ = reproduction_dataset(name, identifiers)
    digest = hashlib.sha256(("\n".join(str(item["ground_truth"]["parent_asin"]) for item in samples) + "\n").encode()).hexdigest()
    return samples, digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("public", "shadow", "confirm_a", "confirm_b"), required=True)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("output must be a new file under reports/generated")
    samples, digest = build(args.dataset, args.catalog)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(item, separators=(",", ":")) + "\n" for item in samples), encoding="utf-8", newline="\n")
    manifest = output.with_suffix(output.suffix + ".manifest.json")
    manifest.write_text(json.dumps({"dataset": args.dataset, "samples": len(samples), "target_ids_sha256": digest}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), "samples": len(samples), "target_ids_sha256": digest}))


if __name__ == "__main__":
    main()
