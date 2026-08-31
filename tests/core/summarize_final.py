"""Verify recorded offline evidence against current runtime and summarize it."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from solution.api_budget import BudgetLedger
from tests.core.check_adaptive import ROOT, non_regression, sha256, write_json


def main() -> None:
    directory = ROOT / "reports/generated"
    names = [f"task004-final-{mode}-{number}.json" for number in range(1,4) for mode in ("baseline","integrated")]
    names += [f"task004-final-shadow-{mode}.json" for mode in ("baseline","integrated")]
    reports = {name: json.loads((directory / name).read_text(encoding="utf-8")) for name in names}
    candidate_reports = [value for key,value in reports.items() if "integrated" in key]
    for report in candidate_reports:
        if report["working_tree_dirty"]:
            raise ValueError("candidate evidence was produced from a dirty checkout")
        for name, digest in report["source_sha256"].items():
            if name.startswith(("solution/", "starter/", "evaluator/", "data/")):
                path = (ROOT / name).resolve()
                if not path.is_relative_to(ROOT) or sha256(path) != digest:
                    raise ValueError("current runtime or frozen inputs differ from evidence")
    public_failures = []
    for number in range(1,4):
        public_failures.extend(non_regression(reports[f"task004-final-baseline-{number}.json"]["metrics"], reports[f"task004-final-integrated-{number}.json"]["metrics"]))
    shadow_failures = non_regression(reports["task004-final-shadow-baseline.json"]["metrics"], reports["task004-final-shadow-integrated.json"]["metrics"])
    timing = {}
    for mode in ("baseline", "integrated"):
        group = [reports[f"task004-final-{mode}-{number}.json"] for number in range(1,4)]
        timing[mode] = {key: statistics.median(item["timing"]["respond_latency_ms"][key] for item in group) for key in ("mean","p50","p95","p99")}
        timing[mode]["initialization_seconds"] = statistics.median(item["timing"]["agent_initialization_seconds"] for item in group)
        timing[mode]["peak_memory_bytes"] = statistics.median(item["peak_memory_bytes"] for item in group)
    old, new = timing["baseline"], timing["integrated"]
    memory_delta = new["peak_memory_bytes"] - old["peak_memory_bytes"]
    passed = not public_failures and not shadow_failures and new["p95"] <= old["p95"]*1.05 and memory_delta <= 16*1024*1024
    result = {
        "status": "offline_stage_eligible" if passed else "offline_stage_failed",
        "complete_project_optimization": False,
        "runtime_commit": candidate_reports[0]["commit"],
        "all_candidate_runtime_hashes_match_current": True,
        "public": reports["task004-final-integrated-1.json"]["metrics"],
        "shadow": reports["task004-final-shadow-integrated.json"]["metrics"],
        "public_regressions": public_failures, "shadow_regressions": shadow_failures,
        "three_run_median_timing": timing,
        "mean_latency_reduction_percent": (1-new["mean"]/old["mean"])*100,
        "p95_latency_reduction_percent": (1-new["p95"]/old["p95"])*100,
        "additional_peak_mib": memory_delta/1048576,
        "additional_initialization_seconds": new["initialization_seconds"]-old["initialization_seconds"],
        "api_budget": BudgetLedger(ROOT / "artifacts/api-budget/task004.sqlite3").summary(),
        "pending": ["Qwen and DeepSeek real account credits, keys, region and live comparisons", "Final judge simulation after live API selection", "Independent Liu/Cheng simple reproduction; no Wang task", "Submission materials and public visibility are not approved by this software check"],
        "evidence_sha256": {name:sha256(directory/name) for name in names},
        "limits": ["Shadow is synthetic, not organizer private scoring", "Timing applies to the fixed 200-session public workload on this Windows CPU", "Small memory and startup costs remain; not every resource measurement improves", "No claim of globally optimal algorithm or official passing grade"],
    }
    output = directory / "task004-final-summary.json"
    write_json(output, result)
    print(json.dumps({key:value for key,value in result.items() if key not in {"public","shadow","evidence_sha256"}}, indent=2))
    print("summary_sha256=" + sha256(output))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
