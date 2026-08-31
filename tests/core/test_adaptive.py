from __future__ import annotations

import json
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solution.clarification import choose_adaptive_question
from solution.config import CoreConfig
from solution.context import ContextMemory, profile_priors
from solution.contracts import Candidate, PreferenceSlot
from solution.ranker import rank_candidates
from solution.state import SessionState
from solution.workflow import WorkflowState
from starter.agent import Agent


def candidates(attribute: str = "color") -> list[Candidate]:
    values = ("red", "blue") if attribute == "color" else ("cotton", "wool")
    return [Candidate(f"P{i:03}", i, 1.0, f"shoes {values[i % 2]}", 40.0) for i in range(40)]


class ContextTest(unittest.TestCase):
    def test_profile_whitelist_and_bounded_input(self) -> None:
        profile = {"preference_tags": ["cotton", None, {"arbitrary": "value"}, "blue"], "identity": "do-not-export"}
        self.assertEqual({slot.attribute for slot in profile_priors(profile)}, {"material", "color"})
        self.assertEqual(profile_priors({"preference_tags": "cotton"}), ())
        self.assertLessEqual(len(profile_priors({"preference_tags": ["cotton"] * 100})[0].values), 16)

    def test_explicit_then_clear_does_not_resurrect_prior(self) -> None:
        state = SessionState.create("a", {"preference_tags": ["red", "cotton"]})
        memory = ContextMemory.create(state.user_profile)
        state.apply_user_message("I'm looking for shoes. A key requirement is: blue.", 1, flexible=True)
        memory.observe(state, "blue")
        self.assertEqual([slot.attribute for slot in memory.active_priors()], ["material"])
        state.apply_user_message("I don't have a preference for color.", 2, flexible=True)
        memory.observe(state, "no preference")
        self.assertNotIn("red", json.dumps(memory.distill(state)))
        self.assertIn("color", memory.distill(state)["unconstrained"])

    def test_override_distillation_has_no_old_text(self) -> None:
        state = SessionState.create("a", {"preference_tags": ["red", "cotton"]})
        memory = ContextMemory.create(state.user_profile)
        state.apply_user_message("I'm looking for shoes. I prefer red.", 1, flexible=True)
        memory.observe(state, "red")
        text = "Actually, ignore my earlier preference. What I need is: leather."
        state.apply_user_message(text, 2, flexible=True)
        memory.observe(state, text)
        distilled = json.dumps(memory.distill(state))
        self.assertNotIn("red", distilled)
        self.assertNotIn("cotton", distilled)
        self.assertIn("leather", distilled)
        self.assertEqual(memory.revision, 2)

    def test_plain_reply_and_feedback_do_not_conflict(self) -> None:
        state = SessionState.create("a", {})
        state.mark_asked("color")
        state.apply_user_message("blue", 1, flexible=True)
        self.assertEqual(state.preferences["color"].values, ("blue",))
        state.apply_user_message("Those options are not quite right yet.", 2, flexible=True)
        self.assertEqual(state.preferences["color"].values, ("blue",))

    def test_category_correction_and_category_reply(self) -> None:
        state = SessionState.create("a", {})
        state.apply_user_message("I'm looking for shoes. I prefer red.", 1, flexible=True)
        state.apply_user_message("Actually, I'm looking for bags.", 2, flexible=True)
        self.assertEqual(state.category, "bags")
        self.assertEqual(state.preferences, {})
        state.mark_asked("category")
        state.apply_user_message("shirts", 3, flexible=True)
        self.assertEqual(state.category, "shirts")


