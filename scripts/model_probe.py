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
from tests.core.check_adaptive import sha256, write_json


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
            raise RuntimeError("live model screen failed; inspect sanitized summary and budget")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=tuple(RATES), default="qwen3.8-flash")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--initialize-budget", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--per-scenario", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.initialize_budget:
        BudgetLedger.initialize(args.ledger.resolve())
    ledger = BudgetLedger(args.ledger.resolve())
    provider = RATES[args.model][0]
    key_name = "DASHSCOPE_API_KEY" if provider == "qwen" else "DEEPSEEK_API_KEY"
    readiness = {"model": args.model, "provider": provider, "credential_present": bool(os.environ.get(key_name)), "qwen_region": os.environ.get("INTENTCOMPASS_QWEN_REGION", "unconfirmed"), "budget": ledger.summary()}
    if not args.live:
        print(json.dumps(readiness, indent=2))
        return
    if not readiness["credential_present"] or (provider == "qwen" and readiness["qwen_region"] != "beijing"):
        parser.error("credentials and verified region required; no request sent")
    if not 1 <= args.per_scenario <= 80 or args.output is None:
        parser.error("live screen requires --output and per-scenario 1..80")
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports/generated").resolve()) or output.exists():
        parser.error("new output must be under reports/generated")
    output.parent.mkdir(parents=True, exist_ok=True)
    os.environ.update(INTENTCOMPASS_AGENT_MODE="integrated", INTENTCOMPASS_RETRIEVAL="baseline", INTENTCOMPASS_SEMANTIC=provider, INTENTCOMPASS_LLM_MODEL=args.model, INTENTCOMPASS_LLM_ALLOW_NETWORK="1", INTENTCOMPASS_BUDGET_LEDGER=str(args.ledger.resolve()))
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
    agent = ProbeAgent(ROOT / "data/catalog.jsonl")
    metrics, status = None, "completed"
    try:
        metrics = evaluate(agent, selected, ids, categories, products)
        metrics.pop("sessions", None)
        if agent.semantic_reasons["model_ranked"] == 0:
            status = "no_successful_model_calls"
    except RuntimeError:
        status = "provider_failed_screen_aborted"
    finally:
        agent.agent.close()
    result = {"model": args.model, "provider": provider, "status": status, "sample_selection": "first N public sessions per scenario; fixed before calls", "sample_counts": dict(counts), "metrics": metrics, "semantic_reasons": dict(agent.semantic_reasons), "latency_p95_ms": percentile(agent.latencies, .95) if agent.latencies else None, "budget": ledger.summary(), "source_sha256": before, "sources_unchanged": before == inventory(), "limitations": ["Only current public candidate text and safe context sent; no private or Shadow data", "Cost is conservative uncached peak estimate, not a provider invoice", "A small screen cannot establish final quality or private performance"]}
    write_json(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "source_sha256"}, indent=2))
    print("output_sha256=" + sha256(output))
    if status != "completed" or not result["sources_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
