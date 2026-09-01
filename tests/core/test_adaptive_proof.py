from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tests.core.check_adaptive import non_regression, sha256, write_json


class AdaptiveProofTest(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = {"hit_rate_at_10": 0.9, "mrr": 0.6, "mttc": 4.0, "scenario_metrics": {"browsing": {"hit_rate_at_10": 0.8, "mrr": 0.5, "mttc": 5.0}}}

    def test_overall_gain_does_not_hide_scenario_regression(self) -> None:
        candidate = copy.deepcopy(self.metrics)
        candidate["hit_rate_at_10"] = 0.95
        candidate["scenario_metrics"]["browsing"]["mrr"] = 0.4
        self.assertEqual(len(non_regression(self.metrics, candidate)), 1)
        self.assertIn("browsing.mrr", non_regression(self.metrics, candidate)[0])

    def test_missing_scenario_and_slower_conversion_fail(self) -> None:
        candidate = copy.deepcopy(self.metrics)
        candidate["mttc"] = 5.0
        candidate["scenario_metrics"] = {}
        self.assertEqual(len(non_regression(self.metrics, candidate)), 2)
        self.assertEqual(non_regression(self.metrics, self.metrics), [])

    def test_evidence_lf_utf8_and_byte_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proof.json"
            write_json(path, {"message": "偏好"})
            original = sha256(path)
            self.assertNotIn(b"\r", path.read_bytes())
            self.assertIn("偏好", path.read_text(encoding="utf-8"))
            write_json(path, {"message": "changed"})
            self.assertNotEqual(sha256(path), original)


if __name__ == "__main__":
    unittest.main()
