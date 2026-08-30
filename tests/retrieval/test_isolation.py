from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RETRIEVAL_ROOT = ROOT / "solution" / "retrieval"


class RetrievalIsolationTest(unittest.TestCase):
    def test_product_retrieval_does_not_import_evaluator_or_experiment_code(self) -> None:
        forbidden_roots = {"evaluator", "experiments", "scripts"}
        for path in RETRIEVAL_ROOT.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(
                imported & forbidden_roots,
                f"{path.relative_to(ROOT)} crosses the experiment/evaluator boundary",
            )

    def test_product_retrieval_contains_no_label_field_names(self) -> None:
        forbidden = ("ground_" + "truth", "target_" + "asin", "public_" + "set")
        for path in RETRIEVAL_ROOT.rglob("*.py"):
            content = path.read_text(encoding="utf-8").lower()
            for marker in forbidden:
                self.assertNotIn(marker, content, f"forbidden marker in {path.relative_to(ROOT)}")


if __name__ == "__main__":
    unittest.main()
