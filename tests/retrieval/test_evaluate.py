from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from experiments.retrieval.evaluate import (
    add_scenario_technical_scores,
    assert_scenario_consistency,
)


class ScenarioTechnicalScoreTest(unittest.TestCase):
    def test_checked_in_raw_runs_regenerate_consistent_scenario_scores(self) -> None:
        results_path = (
            Path(__file__).resolve().parents[2]
            / "reports"
            / "experiments"
            / "TASK-303-results.json"
        )
        results = json.loads(results_path.read_text(encoding="utf-8"))
        for run in results["runs"].values():
            metrics = copy.deepcopy(run["metrics"])
            add_scenario_technical_scores(metrics)
            assert_scenario_consistency(metrics)

    def test_scores_are_generated_from_raw_scenario_json_and_are_consistent(self) -> None:
        metrics: dict[str, object] = {
            "sample_count": 4,
            "hit_rate_at_10": 0.75,
            "mrr": 0.5,
            "mttc": 5.5,
            "efficiency": 0.55,
            "recommended_technical_score": 0.635,
            "scenario_metrics": {
                "buying": {
                    "sample_count": 2,
                    "hit_rate_at_10": 1.0,
                    "mrr": 0.75,
                    "mttc": 3.0,
                },
                "browsing": {
                    "sample_count": 2,
                    "hit_rate_at_10": 0.5,
                    "mrr": 0.25,
                    "mttc": 8.0,
                },
            },
        }

        add_scenario_technical_scores(metrics)

        scenarios = metrics["scenario_metrics"]
        assert isinstance(scenarios, dict)
        self.assertEqual(0.885, scenarios["buying"]["recommended_technical_score"])
        self.assertEqual(0.385, scenarios["browsing"]["recommended_technical_score"])
        assert_scenario_consistency(metrics)

    def test_inconsistent_raw_scenario_json_is_rejected(self) -> None:
        metrics: dict[str, object] = {
            "sample_count": 2,
            "hit_rate_at_10": 1.0,
            "mrr": 1.0,
            "mttc": 1.0,
            "efficiency": 1.0,
            "recommended_technical_score": 1.0,
            "scenario_metrics": {
                "buying": {
                    "sample_count": 1,
                    "hit_rate_at_10": 1.0,
                    "mrr": 1.0,
                    "mttc": 1.0,
                }
            },
        }
        add_scenario_technical_scores(metrics)
        with self.assertRaisesRegex(ValueError, "sample count"):
            assert_scenario_consistency(metrics)


if __name__ == "__main__":
    unittest.main()