class ClarificationTest(unittest.TestCase):
    def test_candidate_distribution_changes_question(self) -> None:
        state = SessionState.create("a", {})
        color = choose_adaptive_question(state, candidates("color"), output_limit=10, fallback_used=False)
        material = choose_adaptive_question(state, candidates("material"), output_limit=10, fallback_used=False)
        self.assertEqual(color.attribute, "color")
        self.assertEqual(material.attribute, "material")
        self.assertEqual(color.reason, "candidate_information_gain")
        self.assertEqual(color.information_gain, 1.0)
        self.assertTrue(color.overloaded)

    def test_missing_or_constant_evidence_uses_fallback(self) -> None:
        state = SessionState.create("a", {})
        pool = [Candidate(str(i), i, 0, "red shoes", None) for i in range(40)]
        question = choose_adaptive_question(state, pool, output_limit=10, fallback_used=False)
        self.assertEqual(question.attribute, "feature")
        self.assertEqual(question.reason, "sparse_evidence_fallback")

    def test_no_preference_and_asked_attributes_are_excluded(self) -> None:
        state = SessionState.create("a", {})
        state.unconstrained_attributes.add("color")
        question = choose_adaptive_question(state, candidates(), output_limit=10, fallback_used=False)
        self.assertNotEqual(question.attribute, "color")
        state.mark_asked(question.attribute)
        next_question = choose_adaptive_question(state, candidates(), output_limit=10, fallback_used=False)
        self.assertNotEqual(question.attribute, next_question.attribute)

    def test_no_match_does_not_treat_popularity_as_relevance(self) -> None:
        state = SessionState.create("a", {})
        question = choose_adaptive_question(state, candidates(), output_limit=10, fallback_used=True)
        self.assertEqual(question.attribute, "category")
        self.assertFalse(question.overloaded)

    def test_turn_ten_and_all_attributes_exhausted(self) -> None:
        state = SessionState.create("a", {})
        state.latest_turn = 10
        self.assertIsNone(choose_adaptive_question(state, candidates(), output_limit=10, fallback_used=False).attribute)
        state.latest_turn = 2
        state.asked_attributes = ["feature", "material", "color", "size", "style", "use_case", "budget", "brand", "other", "category"]
        self.assertIsNone(choose_adaptive_question(state, candidates(), output_limit=10, fallback_used=False).attribute)

    def test_nonfinite_prices_are_not_evidence(self) -> None:
        pool = [Candidate(str(i), i, 0, "", float("nan") if i % 2 else float("inf")) for i in range(40)]
        question = choose_adaptive_question(SessionState.create("a", {}), pool, output_limit=10, fallback_used=False)
        self.assertEqual(question.reason, "sparse_evidence_fallback")


class WorkflowTest(unittest.TestCase):
    def test_route_controls_bounded_pool(self) -> None:
        state = SessionState.create("a", {})
        flow = WorkflowState()
        browsing = flow.plan(state, "", changed=False)
        self.assertEqual((browsing.route, browsing.pool_limit), ("browsing", 80))
        state.preferences["color"] = PreferenceSlot("color", ("blue",), 1)
        buying = flow.plan(state, "", changed=True)
        self.assertEqual((buying.route, buying.pool_limit), ("buying", 50))

    def test_cutoff_recovery_and_new_information_reset(self) -> None:
        state = SessionState.create("a", {})
        flow = WorkflowState(overloaded=True)
        self.assertEqual(flow.plan(state, "", changed=False).pool_limit, 40)
        flow.plan(state, "not quite right", changed=False)
        self.assertTrue(flow.plan(state, "not quite right", changed=False).recovery)
        self.assertFalse(flow.plan(state, "blue", changed=True).recovery)
        self.assertEqual(flow.rejected_turns, 0)

    def test_profile_soft_tiebreak_and_explicit_priority(self) -> None:
        state = SessionState.create("a", {})
        pool = [Candidate("RED", 0, 0, "red leather", 50), Candidate("BLUE", 1, 0, "blue cotton", 50)]
        priors = (PreferenceSlot("material", ("cotton",), 0),)
        self.assertEqual(rank_candidates(pool, state, 2, profile_priors=priors)[0].parent_asin, "BLUE")
        state.preferences["color"] = PreferenceSlot("color", ("red",), 1)
        self.assertEqual(rank_candidates(pool, state, 2, profile_priors=priors)[0].parent_asin, "RED")


class AdaptiveIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "catalog.jsonl"
        self.path.write_text("".join(json.dumps({"parent_asin": item.parent_asin, "title": item.searchable_text, "categories": ["shoes"], "price": item.price}) + "\n" for item in candidates()), encoding="utf-8", newline="\n")
        self.environment = patch.dict(os.environ, {"INTENTCOMPASS_AGENT_MODE": "adaptive", "INTENTCOMPASS_RETRIEVAL": "baseline", "INTENTCOMPASS_SEMANTIC": "off", "INTENTCOMPASS_LLM_ALLOW_NETWORK": "0"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.agent = Agent(self.path)
        self.addCleanup(self.agent.close)

    def trace(self, session: str = "a") -> dict:
        return self.agent._core._adaptive.sessions[session].last_trace

    def test_official_adapter_runs_offline_dynamic_route(self) -> None:
        self.agent.reset("a", {})
        with patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")):
            first = self.agent.respond("a", "I'm looking for shoes, but I'm still exploring.", 1, 10)
            self.assertEqual(first["ask_attribute"], "color")
            self.assertEqual(self.trace()["intent_route"], "browsing")
            second = self.agent.respond("a", "blue", 2, 10)
        self.assertEqual(self.trace()["intent_route"], "buying")
        self.assertEqual(self.trace()["pool_limit"], 50)
        self.assertTrue(second["recommendations"])
        self.assertTrue(all(int(item["parent_asin"][1:]) % 2 == 1 for item in second["recommendations"]))
        self.assertEqual(second["usage"], {"prompt_tokens": 0, "completion_tokens": 0})

    def test_fallback_topk_reset_and_isolation(self) -> None:
        with self.assertRaises(RuntimeError):
            self.agent.respond("missing", "shoes", 1, 10)
        for session in ("a", "b"):
            self.agent.reset(session, {"preference_tags": ["blue"]})
        first = self.agent.respond("a", "zzzznotaword", 1, 10)
        other = self.agent.respond("b", "zzzznotaword", 1, 10)
        self.assertEqual(first, other)
        self.assertTrue(self.trace()["retrieval"]["fallback_used"])
        self.assertEqual(first["ask_attribute"], "category")
        self.assertEqual([item["parent_asin"] for item in first["recommendations"]], self.agent._core._retriever.index.fallback_ids[:10])
        self.agent.reset("a", {})
        self.assertEqual(self.agent._core._adaptive.sessions["a"].last_trace, {})
        self.assertEqual(self.agent.respond("a", "shoes", 1, 0)["recommendations"], [])
        self.agent.close()
        self.agent.close()

    def test_recovery_changes_query_without_discarding_preferences(self) -> None:
        self.agent.reset("a", {})
        self.agent.respond("a", "I'm looking for shoes. A key requirement is: blue.", 1, 10)
        self.agent.respond("a", "Those options are not quite right yet.", 2, 10)
        self.agent.respond("a", "Those options are not quite right yet.", 3, 10)
        trace = self.trace()
        self.assertEqual(trace["workflow"], "recover_after_miss_or_rejection")
        self.assertEqual(trace["query"], "shoes")
        self.assertIn("blue", json.dumps(trace["context"]["explicit"]))

    def test_dual_route_explicit_opt_in_uses_existing_protocol(self) -> None:
        with patch.dict(os.environ, {"INTENTCOMPASS_RETRIEVAL": "dual_route"}):
            agent = Agent(self.path)
        self.addCleanup(agent.close)
        agent.reset("a", {})
        agent.respond("a", "I'm looking for shoes. A key requirement is: blue.", 1, 10)
        trace = agent._core._adaptive.sessions["a"].last_trace
        self.assertEqual(trace["backend"], "dual_route")
        self.assertEqual(trace["retrieval"]["selected_path"], "buying")

    def test_invalid_config_is_not_silently_ignored(self) -> None:
        with patch.dict(os.environ, {"INTENTCOMPASS_AGENT_MODE": "typo"}):
            with self.assertRaises(ValueError):
                CoreConfig.from_environment()
        with patch.dict(os.environ, {"INTENTCOMPASS_AGENT_MODE": "baseline", "INTENTCOMPASS_RETRIEVAL": "dual_route"}):
            with self.assertRaises(ValueError):
                CoreConfig.from_environment()

    def test_semantic_usage_reaches_official_payload_and_unknown_is_omitted(self) -> None:
        from solution.semantic import SemanticResult

        self.agent.reset("a", {})
        def with_usage(pool, context):
            return SemanticResult(pool, "mock", {"prompt_tokens": 12, "completion_tokens": 3}, True)
        with patch.object(self.agent._core._adaptive.semantic, "rerank", side_effect=with_usage):
            payload = self.agent.respond("a", "I'm looking for shoes.", 1, 10)
        self.assertEqual(payload["usage"], {"prompt_tokens": 12, "completion_tokens": 3})
        def unknown_usage(pool, context):
            return SemanticResult(pool, "mock_failure", None, True)
        with patch.object(self.agent._core._adaptive.semantic, "rerank", side_effect=unknown_usage):
            payload = self.agent.respond("a", "blue", 2, 10)
        self.assertNotIn("usage", payload)
        self.assertFalse(self.trace()["semantic"]["usage_known"])
        self.assertTrue(payload["recommendations"])


if __name__ == "__main__":
    unittest.main()
