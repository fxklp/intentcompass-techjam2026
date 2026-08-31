from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from solution.contracts import Candidate, PreferenceSlot
from solution.precision_order import DEFAULT, PrecisionOrder, matches_all
from solution.retrieval.index import FTS5CatalogIndex
from solution.state import SessionState


class PrecisionOrderTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "catalog.jsonl"
        rows = [{"parent_asin": str(i), "title": "red leather" if i == 2 else "blue cotton",
                 "categories": ["Shoes"] if i < 10 else ["Bags"]} for i in range(12)]
        self.path.write_text("".join(json.dumps(r)+"\n" for r in rows), encoding="utf-8")
        self.index = FTS5CatalogIndex(self.path)
        self.addCleanup(self.index.close)
        self.items = [Candidate(str(i), i, 12-i, r["title"]) for i, r in enumerate(rows)]
        self.state = SessionState.create("s", {})
        self.state.category = "Shoes"
        self.state.preferences["feature"] = PreferenceSlot("feature", ("red leather",), 1)

    def model(self, variant):
        model = PrecisionOrder(self.index, variant)
        self.addCleanup(model.close)
        return model

    def test_partition_membership_tail_and_ties(self):
        for variant in ("joined", "separate"):
            result = self.model(variant).reorder(self.items, self.state)
            self.assertEqual(result[0].parent_asin, "2")
            self.assertEqual(set(result[:10]), set(self.items[:10]))
            self.assertEqual(result[10:], self.items[10:])
            self.assertEqual(result[1:10], [x for x in self.items[:10] if x.parent_asin != "2"])

    def test_category_boundaries(self):
        items = [self.items[0], self.items[10], self.items[2]]
        for variant in ("joined", "separate"):
            self.assertEqual(self.model(variant).reorder(items, self.state), items)

    def test_token_boundaries_and_normalization(self):
        for separate in (True, False):
            self.assertTrue(matches_all([("red", "leather")], "RED—leather", separate=separate))
            self.assertFalse(matches_all([("red", "leather")], "tired leathery", separate=separate))

    def test_field_boundary_and_conjunction(self):
        query = [("red", "leather")]
        self.assertTrue(matches_all(query, "red \n leather \n ", separate=False))
        self.assertFalse(matches_all(query, "red \n leather \n ", separate=True))
        self.assertTrue(matches_all([("red",), ("leather",)], "red \n leather \n ", separate=True))
        self.assertFalse(matches_all([("red",), ("cotton",)], "red \n leather \n ", separate=True))

    def test_real_reader_preserves_field_boundaries(self):
        for variant in ("joined", "separate"):
            model = self.model(variant)
            model.reorder(self.items, self.state)
            fields = model.fields.get(["2"])
            self.assertIn(" \n ", fields["2"])
            self.assertTrue(matches_all([("red", "leather")], fields["2"], separate=True))
            self.assertLessEqual(len(model.fields.cache), 256)

    def test_no_partial_promotion(self):
        self.state.preferences["color"] = PreferenceSlot("color", ("green",), 1)
        for variant in ("joined", "separate"):
            self.assertEqual(self.model(variant).reorder(self.items, self.state), self.items)

    def test_budget_and_exclusion_guards(self):
        for variant in ("joined", "separate"):
            model = self.model(variant)
            for key, value in (("budget", "under $20"), ("material", "no leather")):
                self.state.preferences[key] = PreferenceSlot(key, (value,), 1)
                self.assertEqual(model.reorder(self.items, self.state), self.items)
                self.assertIsNone(model.fields)
                del self.state.preferences[key]

    def test_fallback_empty_missing_and_single_token(self):
        for variant in ("joined", "separate"):
            model = self.model(variant)
            self.assertEqual(model.reorder(self.items, self.state, fallback=True), self.items)
            self.assertEqual(model.reorder([], self.state), [])
            self.assertIsNone(model.fields)
            self.assertFalse(matches_all([("red", "leather")], "", separate=variant == "separate"))
        self.state.preferences.clear()
        model = self.model("separate")
        self.assertEqual(model.reorder(self.items, self.state), self.items)
        self.state.preferences["color"] = PreferenceSlot("color", ("red",), 1)
        self.assertEqual(model.reorder(self.items, self.state), self.items)
        self.assertIsNone(model.fields)

    def test_agent_reset_override_isolation_and_zero_k(self):
        from starter.agent import Agent
        clean = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
        for variant in ("joined", "separate"):
            with patch.dict(os.environ, dict(clean, INTENTCOMPASS_PRECISION_ORDER=variant), clear=True):
                agent = Agent(self.path)
                try:
                    message = "I'm looking for shoes. What I need is: red leather."
                    agent.reset("a", {})
                    first = agent.respond("a", message, 1, 10)
                    agent.respond("a", "Actually, what I need is: blue cotton.", 2, 10)
                    agent.reset("b", {})
                    self.assertEqual(first, agent.respond("b", message, 1, 10))
                    agent.reset("a", {})
                    self.assertEqual(first, agent.respond("a", message, 1, 10))
                    self.assertEqual(agent.respond("a", "hello", 2, 0)["recommendations"], [])
                finally:
                    agent.close()

    def test_default_configuration(self):
        from starter.agent import Agent
        clean = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
        with patch.dict(os.environ, clean, clear=True):
            agent = Agent(self.path)
            try:
                component = agent._core._adaptive.precision
                self.assertEqual(component.variant if component else "off", DEFAULT)
            finally:
                agent.close()

    def test_invalid_configuration(self):
        from starter.agent import Agent
        for variant in ("off", "invalid"):
            with self.assertRaises(ValueError):
                self.model(variant)
        with patch.dict(os.environ, {"INTENTCOMPASS_PRECISION_ORDER": "invalid"}):
            with self.assertRaises(ValueError):
                Agent(self.path)


if __name__ == "__main__":
    unittest.main()
