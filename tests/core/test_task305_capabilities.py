from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solution.buying_constraints import (
    candidate_evidence,
    filter_buying_candidates,
    value_evidence,
)
from solution.contracts import Candidate, PreferenceSlot
from solution.state import SessionState
from starter.agent import Agent
from solution.local_llm_reranker import LocalLLMReranker


class BuyingConstraintEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.match = Candidate("MATCH", 0, 1.0, "blue cotton running shoes", 40.0)
        self.conflict = Candidate("CONFLICT", 1, 0.9, "red leather running shoes", 120.0)
        self.unknown = Candidate("UNKNOWN", 2, 0.8, "running shoes", None)

    def test_budget_and_attribute_are_three_valued(self) -> None:
        self.assertEqual(value_evidence(self.match, "budget", "under $50"), "satisfied")
        self.assertEqual(value_evidence(self.conflict, "budget", "under $50"), "conflict")
        self.assertEqual(value_evidence(self.unknown, "budget", "under $50"), "unknown")
        self.assertEqual(value_evidence(self.match, "color", "blue"), "satisfied")
        self.assertEqual(value_evidence(self.match, "material", "100% cotton"), "satisfied")
        self.assertEqual(value_evidence(self.conflict, "color", "blue"), "conflict")
        self.assertEqual(value_evidence(self.unknown, "color", "blue"), "unknown")

    def test_negative_unknown_and_known_conflict(self) -> None:
        self.assertEqual(value_evidence(self.conflict, "material", "no leather"), "conflict")
        self.assertEqual(value_evidence(self.match, "material", "no leather"), "satisfied")
        self.assertEqual(value_evidence(self.unknown, "material", "no leather"), "unknown")

    def test_filter_excludes_conflict_and_discloses_unknown_relaxation(self) -> None:
        state = SessionState.create("s", {})
        state.preferences = {
            "color": PreferenceSlot("color", ("blue",), 1),
            "budget": PreferenceSlot("budget", ("under $50",), 1),
        }
        kept, report = filter_buying_candidates([self.conflict, self.unknown, self.match], state)
        self.assertEqual([item.parent_asin for item in kept], ["MATCH", "UNKNOWN"])
        self.assertEqual(report.to_dict(), {
            "satisfied": 1, "conflict": 1, "unknown": 1, "retained_unknown": True,
        })
        self.assertEqual(candidate_evidence(self.unknown, state), "unknown")

    def test_all_known_conflicts_return_honest_empty_result(self) -> None:
        state = SessionState.create("s", {})
        state.preferences["budget"] = PreferenceSlot("budget", ("under $10",), 1)
        kept, report = filter_buying_candidates([self.match, self.conflict], state)
        self.assertEqual(kept, [])
        self.assertEqual(report.conflict, 2)


