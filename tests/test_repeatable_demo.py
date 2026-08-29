from __future__ import annotations

import unittest

from demo.run_demo import run_session


class RepeatableDemoTest(unittest.TestCase):
    def test_default_demo_replaces_old_preference_and_hits_after_override(self) -> None:
        result = run_session(verbose=False)
        self.assertTrue(result["override_seen"])
        self.assertTrue(result["hit"])
        self.assertEqual(result["first_hit_turn"], 3)
        self.assertEqual(result["best_rank"], 1)

        active = " ".join(
            value
            for values in result["active_preferences"].values()
            for value in values
        ).casefold()
        self.assertNotIn(result["old_value"].casefold(), active)
        self.assertIn(result["new_value"].casefold(), active)


if __name__ == "__main__":
    unittest.main()
