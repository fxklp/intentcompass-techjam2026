from __future__ import annotations

import unittest

from scripts.team_gate import evaluation_threshold_violations, trailing_whitespace_lines


PASSING_RESULT = {
    "sample_count": 200,
    "hit_rate_at_10": 0.75,
    "recommended_technical_score": 0.60,
    "scenario_metrics": {
        name: {"hit_rate_at_10": 0.60}
        for name in ("boundary", "browsing", "buying", "intent_override")
    },
}


class TeamGateThresholdTest(unittest.TestCase):
    def test_exact_milestone_thresholds_pass(self) -> None:
        self.assertEqual(evaluation_threshold_violations(PASSING_RESULT), [])

    def test_regression_and_missing_scenario_are_rejected(self) -> None:
        result = {
            **PASSING_RESULT,
            "hit_rate_at_10": 0.74,
            "recommended_technical_score": 0.59,
            "scenario_metrics": {
                "boundary": {"hit_rate_at_10": 0.59},
                "browsing": {"hit_rate_at_10": 0.90},
                "buying": {"hit_rate_at_10": 0.90},
            },
        }
        violations = "\n".join(evaluation_threshold_violations(result))
        self.assertIn("HitRate@10 must be >= 0.75", violations)
        self.assertIn("TechnicalScore must be >= 0.60", violations)
        self.assertIn("boundary HitRate@10 must be >= 0.60", violations)
        self.assertIn("missing scenario metrics: intent_override", violations)

    def test_trailing_whitespace_detection_covers_markdown_breaks_and_tabs(self) -> None:
        content = "clean\nmarkdown break  \ntrailing tab\t\nclean again\n"
        self.assertEqual(trailing_whitespace_lines(content), [2, 3])


if __name__ == "__main__":
    unittest.main()
