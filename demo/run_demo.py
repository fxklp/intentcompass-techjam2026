from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import (  # noqa: E402
    MAX_TURNS,
    TOP_K,
    catalog_index,
    coarse_category,
    customer_reply,
    initial_message,
    load_jsonl,
    materialize_hidden_fields,
    normalize_recommendations,
)
from starter.agent import Agent  # noqa: E402


DEFAULT_SAMPLE = "public_0183"
NOT_SCORED_UNTIL_OVERRIDE = "Not scored until intent override"


def _active_state(agent: Agent, session_id: str, turn: int) -> tuple[dict[str, list[str]], str]:
    # Demo-only observability. The official evaluator still sees only reset/respond.
    state = agent._core._sessions[session_id]  # noqa: SLF001
    preferences = {
        attribute: list(slot.values)
        for attribute, slot in state.preferences.items()
    }
    return preferences, state.retrieval_query(turn)


def official_target_rank(raw_target_rank: int | None, *, score_eligible: bool) -> int | None:
    """Apply the official Intent Override scoring gate to an observed Top 10 rank."""
    return raw_target_rank if score_eligible else None


def target_rank_display(raw_target_rank: int | None, *, score_eligible: bool) -> str:
    """Return a truthful target-rank label for the current evaluator state."""
    if not score_eligible:
        return NOT_SCORED_UNTIL_OVERRIDE
    return str(raw_target_rank) if raw_target_rank is not None else "not in Top 10"


def run_session(sample_id: str = DEFAULT_SAMPLE, *, verbose: bool = True) -> dict:
    catalog_path = ROOT / "data" / "catalog.jsonl"
    public_path = ROOT / "data" / "public_set.jsonl"
    samples = load_jsonl(public_path)
    try:
        sample = next(item for item in samples if item["sample_id"] == sample_id)
    except StopIteration as exc:
        raise ValueError(f"unknown public sample: {sample_id}") from exc
    if sample["scenario_type"] != "intent_override":
        raise ValueError("the first demo requires an Intent Override sample")

    catalog_ids, categories, products = catalog_index(catalog_path)
    target = str(sample["ground_truth"]["parent_asin"])
    intent_card, behavior = materialize_hidden_fields(sample, products)
    effective_sample = {**sample, "intent_card": intent_card, "behavior": behavior}

    agent = Agent(catalog_path)
    session_id = f"demo-{sample_id}"
    agent.reset(session_id, sample["user_profile"])

    disclosed: set[str] = set()
    boundary_used = False
    score_eligible = False
    override_seen = False
    override = effective_sample["behavior"].get("override") or {}
    override_turn = int(override.get("turn", 3))
    old_value = str(override.get("old_value", ""))
    new_value = str(override.get("new_value", ""))
    user_message = initial_message(
        effective_sample,
        coarse_category(categories.get(target, [])),
        disclosed,
    )
    turn_records: list[dict] = []
    override_preferences: dict[str, list[str]] | None = None
    override_query: str | None = None
    first_hit_turn: int | None = None
    best_rank: int | None = None
    preferences: dict[str, list[str]] = {}
    query = ""

    if verbose:
        print("=" * 72)
        print("IntentCompass deterministic demo")
        print(f"Session: {sample_id} | Scenario: intent_override")
        print("The harness knows the public target only for official scoring.")
        print("The Agent receives only user_profile and customer messages.")
        print("=" * 72)

    try:
        for turn in range(1, MAX_TURNS + 1):
            response = agent.respond(session_id, user_message, turn, TOP_K)
            ranked = normalize_recommendations(response["recommendations"], catalog_ids)
            preferences, query = _active_state(agent, session_id, turn)
            raw_target_rank = ranked.index(target) + 1 if target in ranked else None
            scored_target_rank = official_target_rank(
                raw_target_rank,
                score_eligible=score_eligible,
            )
            rank_display = target_rank_display(
                raw_target_rank,
                score_eligible=score_eligible,
            )

            if score_eligible and override_preferences is None:
                override_preferences = {
                    attribute: list(values)
                    for attribute, values in preferences.items()
                }
                override_query = query

            turn_records.append({
                "turn": turn,
                "customer_message": user_message,
                "active_preferences": {
                    attribute: list(values)
                    for attribute, values in preferences.items()
                },
                "query": query,
                "ask_attribute": response["ask_attribute"],
                "agent_message": response["message"],
                "top_10": list(ranked),
                "score_eligible": score_eligible,
                "raw_target_rank": raw_target_rank,
                "scored_target_rank": scored_target_rank,
                "target_rank_display": rank_display,
            })

            if verbose:
                print(f"\nTURN {turn}")
                print(f"Customer     : {user_message}")
                print(f"Active state : {preferences or '{}'}")
                print(f"Search query : {query or '<empty>'}")
                print(f"Ask attribute: {response['ask_attribute']}")
                print(f"Agent message: {response['message']}")
                print(f"Top 10       : {ranked}")
                print(f"Target rank  : {rank_display}")

            if scored_target_rank is not None:
                first_hit_turn = turn
                best_rank = scored_target_rank
                break

            if turn == MAX_TURNS:
                break

            if not score_eligible and turn + 1 == override_turn:
                score_eligible = True
                override_seen = True
                if new_value:
                    disclosed.add(new_value)
                user_message = str(override.get("message"))
            else:
                user_message, boundary_used = customer_reply(
                    effective_sample,
                    response.get("ask_attribute"),
                    disclosed,
                    boundary_used,
                )
    finally:
        agent.close()

    result = {
        "sample_id": sample_id,
        "hit": first_hit_turn is not None,
        "first_hit_turn": first_hit_turn,
        "best_rank": best_rank,
        "override_seen": override_seen,
        "override_turn": override_turn,
        "override_preferences": override_preferences or {},
        "override_query": override_query or "",
        "active_preferences": preferences,
        "query": query,
        "old_value": old_value,
        "new_value": new_value,
        "turns": turn_records,
    }
    if verbose:
        if result["hit"]:
            print("\nDEMO RESULT: OFFICIAL HIT after intent override")
            print(f"First hit turn: {first_hit_turn} | Rank: {best_rank}")
        else:
            print("\nDEMO RESULT: OFFICIAL MISS")
        print("=" * 72)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the first deterministic IntentCompass demo")
    parser.add_argument("--sample-id", default=DEFAULT_SAMPLE)
    args = parser.parse_args()
    result = run_session(args.sample_id)
    if not result["hit"] or not result["override_seen"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
