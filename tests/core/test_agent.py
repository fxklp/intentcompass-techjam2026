from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starter.agent import Agent


CATALOG = (
    {
        "parent_asin": "BLUE",
        "title": "Blue cotton running shoe",
        "features": ["lightweight", "wide fit"],
        "categories": ["Shoes"],
        "details": {},
        "description": [],
        "store": "Example",
        "price": 40,
        "average_rating": 4.5,
        "rating_number": 100,
    },
    {
        "parent_asin": "RED",
        "title": "Red leather formal shoe",
        "features": ["narrow fit"],
        "categories": ["Shoes"],
        "details": {},
        "description": [],
        "store": "Example",
        "price": 80,
        "average_rating": 4.0,
        "rating_number": 20,
    },
)


class AgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.catalog_path = Path(self.temporary_directory.name) / "catalog.jsonl"
        self.catalog_path.write_text(
            "".join(json.dumps(item) + "\n" for item in CATALOG),
            encoding="utf-8",
        )
        self.agent = Agent(self.catalog_path)

    def tearDown(self) -> None:
        self.agent.close()
        self.temporary_directory.cleanup()

    def test_close_is_idempotent(self) -> None:
        self.agent.close()
        self.agent.close()

    def test_browsing_turn_preserves_baseline_order_and_returns_valid_schema(self) -> None:
        self.agent.reset("session", {})
        response = self.agent.respond("session", "I'm looking for shoes, but I'm still exploring.", 1, 10)

        self.assertIsInstance(response["message"], str)
        self.assertEqual(response["ask_attribute"], "feature")
        self.assertEqual(
            response["recommendations"],
            [{"parent_asin": "RED"}, {"parent_asin": "BLUE"}],
        )
        self.assertEqual(len(response["recommendations"]), len({item["parent_asin"] for item in response["recommendations"]}))
        self.assertEqual(response["usage"], {"prompt_tokens": 0, "completion_tokens": 0})

    def test_questions_are_not_repeated_after_boundary_reply(self) -> None:
        self.agent.reset("session", {})
        first = self.agent.respond("session", "I'm looking for shoes.", 1, 10)
        second = self.agent.respond(
            "session",
            "I don't have a preference for feature; please use your judgment.",
            2,
            10,
        )

        self.assertEqual(first["ask_attribute"], "feature")
        self.assertNotEqual(second["ask_attribute"], first["ask_attribute"])
        self.assertTrue(second["recommendations"])

    def test_empty_query_uses_deterministic_offline_fallback(self) -> None:
        self.agent.reset("session", {})
        first = self.agent.respond("session", "...", 1, 10)
        self.agent.reset("session", {})
        second = self.agent.respond("session", "...", 1, 10)
        self.assertEqual(first["recommendations"], second["recommendations"])
        self.assertTrue(first["recommendations"])

    def test_sessions_are_isolated_and_reset_is_required(self) -> None:
        with self.assertRaises(RuntimeError):
            self.agent.respond("missing", "blue shoes", 1, 10)
        self.agent.reset("one", {})
        self.agent.reset("two", {})
        self.agent.respond("one", "I'm looking for shoes.", 1, 10)
        response = self.agent.respond("two", "I'm looking for shoes.", 1, 10)
        self.assertEqual(response["ask_attribute"], "feature")


if __name__ == "__main__":
    unittest.main()
