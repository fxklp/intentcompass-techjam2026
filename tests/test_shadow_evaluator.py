from __future__ import annotations

import unittest
from collections import Counter

from scripts.shadow_evaluator import SCENARIO_COUNTS, scenario_sequence, select_targets


class ShadowEvaluatorTest(unittest.TestCase):
    def test_selection_is_deterministic_and_excludes_public_targets(self) -> None:
        catalog = {f"P{index:03d}" for index in range(20)}
        public = {"P001", "P002", "P003"}
        first = select_targets(catalog, public, 10, "fixture")
        second = select_targets(catalog, public, 10, "fixture")
        self.assertEqual(first, second)
        self.assertFalse(set(first) & public)
        self.assertEqual(len(first), len(set(first)))

    def test_scenario_mix_matches_official_proportions(self) -> None:
        self.assertEqual(Counter(scenario_sequence()), Counter(SCENARIO_COUNTS))

    def test_insufficient_non_public_targets_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            select_targets({"A", "B"}, {"A"}, 2)


if __name__ == "__main__":
    unittest.main()