class Task305EndToEndTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.catalog = Path(temporary.name) / "catalog.jsonl"
        rows = [
            {"parent_asin": "RED", "title": "red leather shoes", "categories": ["shoes"], "price": 90, "rating_number": 3},
            {"parent_asin": "BLUE", "title": "blue cotton shoes", "categories": ["shoes"], "price": 40, "rating_number": 2},
            {"parent_asin": "PLAIN", "title": "everyday shoes", "categories": ["shoes"], "price": None, "rating_number": 1},
        ]
        self.catalog.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8", newline="\n")
        environment = {
            "INTENTCOMPASS_AGENT_MODE": "adaptive",
            "INTENTCOMPASS_RETRIEVAL": "baseline",
            "INTENTCOMPASS_SEMANTIC": "off",
            "INTENTCOMPASS_LLM_ALLOW_NETWORK": "0",
            "INTENTCOMPASS_OFFLINE_RANKING": "constraints",
            "INTENTCOMPASS_TERMINAL_RECOVERY": "off",
            "INTENTCOMPASS_FINAL_POLICY": "off",
            "INTENTCOMPASS_PRECISION_ORDER": "off",
            "INTENTCOMPASS_CATEGORY_ORDER": "off",
        }
        self.environment = patch.dict(os.environ, environment)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.agent = Agent(self.catalog)
        self.addCleanup(self.agent.close)

    def trace(self, session: str) -> dict:
        return self.agent._core._adaptive.sessions[session].last_trace

    def test_overgeneral_request_skips_then_substantive_reply_resumes(self) -> None:
        self.agent.reset("broad", {})
        first = self.agent.respond("broad", "I'm just browsing and not sure what I want.", 1, 10)
        trace = self.trace("broad")
        self.assertEqual(first["ask_attribute"], "category")
        self.assertEqual(trace["workflow"], "pre_retrieval_cutoff")
        self.assertEqual(trace["calls"], {"retrieval": 0, "semantic": 0})
        self.assertEqual(trace["retrieval"]["routes"], ["cached_popularity_prior"])

        second = self.agent.respond("broad", "shoes", 2, 10)
        trace = self.trace("broad")
        self.assertTrue(second["recommendations"])
        self.assertEqual(trace["calls"]["retrieval"], 1)
        self.assertNotEqual(trace["workflow"], "pre_retrieval_cutoff")

    def test_explicit_profile_export_import_changes_new_session_order(self) -> None:
        self.agent.reset("first", {"preference_tags": ["blue"]})
        first = self.agent.respond("first", "I'm looking for shoes.", 1, 10)
        self.assertEqual(first["recommendations"][0]["parent_asin"], "BLUE")
        exported = self.agent.export_profile("first")
        self.assertEqual(exported, {"preference_tags": ["blue"]})

        self.agent.reset("second", exported)
        second = self.agent.respond("second", "I'm looking for shoes.", 1, 10)
        self.assertEqual(second["recommendations"][0]["parent_asin"], "BLUE")
        self.agent.respond("second", "Actually, ignore my earlier preference. What I need is: red.", 2, 10)
        self.assertEqual(self.agent.export_profile("second"), {"preference_tags": ["red"]})

        self.agent.reset("other-user", {})
        self.assertEqual(self.agent.export_profile("other-user"), {"preference_tags": []})
        with self.assertRaises(KeyError):
            self.agent.export_profile("missing")


class LocalLLMTest(unittest.TestCase):
    def test_parser_rejects_shortlist_and_accepts_exact_permutation(self) -> None:
        self.assertEqual(LocalLLMReranker._parse('{"ordered_indices":[2,0,1]}', 3), [2, 0, 1])
        with self.assertRaises(ValueError):
            LocalLLMReranker._parse('{"ordered_indices":[0,1]}', 3)

    @unittest.skipUnless(
        os.environ.get("INTENTCOMPASS_RUN_LOCAL_LLM_PROOF") == "1"
        and (Path(__file__).resolve().parents[2] / "artifacts/local_llm/manifest.json").exists(),
        "explicit pinned local LLM proof not requested",
    )
    def test_real_local_llm_output_enters_ranking_decision(self) -> None:
        reranker = LocalLLMReranker(Path(__file__).resolve().parents[2] / "artifacts/semantic")
        pool = [
            Candidate("LEATHER", 0, 1, "red leather formal shoes", 120),
            Candidate("BLUE", 1, 1, "blue cotton running shoes", 45),
            Candidate("PLAIN", 2, 1, "everyday walking shoes", 35),
        ]
        context = {"category": "shoes", "explicit": {"color": ["blue"], "material": ["cotton"]}, "profile_priors": {}, "unconstrained": []}
        result = reranker.rerank(pool, context)
        self.assertTrue(result.attempted)
        self.assertEqual(result.reason, "model_ranked", reranker.last_failure)
        self.assertEqual({item.parent_asin for item in result.candidates}, {item.parent_asin for item in pool})
        self.assertEqual(result.candidates[0].parent_asin, "BLUE")


if __name__ == "__main__":
    unittest.main()
