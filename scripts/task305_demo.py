"""Record a target-blind multi-turn TASK-305 capability demonstration."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task305_evaluate import PRESET
from starter.agent import Agent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("output must be a new file under reports/generated")
    os.environ.update(PRESET)
    os.environ.update(INTENTCOMPASS_SEMANTIC="local", INTENTCOMPASS_LLM_ALLOW_NETWORK="0")
    agent = Agent(args.catalog)
    records: list[dict] = []
    try:
        if agent._core._adaptive.retriever.dense_status != "ready":
            raise RuntimeError("real dense index is required")
        session = "task305-demo-current-user"
        agent.reset(session, {"preference_tags": ["blue"]})
        messages = [
            "I'm just browsing and not sure what I want.",
            "shoes",
            "Actually, what I need is: blue.",
            "For that, what matters is: cotton; under $50.",
            "Those options are not quite right yet.",
            "Those options are not quite right yet.",
            "Actually, ignore my earlier preference. What I need is: leather.",
        ]
        for turn, message in enumerate(messages, 1):
            response = agent.respond(session, message, turn, 10)
            trace = agent._core._adaptive.sessions[session].last_trace
            records.append({"session": session, "turn": turn, "user": message, "response": response, "trace": trace})
        profile = agent.export_profile(session)
        next_session = "task305-demo-explicit-handoff"
        agent.reset(next_session, profile)
        response = agent.respond(next_session, "I'm looking for shoes.", 1, 10)
        records.append({
            "session": next_session,
            "turn": 1,
            "user": "I'm looking for shoes.",
            "explicit_imported_profile": profile,
            "response": response,
            "trace": agent._core._adaptive.sessions[next_session].last_trace,
        })
    finally:
        agent.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"task": "TASK-305", "target_blind": True, "records": records}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), "turns": len(records), "first_workflow": records[0]["trace"]["workflow"], "profile_handoff": records[-1]["trace"]["context"]["profile_priors"]}, indent=2))


if __name__ == "__main__":
    main()
