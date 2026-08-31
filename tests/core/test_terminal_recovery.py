from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from solution.contracts import Candidate, PreferenceSlot
from solution.question_policy import QUESTION_PRIORITY
from solution.retrieval.index import FTS5CatalogIndex
from solution.state import SessionState
from solution.terminal_recovery import TerminalRecovery, features


class TerminalRecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/"catalog.jsonl"
        products = [{"parent_asin": str(i), "title": "red leather" if i == 11 else "blue shoes",
                     "categories": ["Shoes"]} for i in range(30)]
        self.path.write_text("".join(json.dumps(p)+"\n" for p in products), encoding="utf-8")
        self.index = FTS5CatalogIndex(self.path)
        self.addCleanup(self.index.close)
        self.model = TerminalRecovery(self.index, "lastchance")
        self.addCleanup(self.model.close)
        self.items = [Candidate(str(i), i, 30-i, p["title"]) for i, p in enumerate(products)]
        self.state = SessionState.create("one", {})
        self.state.category = "Shoes"
        self.state.preferences["material"] = PreferenceSlot("material", ("red leather",), 1)

    def call(self, message="hello", k=10, fallback=False, items=None):
        items = self.items if items is None else items
        return self.model.reorder(items, self.state, items, message, k, fallback=fallback)

    def test_lazy_fields_and_terminal_rejection(self):
        self.assertEqual(self.call(), self.items)
        self.assertIsNone(self.model.fields)
        self.assertEqual(self.model.pool_limit(self.state, "hello", 10), 50)
        self.state.asked_attributes = list(QUESTION_PRIORITY)
        self.assertEqual(self.model.pool_limit(self.state, "not quite right", 10), 200)
        self.assertEqual(self.call("not quite right")[0].parent_asin, "11")
        self.assertTrue(self.model.last_active)

    def test_lastchance_only_final_unchanged_repeat(self):
        self.call()
        self.state.latest_turn = 9
        message = "I don't have an additional preference for style."
        self.assertEqual(self.call(message), self.items)
        self.state.latest_turn = 10
        self.assertEqual(self.model.pool_limit(self.state, message, 10), 200)
        self.assertEqual(self.call(message)[0].parent_asin, "11")
        self.assertTrue(self.model.last_active)

    def test_different_output_new_preference_and_override_do_not_trigger(self):
        self.call()
        self.state.latest_turn = 10
        message = "I don't have an additional preference for style."
        self.assertEqual(self.call(message, items=list(reversed(self.items))), list(reversed(self.items)))
        self.state.preferences["material"] = PreferenceSlot("material", ("cotton",), 10)
        self.assertEqual(self.call(message), self.items)
        self.assertEqual(self.call("Actually, not quite right"), self.items)
        self.assertFalse(self.model.last_active)

    def test_reset_sessions_and_zero_topk_history(self):
        self.call(k=0)
        self.assertEqual(self.model.sessions["one"].shown, ())
        self.state.latest_turn = 10
        self.assertEqual(self.call("no additional preference"), self.items)
        self.model.reset("one")
        self.assertEqual(self.call("no additional preference"), self.items)
        self.state.session_id = "two"
        self.assertEqual(self.call("no additional preference"), self.items)

    def test_fallback_and_terminal_mode_do_not_use_final_guard(self):
        self.call()
        self.state.latest_turn = 10
        self.assertEqual(self.call("no additional preference", fallback=True), self.items)
        self.model.mode = "terminal"
        self.assertEqual(self.call("no additional preference"), self.items)

    def test_feature_boundaries(self):
        row = features(self.items[11], self.state, "Red—leather", "Shoes", 0, 30)
        self.assertEqual(row[1:3], [1, 1])
        self.assertEqual(row[4], 1)
        self.assertEqual(features(self.items[11], self.state, "tired leathery", "Shoes", 0, 30)[4], 0)

    def test_agent_reset_and_empty_outputs(self):
        from starter.agent import Agent
        clean = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
        with patch.dict(os.environ, clean, clear=True):
            agent = Agent(self.path)
            try:
                self.assertEqual(agent._core._adaptive.terminal.mode, "lastchance")
                agent.reset("manual", {})
                first = agent.respond("manual", "I'm looking for shoes. What I need is: leather.", 1, 10)
                self.assertEqual(agent.respond("manual", "hello", 2, 0)["recommendations"], [])
                self.assertEqual(agent._core._adaptive.terminal.sessions["manual"].shown, ())
                agent.reset("manual", {})
                self.assertEqual(first, agent.respond("manual", "I'm looking for shoes. What I need is: leather.", 1, 10))
            finally:
                agent.close()

    def test_invalid_configuration_rejected_and_explicit_off(self):
        from starter.agent import Agent
        with patch.dict(os.environ, {"INTENTCOMPASS_TERMINAL_RECOVERY": "unknown"}):
            with self.assertRaises(ValueError):
                Agent(self.path)
        with patch.dict(os.environ, {"INTENTCOMPASS_TERMINAL_RECOVERY": "off"}):
            agent = Agent(self.path)
            try:
                self.assertIsNone(agent._core._adaptive.terminal)
            finally:
                agent.close()


if __name__ == "__main__":
    unittest.main()
