"""Aggregate Public-only diagnosis; target labels never enter production code."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from tests.core.check_adaptive import ROOT, sha256, write_json
from tests.core.check_final import inventory


class Observed:
    def __init__(self, catalog):
        from starter.agent import Agent
        self.agent = Agent(catalog)
        self.turns = []
        retriever = self.agent._core._adaptive.retriever
        original = retriever.search
        def search(request):
            result = original(request)
            self.pool = [c.parent_asin for c in result.candidates]
            return result
        retriever.search = search

    def reset(self, session_id, profile):
        self.turns = []
        self.agent.reset(session_id, profile)

    def respond(self, session_id, message, turn, top_k):
        result = self.agent.respond(session_id, message, turn, top_k)
        trace = self.agent._core._adaptive.sessions[session_id].last_trace
        self.turns.append({"turn": turn, "pool": self.pool[:],
                           "ids": [r["parent_asin"] for r in result["recommendations"]],
                           "context": trace["context"], "query": trace["query"],
                           "fallback": trace["retrieval"]["fallback_used"]})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("use a new file under reports/generated")
    for key in list(os.environ):
        if key.startswith("INTENTCOMPASS_"):
            del os.environ[key]
    os.environ.update(INTENTCOMPASS_AGENT_MODE="integrated", INTENTCOMPASS_RETRIEVAL="baseline", INTENTCOMPASS_SEMANTIC="off", INTENTCOMPASS_LLM_ALLOW_NETWORK="0")
    from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl, metric_summary
    from solution.contracts import flatten_text
    before = inventory()
    ids, categories, products = catalog_index(ROOT / "data/catalog.jsonl")
    agent = Observed(ROOT / "data/catalog.jsonl")
    counts, by_scenario, field_coverage, preference_counts = Counter(), defaultdict(Counter), Counter(), Counter()
    sessions = []
    try:
        for sample in load_jsonl(ROOT / "data/public_set.jsonl"):
            result = evaluate(agent, [sample], ids, categories, products)
            session = result["sessions"][0]
            sessions.append(session)
            # Labels enter here only AFTER the unchanged evaluator and Agent ran.
            target = sample["ground_truth"]["parent_asin"]
            turns = agent.turns
            available = [t for t in turns if target in t["pool"]]
            if session["hit"]:
                reason = "hit_rank_1" if session["best_rank"] == 1 else "hit_rank_2_3" if session["best_rank"] <= 3 else "hit_rank_4_10"
            else:
                reason = "miss_never_in_pool" if not available else "miss_present_but_below_top10"
            counts[reason] += 1
            by_scenario[sample["scenario_type"]][reason] += 1
            if len(turns) >= 2 and not session["hit"] and turns[-1]["ids"] == turns[-2]["ids"]:
                counts["miss_repeated_final_top10"] += 1
            last = turns[-1]
            preference_counts[f"{reason}: {len(last['context']['explicit'])} attributes"] += 1
            values = [v.casefold() for k, vs in last["context"]["explicit"].items() if k != "budget" for v in vs if v]
            fields = {k: flatten_text(products[target].get(k)).casefold() for k in ("title", "features", "details", "categories", "description")}
            for value in values:
                field_coverage["visible_preferences"] += 1
                for field, text in fields.items():
                    if value in text:
                        field_coverage[f"exact_in_{field}"] += 1
            if session["first_hit_turn"] and session["first_hit_turn"] >= 6:
                counts["hit_turn_6_or_later"] += 1
    finally:
        agent.agent.close()
    grouped = defaultdict(list)
    for session in sessions:
        grouped[session["scenario_type"]].append(session)
    report = {"metrics": metric_summary(sessions), "scenario_metrics": {k: metric_summary(v) for k,v in grouped.items()},
              "diagnosis": dict(counts), "scenario_diagnosis": {k: dict(v) for k,v in by_scenario.items()},
              "final_visible_preference_counts": dict(preference_counts), "target_field_coverage_aggregate_only": dict(field_coverage),
              "source_sha256": before, "sources_unchanged": before == inventory(),
              "limitations": ["Public diagnostic only; no identifiers or target text exported", "Pool coverage across turns is diagnostic, not causal attribution or achievable score", "Field coverage is overlapping, not exclusive"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(json.dumps({k:v for k,v in report.items() if k != "source_sha256"}, indent=2))
    print("sha256="+sha256(output))
    if not report["sources_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
