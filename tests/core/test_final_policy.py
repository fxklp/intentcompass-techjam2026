from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from solution.contracts import Candidate, PreferenceSlot
from solution.final_policy import DEFAULT, FinalPolicy
from solution.precision_order import PrecisionOrder
from solution.question_policy import choose_question
from solution.retrieval.index import FTS5CatalogIndex
from solution.state import SessionState


class FinalPolicyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "catalog.jsonl"
        rows = [{"parent_asin": str(i), "title": "red leather" if i == 1 else "blue garment",
                 "features": ["red leather"], "categories": ["Shoes"] if i < 10 else ["Bags"]}
                for i in range(12)]
        self.path.write_text("".join(json.dumps(r)+"\n" for r in rows), encoding="utf-8")
        self.index = FTS5CatalogIndex(self.path)
        self.addCleanup(self.index.close)
        self.precision = PrecisionOrder(self.index, "separate")
        self.addCleanup(self.precision.close)
        self.model = FinalPolicy(self.index, self.precision)
        self.addCleanup(self.model.close)
        self.items = [Candidate(str(i), i, 12-i, r["title"]+" red leather") for i, r in enumerate(rows)]
        self.state = SessionState.create("s", {})
        self.state.category = "Shoes"
        self.state.preferences["feature"] = PreferenceSlot("feature", ("red leather",), 1)
        self.state.latest_turn = 2

    def question(self, message="I have no preference.", **kwargs):
        return self.model.question(self.state, self.items, message, **kwargs)

    def test_title_membership_tail_and_stable_ties(self):
        before = copy.deepcopy(self.state)
        result = self.model.reorder(self.items, self.state)
        self.assertEqual(result[0].parent_asin, "1")
        self.assertEqual(set(result[:10]), set(self.items[:10]))
        self.assertEqual(result[10:], self.items[10:])
        self.assertEqual(result[1:10], [c for c in self.items[:10] if c.parent_asin != "1"])
        self.assertEqual(before, self.state)

    def test_contiguous_category_boundaries(self):
        items = [self.items[0], self.items[10], self.items[1]]
        self.assertEqual(self.model.reorder(items, self.state), items)

    def test_retrieval_gap_boundary(self):
        self.assertEqual(self.model.reorder([self.items[4], self.items[1]], self.state)[0], self.items[1])
        items = [self.items[5], self.items[1]]
        self.assertEqual(self.model.reorder(items, self.state), items)

    def test_full_phrase_groups_are_not_crossed(self):
        fields = {c.parent_asin: "blue" for c in self.items}
        fields["1"] = "red leather"
        with patch.object(self.model, "primary", return_value=fields):
            self.assertEqual(self.model.reorder(self.items, self.state), self.items)

    def test_incomparable_title_evidence_is_not_scalar_ranked(self):
        self.state.preferences["feature"] = PreferenceSlot("feature", ("red leather", "blue cotton"), 1)
        fields = {c.parent_asin: "red leather \n red leather blue cotton" for c in self.items}
        fields["1"] = "blue cotton \n red leather blue cotton"
        with patch.object(self.model, "primary", return_value=fields):
            self.assertEqual(self.model.reorder(self.items, self.state), self.items)

    def test_budget_exclusion_fallback_and_missing_guards(self):
        self.assertEqual(self.model.reorder(self.items, self.state, fallback=True), self.items)
        for key, value in (("budget", "under $20"), ("material", "no leather")):
            self.state.preferences[key] = PreferenceSlot(key, (value,), 1)
            self.assertEqual(self.model.reorder(self.items, self.state), self.items)
            del self.state.preferences[key]
        self.assertEqual(self.model.reorder([], self.state), [])
        self.assertEqual(self.model.reorder(self.items[:1], self.state), self.items[:1])
        self.state.preferences.clear()
        self.assertEqual(self.model.reorder(self.items, self.state), self.items)
        self.assertIsNone(self.precision.fields)

    def test_existing_field_reader_is_shared_and_bounded(self):
        self.precision.reorder(self.items, self.state)
        reader = self.precision.fields
        self.model.reorder(self.items, self.state)
        self.assertIs(self.precision.fields, reader)
        self.assertIs(reader.connection, self.index.connection)
        self.assertLessEqual(len(reader.cache), 256)
        self.model.close()
        self.assertTrue(reader.rowids)  # No second owner prematurely closing it.

    def test_exact_three_reply_threshold_and_no_repeat(self):
        self.assertEqual(self.question()[0], "material")
        self.assertEqual(self.question()[0], "material")
        self.assertEqual(self.question()[0], "other")
        self.state.mark_asked("other")
        self.assertEqual(self.question()[0], "material")
        self.assertEqual(self.model.question_changes, 1)

    def test_substantive_override_and_reset_clear_streak(self):
        for message in ("Actually, I have no preference.", "I need cotton."):
            self.question()
            self.question()
            self.question(message)
            self.assertEqual(self.model.streaks["s"], 0)
            self.assertEqual(self.question()[0], "material")
            self.model.reset("s")
        self.assertNotIn("s", self.model.streaks)

    def test_question_guards_and_isolation(self):
        self.model.streaks["s"] = 3
        self.assertEqual(self.question(fallback=True)[0], "material")
        self.assertEqual(self.question(output_limit=0)[0], "material")
        self.assertEqual(self.model.question(self.state, [], "I have no preference.")[0], "material")
        self.state.latest_turn = 10
        self.assertEqual(self.question(), choose_question(self.state))
        self.state.latest_turn = 2
        self.state.session_id = "independent"
        self.assertEqual(self.question()[0], "material")
        self.state.preferences.clear()
        self.assertEqual(self.question()[0], "feature")

    def test_other_unconstrained_or_known_is_never_reasked(self):
        self.model.streaks["s"] = 3
        self.state.unconstrained_attributes.add("other")
        self.assertEqual(self.question()[0], "material")
        self.state.unconstrained_attributes.clear()
        self.state.preferences["other"] = PreferenceSlot("other", ("light",), 1)
        self.assertEqual(self.question()[0], "material")

    def test_agent_default_on_explicit_off_and_incompatible_mode(self):
        from starter.agent import Agent
        clean = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
        self.assertEqual(DEFAULT, "on")
        for extra, enabled in (({}, True), ({"INTENTCOMPASS_FINAL_POLICY": "off"}, False),
                               ({"INTENTCOMPASS_PRECISION_ORDER": "off"}, False)):
            with patch.dict(os.environ, dict(clean, **extra), clear=True):
                agent = Agent(self.path)
                try:
                    self.assertEqual(agent._core._adaptive.final_policy is not None, enabled)
                finally:
                    agent.close()
        with patch.dict(os.environ, dict(clean, INTENTCOMPASS_FINAL_POLICY="invalid"), clear=True):
            with self.assertRaisesRegex(ValueError, "must be on or off"):
                Agent(self.path)

    def test_agent_reset_zero_k_and_turn_ten(self):
        from starter.agent import Agent
        clean = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
        with patch.dict(os.environ, clean, clear=True):
            agent = Agent(self.path)
            try:
                message = "I'm looking for Shoes. What I need is: red leather."
                agent.reset("a", {})
                first = agent.respond("a", message, 1, 10)
                agent.respond("a", "I have no preference for material.", 2, 10)
                agent.respond("a", "I have no preference for color.", 3, 10)
                self.assertTrue(agent._core._adaptive.final_policy.streaks["a"])
                agent.reset("a", {})
                self.assertNotIn("a", agent._core._adaptive.final_policy.streaks)
                self.assertEqual(first, agent.respond("a", message, 1, 10))
                agent.reset("b", {})
                self.assertEqual(first, agent.respond("b", message, 1, 10))
                self.assertEqual(agent.respond("a", "I have no preference.", 10, 0)["recommendations"], [])
                self.assertIsNone(agent.respond("a", "I have no preference.", 10, 10)["ask_attribute"])
                self.assertEqual(first["usage"], {"prompt_tokens": 0, "completion_tokens": 0})
            finally:
                agent.close()


if __name__ == "__main__":
    unittest.main()
