from __future__ import annotations

import unittest

from scripts.benchmark_runtime import percentile


class RuntimeBenchmarkTest(unittest.TestCase):
    def test_nearest_rank_percentile(self) -> None:
        values = [5.0, 1.0, 3.0, 2.0, 4.0]
        self.assertEqual(percentile(values, 0.50), 3.0)
        self.assertEqual(percentile(values, 0.95), 5.0)

    def test_empty_percentile_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            percentile([], 0.50)


if __name__ == "__main__":
    unittest.main()
