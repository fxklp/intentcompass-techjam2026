"""Explicit, budgeted live API screen on a fixed public subset (never Shadow)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from solution.api_budget import BudgetLedger
from solution.chat_reranker import RATES
from tests.core.check_adaptive import non_regression, sha256, write_json


class LiveScreenAborted(BaseException):
    """Escape the official evaluator's per-turn Exception handler unchanged."""


class ProbeAgent:
    def __init__(self, catalog: Path):
        from starter.agent import Agent
        self.agent = Agent(catalog)
        self.semantic_reasons = Counter()
        self.latencies = []

    def reset(self, session_id, user_profile):
        self.agent.reset(session_id, user_profile)

    def respond(self, session_id, user_message, turn, top_k):
        started = time.perf_counter()
        result = self.agent.respond(session_id, user_message, turn, top_k)
        self.latencies.append(1000 * (time.perf_counter()-started))
        trace = self.agent._core._adaptive.sessions[session_id].last_trace["semantic"]
        self.semantic_reasons[trace["reason"]] += 1
        # Abort a live screen after provider failure; do not call a fallback-only
        # evaluation a model experiment, and do not retry in another Agent.
        if trace["attempted"] and trace["reason"] != "model_ranked":
            raise LiveScreenAborted("live model screen failed; inspect sanitized summary and budget")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=tuple(RATES), default="qwen3.8-flash")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--initialize-budget", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--per-scenario", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--credentials-file", type=Path)
    parser.add_argument("--output-format", choices=("ids", "indices"), default="ids")
    args = parser.parse_args()
    if args.credentials_file:
        from scripts.api_credentials import load_credentials
        try:
            load_credentials(args.credentials_file)
        except (ValueError, OSError):
            parser.error("credential file invalid; contents suppressed; no request sent")
    if args.initialize_budget:
        BudgetLedger.initialize(args.ledger.resolve())
    ledger = BudgetLedger(args.ledger.resolve())
    provider = RATES[args.model][0]
    key_name = "DASHSCOPE_API_KEY" if provider == "qwen" else "DEEPSEEK_API_KEY"
    readiness = {"model": args.model, "provider": provider, "credential_present": bool(os.environ.get(key_name)), "qwen_region": os.environ.get("INTENTCOMPASS_QWEN_REGION", "unconfirmed"), "budget": ledger.summary()}
    if not args.live:
        print(json.dumps(readiness, indent=2))
        return
    if not readiness["credential_present"] or (provider == "qwen" and readiness["qwen_region"] not in {"beijing", "singapore"}):
        parser.error("credentials and verified region required; no request sent")
    if not 1 <= args.per_scenario <= 80 or args.output is None:
        parser.error("live screen requires --output and per-scenario 1..80")
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports/generated").resolve()) or output.exists():
        parser.error("new output must be under reports/generated")
    output.parent.mkdir(parents=True, exist_ok=True)
    os.environ.update(INTENTCOMPASS_AGENT_MODE="integrated", INTENTCOMPASS_RETRIEVAL="baseline", INTENTCOMPASS_SEMANTIC=provider, INTENTCOMPASS_LLM_MODEL=args.model, INTENTCOMPASS_LLM_ALLOW_NETWORK="1", INTENTCOMPASS_BUDGET_LEDGER=str(args.ledger.resolve()))
    os.environ["INTENTCOMPASS_LLM_OUTPUT_FORMAT"] = args.output_format
    from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl
    from scripts.benchmark_runtime import percentile
    from tests.core.check_final import inventory
    before = inventory()
    selected, counts = [], Counter()
    for sample in load_jsonl(ROOT / "data/public_set.jsonl"):
        scenario = sample["scenario_type"]
        if counts[scenario] < args.per_scenario:
            selected.append(sample)
            counts[scenario] += 1
    ids, categories, products = catalog_index(ROOT / "data/catalog.jsonl")
    os.environ.update(INTENTCOMPASS_SEMANTIC="off", INTENTCOMPASS_LLM_ALLOW_NETWORK="0")
    reference = ProbeAgent(ROOT / "data/catalog.jsonl")
    try:
        baseline = evaluate(reference, selected, ids, categories, products)
        baseline.pop("sessions", None)
    finally:
        reference.agent.close()
    baseline_p95 = percentile(reference.latencies, .95)
    os.environ.update(INTENTCOMPASS_SEMANTIC=provider, INTENTCOMPASS_LLM_ALLOW_NETWORK="1")
    budget_before = ledger.summary()
    agent = ProbeAgent(ROOT / "data/catalog.jsonl")
    metrics, status = None, "completed"
    try:
        metrics = evaluate(agent, selected, ids, categories, products)
        metrics.pop("sessions", None)
        if agent.semantic_reasons["model_ranked"] == 0:
            status = "no_successful_model_calls"
    except LiveScreenAborted:
        status = "provider_failed_screen_aborted"
    finally:
        agent.agent.close()
    result = {"model": args.model, "provider": provider, "qwen_region": readiness["qwen_region"] if provider == "qwen" else None, "status": status, "sample_selection": "first N public sessions per scenario; fixed before calls", "sample_counts": dict(counts), "metrics": metrics, "baseline_metrics": baseline, "quality_regressions": non_regression(baseline, metrics) if metrics else None, "baseline_latency_p95_ms": baseline_p95, "semantic_reasons": dict(agent.semantic_reasons), "provider_failure": agent.agent._core._adaptive.semantic.last_failure, "latency_p95_ms": percentile(agent.latencies, .95) if agent.latencies else None, "budget_before": budget_before, "budget": ledger.summary(), "source_sha256": before, "sources_unchanged": before == inventory(), "limitations": ["Only current public candidate text and safe context sent; no private or Shadow data", "Cost is conservative uncached peak estimate, not a provider invoice", "A small screen cannot establish final quality or private performance"]}
    result["output_format"] = args.output_format
    write_json(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "source_sha256"}, indent=2))
    print("output_sha256=" + sha256(output))
    if status != "completed" or not result["sources_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
