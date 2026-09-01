from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starter.agent import Agent
from solution.retrieval.capability import CapabilityRetriever
from solution.retrieval.contracts import RetrievalConstraint, RetrievalRequest


PRODUCTS = [
    {"parent_asin": "RED", "title": "red leather walking shoes", "categories": ["shoes"], "price": 120},
    {"parent_asin": "BLUE", "title": "blue cotton walking shoes", "categories": ["shoes"], "price": 40},
    {"parent_asin": "BOOT", "title": "black waterproof hiking boot", "categories": ["boots"], "price": 70},
    {"parent_asin": "BAG", "title": "formal leather business bag", "categories": ["bags"], "price": 30},
]


class Task306Capabilities(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.catalog = root / "catalog.jsonl"
        self.catalog.write_text("".join(json.dumps(row) + "\n" for row in PRODUCTS), encoding="utf-8", newline="\n")
        self.assets = root / "missing-assets"

    def test_early_cutoff_skips_fts_and_returns_traceable_fallback(self):
        retriever = CapabilityRetriever(self.catalog, self.assets)
        self.addCleanup(retriever.close)
        with patch.object(retriever.index, "search", wraps=retriever.index.search) as search:
            result = retriever.search(RetrievalRequest("anything", 3, "browsing"))
        search.assert_not_called()
        self.assertIn("early_overgenerality_cutoff", result.trace.reason_codes)
        self.assertEqual(len(result.candidates), 3)

    def test_buying_and_browsing_execute_different_real_routes(self):
        retriever = CapabilityRetriever(self.catalog, self.assets)
        self.addCleanup(retriever.close)
        buying = retriever.search(RetrievalRequest(
            "walking shoes blue", 4, "buying", "shoes",
            (RetrievalConstraint("color", ("blue",)),), 2,
        ))
        browsing = retriever.search(RetrievalRequest("walking shoes", 4, "browsing", "shoes"))
        self.assertEqual(buying.trace.selected_path, "buying")
        self.assertIn("exact_constraints", buying.trace.routes)
        self.assertEqual(browsing.trace.selected_path, "browsing")
        self.assertNotIn("exact_constraints", browsing.trace.routes)

    def test_known_budget_conflict_is_demoted_but_unknown_is_not_invented(self):
        retriever = CapabilityRetriever(self.catalog, self.assets)
        self.addCleanup(retriever.close)
        result = retriever.search(RetrievalRequest(
            "walking shoes", 4, "buying", "shoes",
            (RetrievalConstraint("budget", ("under $50",)),), 2,
        ))
        ids = [item.parent_asin for item in result.candidates]
        self.assertLess(ids.index("BLUE"), ids.index("RED"))
        self.assertTrue(any(code.startswith("constraints_satisfied:") for code in result.trace.reason_codes))
        self.assertIn("explicit_constraint_relaxation_for_result_fill", result.trace.reason_codes)

    def test_positive_attribute_match_is_satisfied_and_other_parent_metadata_is_unknown(self):
        retriever = CapabilityRetriever(self.catalog, self.assets)
        self.addCleanup(retriever.close)
        result = retriever.search(RetrievalRequest(
            "walking shoes", 4, "buying", "shoes",
            (RetrievalConstraint("color", ("blue",)),), 2,
        ))
        ids = [item.parent_asin for item in result.candidates]
        self.assertIn("BLUE", ids)
        blue = next(item for item in result.candidates if item.parent_asin == "BLUE")
        self.assertIn("exact_constraints", {e.route for e in blue.evidence})
        self.assertTrue(any(code.startswith("constraints_unknown:") for code in result.trace.reason_codes))

    def test_explicit_profile_handoff_affects_next_caller_supplied_session(self):
        env = {
            "INTENTCOMPASS_AGENT_MODE": "integrated", "INTENTCOMPASS_RETRIEVAL": "capability",
            "INTENTCOMPASS_SEMANTIC": "off", "INTENTCOMPASS_CATEGORY_ORDER": "head",
            "INTENTCOMPASS_TERMINAL_RECOVERY": "lastchance", "INTENTCOMPASS_PRECISION_ORDER": "separate",
            "INTENTCOMPASS_FINAL_POLICY": "on",
        }
        with patch.dict(os.environ, env):
            agent = Agent(self.catalog)
        self.addCleanup(agent.close)
        agent.reset("first", {})
        agent.respond("first", "I'm looking for shoes. A key requirement is: blue.", 1, 4)
        profile = agent.export_profile("first")
        self.assertIn("blue", profile["preference_tags"])
        agent.reset("next", profile)
        result = agent.respond("next", "I'm looking for shoes, but I'm still exploring.", 1, 4)
        self.assertEqual(result["recommendations"][0]["parent_asin"], "BLUE")
        agent.reset("isolated", {})
        isolated = agent.respond("isolated", "I'm looking for shoes, but I'm still exploring.", 1, 4)
        self.assertEqual(isolated["recommendations"][0]["parent_asin"], "RED")

    def test_feedback_reorchestrates_query_and_preserves_preferences(self):
        with patch.dict(os.environ, {"INTENTCOMPASS_RETRIEVAL": "capability", "INTENTCOMPASS_SEMANTIC": "off"}):
            agent = Agent(self.catalog)
        self.addCleanup(agent.close)
        agent.reset("flow", {})
        agent.respond("flow", "I'm looking for shoes. A key requirement is: blue.", 1, 4)
        agent.respond("flow", "Those options are not quite right yet.", 2, 4)
        agent.respond("flow", "Those options are not quite right yet.", 3, 4)
        trace = agent._core._adaptive.sessions["flow"].last_trace
        self.assertEqual(trace["workflow"], "recover_after_miss_or_rejection")
        self.assertGreaterEqual(trace["pool_limit"], 80)
        self.assertEqual(trace["query"], "shoes blue")
        self.assertEqual(trace["intent_route"], "buying")
        self.assertIn("blue", json.dumps(trace["context"]["explicit"]))


if __name__ == "__main__":
    unittest.main()
