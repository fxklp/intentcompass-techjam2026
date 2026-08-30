from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.retrieval.test_retrievers import PRODUCTS


ROOT = Path(__file__).resolve().parents[2]


class RetrievalBenchmarkTest(unittest.TestCase):
    def test_each_variant_runs_in_an_independent_child_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            catalog = directory / "catalog.jsonl"
            output = directory / "benchmark.json"
            catalog.write_text(
                "".join(json.dumps(product) + "\n" for product in PRODUCTS),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "benchmark_retrieval.py"),
                    "--catalog",
                    str(catalog),
                    "--iterations",
                    "1",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            raw_output = output.read_bytes()
            self.assertTrue(raw_output.endswith(b"\n"))
            self.assertNotIn(b"\r\n", raw_output)
            result = json.loads(raw_output.decode("utf-8"))
            baseline_pid = result["baseline"]["process_id"]
            candidate_pid = result["candidate"]["process_id"]
            self.assertNotEqual(os.getpid(), baseline_pid)
            self.assertNotEqual(os.getpid(), candidate_pid)
            self.assertNotEqual(baseline_pid, candidate_pid)


if __name__ == "__main__":
    unittest.main()
