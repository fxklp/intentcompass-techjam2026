"""Paired, isolated API-system evaluation; official evaluator stays unchanged."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path

from solution.api_budget import BudgetLedger
from solution.api_demand import DEMAND_VARIANTS
from solution.chat_reranker import RATES
from tests.core.check_adaptive import ROOT, non_regression, sha256, write_json
from tests.core.check_final import inventory


def quality_verdict(baseline: dict, candidate: dict) -> dict:
    changes = {name: candidate[name] - baseline[name] for name in ("hit_rate_at_10", "mrr", "mttc")}
    regressions = non_regression(baseline, candidate)
    gains = [changes["hit_rate_at_10"] > 1e-6, changes["mrr"] > 1e-6, changes["mttc"] < -1e-6]
    return {"deltas": changes, "regressions": regressions,
            "preliminary_quality_pass": not regressions and any(gains),
            "all_three_strictly_better": not regressions and all(gains)}


def latency_summary(values: list[float]) -> dict:
    from scripts.benchmark_runtime import percentile
    if not values:
        return {"count": 0, "mean": None, "p50": None, "p95": None, "max": None}
    return {"count": len(values), "mean": statistics.fmean(values),
            "p50": percentile(values, .5), "p95": percentile(values, .95), "max": max(values)}


class ObservedAgent:
    def __init__(self, catalog):
        from starter.agent import Agent
        started = time.perf_counter()
        self.agent = Agent(catalog)
        self.init_seconds = time.perf_counter() - started
        self.latencies, self.attempted_latencies = [], []
        self.reasons = Counter()
        self.session_count = 0
        self.exceptions = 0

    def reset(self, session_id, profile):
        self.session_count += 1
        if self.session_count % 10 == 0:
            print(f"sessions_started={self.session_count} api_attempts={len(self.attempted_latencies)}", file=sys.stderr, flush=True)
        self.agent.reset(session_id, profile)

    def respond(self, session_id, message, turn, top_k):
        started = time.perf_counter()
        try:
            result = self.agent.respond(session_id, message, turn, top_k)
        except Exception:
            self.exceptions += 1
            self.latencies.append(1000 * (time.perf_counter() - started))
            raise
        elapsed = 1000 * (time.perf_counter() - started)
        self.latencies.append(elapsed)
        trace = self.agent._core._adaptive.sessions[session_id].last_trace["semantic"]
        self.reasons[trace["reason"]] += 1
        if trace["attempted"]:
            self.attempted_latencies.append(elapsed)
        return result


def worker(split, per_scenario):
    from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl
    from experiments.retrieval.evaluate import peak_rss_bytes
    samples = load_jsonl(ROOT / "data/public_set.jsonl")
    ids, categories, products = catalog_index(ROOT / "data/catalog.jsonl")
    if split == "shadow":
        from scripts.shadow_evaluator import select_targets, build_samples, SCENARIO_COUNTS
        # Selection is evaluator-side; never disclose targets to the Agent.
        targets = select_targets(ids, {s["ground_truth"]["parent_asin"] for s in samples}, sum(SCENARIO_COUNTS.values()))
        samples = build_samples(targets)
    counts, selected = Counter(), []
    for sample in samples:
        scenario = sample["scenario_type"]
        if per_scenario == 0 or counts[scenario] < per_scenario:
            selected.append(sample)
            counts[scenario] += 1
    agent = ObservedAgent(ROOT / "data/catalog.jsonl")
    started = time.perf_counter()
    try:
        result = evaluate(agent, selected, ids, categories, products)
        failure = getattr(agent.agent._core._adaptive.semantic, "last_failure", None)
    finally:
        agent.agent.close()
    if split == "shadow":
        result.pop("sessions", None)
    return {"metrics": result, "scenario_counts": dict(counts),
            "selection_sha256": hashlib.sha256(json.dumps([s["sample_id"] for s in selected]).encode()).hexdigest(),
            "latency_ms": latency_summary(agent.latencies),
            "attempted_latency_ms": latency_summary(agent.attempted_latencies),
            "semantic_reasons": dict(agent.reasons), "provider_failure": failure,
            "agent_exceptions": agent.exceptions,
            "initialization_seconds": agent.init_seconds, "evaluation_seconds": time.perf_counter() - started,
            "peak_memory_bytes": peak_rss_bytes(), "pid": os.getpid()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--variant", choices=tuple(DEMAND_VARIANTS), default="demand20")
    parser.add_argument("--model", choices=tuple(RATES), default="qwen3.8-max")
    parser.add_argument("--split", choices=("public", "shadow"), default="public")
    parser.add_argument("--per-scenario", type=int, default=3, help="0 means the full 200")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--credentials-file", type=Path)
    parser.add_argument("--run-budget-rmb", type=Decimal, default=Decimal("2"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.per_scenario <= 80:
        parser.error("per-scenario must be 0..80")
    if args.worker:
        print(json.dumps(worker(args.split, args.per_scenario)))
        return
    if args.output is None or args.ledger is None:
        parser.error("output and existing ledger required")
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("output must be a NEW file under reports/generated")
    if not args.run_budget_rmb.is_finite() or not 0 < args.run_budget_rmb <= 20:
        parser.error("run budget must be finite, positive and <=20 RMB")
    if args.credentials_file:
        from scripts.api_credentials import load_credentials
        try:
            load_credentials(args.credentials_file)
        except (OSError, ValueError):
            parser.error("credential file invalid; values suppressed")
    ledger = BudgetLedger(args.ledger.resolve())
    budget_before = ledger.summary()
    provider = RATES[args.model][0]
    if args.live and not os.environ.get("DASHSCOPE_API_KEY" if provider == "qwen" else "DEEPSEEK_API_KEY"):
        parser.error("live calls require provider credentials")
    before = inventory()
    # Runtime flags inherited from unrelated shell work cannot affect pairing.
    environment = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
    environment.update(INTENTCOMPASS_AGENT_MODE="integrated", INTENTCOMPASS_RETRIEVAL="baseline",
                       INTENTCOMPASS_SEMANTIC="off", INTENTCOMPASS_LLM_ALLOW_NETWORK="0", PYTHONHASHSEED="0")
    command = [sys.executable, "-m", "tests.core.api_experiment", "--worker", "--split", args.split, "--per-scenario", str(args.per_scenario)]
    def run():
        completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=subprocess.PIPE, text=True, encoding="utf-8", check=True, timeout=5400)
        return json.loads(completed.stdout)
    print("Running paired offline baseline...", flush=True)
    baseline = run()
    ceiling = int((Decimal(str(budget_before["conservative_cost_rmb"])) + args.run_budget_rmb) * 1_000_000)
    environment.update(INTENTCOMPASS_SEMANTIC=provider, INTENTCOMPASS_LLM_ALLOW_NETWORK="1" if args.live else "0",
                       INTENTCOMPASS_API_POLICY=args.variant, INTENTCOMPASS_LLM_MODEL=args.model,
                       INTENTCOMPASS_LLM_OUTPUT_FORMAT="indices", INTENTCOMPASS_QWEN_REGION=os.environ.get("INTENTCOMPASS_QWEN_REGION", ""),
                       INTENTCOMPASS_BUDGET_LEDGER=str(args.ledger.resolve()), INTENTCOMPASS_RUN_CEILING_MICRO_RMB=str(ceiling))
    print(f"Running {args.variant} / {args.model}; run ceiling +{args.run_budget_rmb} RMB...", flush=True)
    candidate = run()
    budget_after = ledger.summary()
    quality = quality_verdict(baseline["metrics"], candidate["metrics"])
    reasons = candidate["semantic_reasons"]
    effective = (args.live and reasons.get("model_ranked", 0) > 0
                 and not candidate["agent_exceptions"]
                 and not any(reasons.get(k, 0) for k in ("circuit_open_after_failure", "shared_budget_unavailable", "missing_credential", "unverified_qwen_region")))
    latency_ok = all(candidate[key]["p95"] is not None and candidate[key]["p95"] <= 3000 for key in ("latency_ms", "attempted_latency_ms"))
    memory_ok = candidate["peak_memory_bytes"] <= baseline["peak_memory_bytes"] + 64*1024*1024
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"variant": args.variant, "model": args.model, "split": args.split, "per_scenario": args.per_scenario,
              "network_enabled": args.live, "python": platform.python_version(), "platform": platform.platform(),
              "configuration": {"candidates": DEMAND_VARIANTS[args.variant][0], "evidence_chars": DEMAND_VARIANTS[args.variant][1], "minimum_explicit_attributes": 2, "session_attempt_limit": 3, "output_format": "indices", "region": environment["INTENTCOMPASS_QWEN_REGION"]},
              "baseline": baseline, "candidate": candidate, "quality": quality,
              "gates": {"effective_live_run": effective, "latency": latency_ok, "memory": memory_ok,
                        "same_samples": baseline["selection_sha256"] == candidate["selection_sha256"]},
              "budget_before": budget_before, "budget_after": budget_after,
              "run_cost_bound_rmb": budget_after["conservative_cost_rmb"] - budget_before["conservative_cost_rmb"],
              "run_allowance_rmb": float(args.run_budget_rmb), "source_sha256": before,
              "sources_unchanged": before == inventory(), "protocol_sha256": sha256(ROOT / "docs/team/tasks/TASK-004-final-integration.md"),
              "limitations": ["Public is a development set; prior-used synthetic Shadow is not official private data", "Costs are conservative uncached estimates including unknown reservations", "Network measurements are environment-dependent; no claims of theoretical optimality", "Failures, cache hits and offline fallback turns remain in system metrics"]}
    report["eligible_for_expansion"] = quality["preliminary_quality_pass"] and all(report["gates"].values()) and report["sources_unchanged"]
    report["full_quality_candidate"] = report["eligible_for_expansion"] and args.per_scenario == 0 and quality["all_three_strictly_better"]
    write_json(output, report)
    summary = {key: report[key] for key in ("variant", "model", "split", "quality", "gates", "run_cost_bound_rmb", "sources_unchanged", "eligible_for_expansion", "full_quality_candidate")}
    summary["baseline_metrics"] = {k: v for k, v in baseline["metrics"].items() if k != "sessions"}
    summary["candidate_metrics"] = {k: v for k, v in candidate["metrics"].items() if k != "sessions"}
    summary["candidate_latency_ms"] = candidate["latency_ms"]
    summary["attempted_latency_ms"] = candidate["attempted_latency_ms"]
    summary["semantic_reasons"] = reasons
    print(json.dumps(summary, indent=2))
    print("output_sha256=" + sha256(output))
    if not report["sources_unchanged"] or not report["gates"]["same_samples"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
