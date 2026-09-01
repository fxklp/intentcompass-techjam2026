"""One sanitized, budgeted end-to-end LLM ranking proof for TASK-306."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("use a new output under reports/generated")
    from scripts.api_credentials import load_credentials
    readiness = load_credentials(args.credentials_file.resolve())
    if not readiness["qwen_present"]:
        parser.error("labeled Qwen credential required; value suppressed")
    from solution.api_budget import BudgetLedger
    ledger = BudgetLedger(args.ledger.resolve())
    before = ledger.summary()
    ceiling = int(round((before["conservative_cost_rmb"] + 1.0) * 1_000_000))
    os.environ.update({
        "INTENTCOMPASS_AGENT_MODE": "integrated",
        "INTENTCOMPASS_RETRIEVAL": "capability",
        "INTENTCOMPASS_SEMANTIC": "qwen",
        "INTENTCOMPASS_LLM_MODEL": "qwen3.8-max",
        "INTENTCOMPASS_LLM_ALLOW_NETWORK": "1",
        "INTENTCOMPASS_LLM_OUTPUT_FORMAT": "indices",
        "INTENTCOMPASS_BUDGET_LEDGER": str(args.ledger.resolve()),
        "INTENTCOMPASS_RUN_CEILING_MICRO_RMB": str(ceiling),
        "INTENTCOMPASS_SEMANTIC_ASSETS": str((ROOT / "artifacts/semantic").resolve()),
        "INTENTCOMPASS_FORCE_SEMANTIC": "1",
        "INTENTCOMPASS_API_POLICY": "legacy",
    })
    from starter.agent import Agent
    agent = Agent(ROOT / "data/catalog.jsonl")
    try:
        agent.reset("task306-live-proof", {})
        reply = agent.respond(
            "task306-live-proof",
            "I'm looking for Shoes, but I'm still exploring.",
            1,
            10,
        )
        trace = agent._core._adaptive.sessions["task306-live-proof"].last_trace
        report = {
            "scope": "one target-blind public-catalog capability proof; not a quality score",
            "provider": "qwen",
            "model": "qwen3.8-max",
            "retrieval_routes": trace["retrieval"]["routes"],
            "dense_ready": agent._core._adaptive.retriever.dense_status,
            "semantic": trace["semantic"],
            "usage": reply.get("usage"),
            "valid_recommendation_count": len(reply["recommendations"]),
            "budget_before": before,
            "budget_after": ledger.summary(),
        }
    finally:
        agent.close()
    if report["dense_ready"] != "ready" or "dense" not in report["retrieval_routes"]:
        raise RuntimeError("real dense route did not execute")
    if report["semantic"]["reason"] != "model_ranked" or not report["semantic"]["attempted"]:
        raise RuntimeError("real LLM ranking did not complete")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
