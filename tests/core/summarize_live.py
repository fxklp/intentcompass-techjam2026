"""Verify the bounded live screen and the subsequent offline release recheck."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from solution.api_budget import BudgetLedger
from tests.core.check_adaptive import ROOT, non_regression, sha256, write_json


LIVE = {
    "qwen3.7-flash": "task004-live-qwen37-indices-screen1.json",
    **{name: f"task004-live-indices-{name}.json" for name in (
        "qwen3.8-flash", "qwen3.8-max", "deepseek-v4-flash", "deepseek-v4-pro"
    )},
}


def verify_runtime(report: dict) -> None:
    for name, digest in report["source_sha256"].items():
        if name.startswith(("solution/", "starter/", "evaluator/", "data/")):
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT) or sha256(path) != digest:
                raise ValueError("recorded runtime or frozen inputs do not match")


def main() -> None:
    directory = ROOT / "reports/generated"
    evidence = {}
    screens = []
    for model, filename in LIVE.items():
        path = directory / filename
        report = json.loads(path.read_text(encoding="utf-8"))
        verify_runtime(report)
        if not report["sources_unchanged"] or report["model"] != model:
            raise ValueError("invalid live evidence")
        if report["sample_counts"] != {name: 3 for name in ("buying", "browsing", "boundary", "intent_override")}:
            raise ValueError("live screens must use the same fixed public subset")
        failures = []
        if report["status"] != "completed":
            failures.append("strict screen aborted; no complete quality score")
        else:
            failures.extend(non_regression(report["baseline_metrics"], report["metrics"]))
            if report["latency_p95_ms"] > report["baseline_latency_p95_ms"] * 1.05:
                failures.append("response latency regresses")
        screens.append({
            "model": model, "status": report["status"],
            "successful_rankings": report["semantic_reasons"].get("model_ranked", 0),
            "metrics": report["metrics"], "baseline_metrics": report["baseline_metrics"],
            "response_p95_ms": report["latency_p95_ms"],
            "baseline_p95_ms": report["baseline_latency_p95_ms"],
            "promotion_failures": failures,
            "screen_cost_bound_rmb": round(report["budget"]["conservative_cost_rmb"] - report["budget_before"]["conservative_cost_rmb"], 6),
        })
        evidence[filename] = sha256(path)
    if any(not item["promotion_failures"] for item in screens):
        raise ValueError("a passing live candidate needs a separate full validation decision")

    reports = {}
    for mode in ("baseline", "integrated"):
        for number in range(1, 4):
            name = f"task004-postapi-{mode}-{number}.json"
            path = directory / name
            reports[name] = json.loads(path.read_text(encoding="utf-8"))
            evidence[name] = sha256(path)
            if reports[name]["working_tree_dirty"]:
                raise ValueError("release evidence must use a clean checkout")
            if mode == "integrated":
                verify_runtime(reports[name])
    regressions = []
    for number in range(1, 4):
        regressions.extend(non_regression(reports[f"task004-postapi-baseline-{number}.json"]["metrics"], reports[f"task004-postapi-integrated-{number}.json"]["metrics"]))
    path = directory / "task004-postapi-shadow.json"
    shadow = json.loads(path.read_text(encoding="utf-8"))
    verify_runtime(shadow)
    if shadow["working_tree_dirty"]:
        raise ValueError("shadow release evidence must use a clean checkout")
    evidence[path.name] = sha256(path)
    # This is a frozen local synthetic reference, NOT the organizer private set.
    prior_path = directory / "task004-final-shadow-baseline.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    evidence[prior_path.name] = sha256(prior_path)
    regressions.extend(non_regression(prior["metrics"], shadow["metrics"]))

    timing = {}
    for mode in ("baseline", "integrated"):
        group = [reports[f"task004-postapi-{mode}-{n}.json"] for n in range(1,4)]
        timing[mode] = {key: statistics.median(item["timing"]["respond_latency_ms"][key] for item in group) for key in ("mean", "p50", "p95", "p99")}
        timing[mode]["peak_memory_bytes"] = statistics.median(item["peak_memory_bytes"] for item in group)
        timing[mode]["initialization_seconds"] = statistics.median(item["timing"]["agent_initialization_seconds"] for item in group)
    old, new = timing["baseline"], timing["integrated"]
    if new["p95"] > old["p95"]*1.05:
        regressions.append("default response p95 exceeds the 5% measurement tolerance")
    if new["peak_memory_bytes"]-old["peak_memory_bytes"] > 16*1024*1024:
        regressions.append("default memory exceeds the predeclared +16MiB allowance")
    result = {
        "status": "local_freeze_eligible_for_independent_reproduction" if not regressions else "recheck_failed",
        "decision": "retain integrated lexical default; no live model promoted",
        "runtime_commit": reports["task004-postapi-integrated-1.json"]["commit"],
        "bounded_model_screen_complete": True,
        "public": reports["task004-postapi-integrated-1.json"]["metrics"],
        "shadow": shadow["metrics"], "regressions": regressions,
        "timing_medians": timing, "live_screens": screens,
        "api_budget": BudgetLedger(ROOT / "artifacts/api-budget/task004.sqlite3").summary(),
        "evidence_sha256": evidence,
        "limits": [
            "Twelve public sessions screen candidates; not full-public or private API accuracy",
            "No qualifying API candidate was expanded to full Public or Shadow",
            "Unknown failed calls retain budget reservations; estimates are not invoices",
            "Offline dense/cross-encoder and live LLM routes are optional, not default gains",
            "No claim of global optimum, official passing score, completed submission materials or remote merge",
            "Liu/Cheng independent reproduction remains pending; no Wang task",
        ],
    }
    output = directory / "task004-postapi-summary.json"
    write_json(output, result)
    print(json.dumps({key: result[key] for key in ("status", "runtime_commit", "decision", "regressions", "timing_medians", "api_budget")}, indent=2))
    print("summary_sha256=" + sha256(output))
    if regressions:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
