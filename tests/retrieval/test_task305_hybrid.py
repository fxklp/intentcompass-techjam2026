from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from solution.retrieval.contracts import RetrievalRequest
from solution.retrieval.hybrid import HybridRetriever


class Task305HybridBehaviorTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog = self.root / "catalog.jsonl"
        rows = [
            {"parent_asin": "A", "title": "casual shoes alpha", "categories": ["shoes", "sneakers"]},
            {"parent_asin": "B", "title": "casual shoes beta", "categories": ["shoes", "sneakers"]},
            {"parent_asin": "C", "title": "casual shoes gamma", "categories": ["shoes", "boots"]},
        ]
        self.catalog.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8", newline="\n")

    def test_route_weights_and_vector_diversity_change_real_candidate_order(self) -> None:
        dense = Mock(ids=["A", "B", "C"])
        dense.search.return_value = [("A", .9), ("B", .8), ("C", .7)]
        dense.similarity.side_effect = lambda left, right: .99 if {left, right} <= {"A", "B"} else .1
        with patch("solution.retrieval.dense.DenseIndex", return_value=dense):
            retriever = HybridRetriever(self.catalog, self.root)
        self.addCleanup(retriever.close)
        buying = retriever.search(RetrievalRequest("casual shoes", 3, "buying", "shoes"))
        browsing = retriever.search(RetrievalRequest("casual shoes", 3, "browsing", "shoes"))
        self.assertEqual([item.parent_asin for item in buying.candidates], ["A", "B", "C"])
        self.assertEqual([item.parent_asin for item in browsing.candidates], ["A", "C", "B"])
        self.assertEqual(browsing.trace.routes, ("keyword", "category", "dense"))
        self.assertIn("bounded_vector_diversity", browsing.trace.reason_codes)
        self.assertNotEqual(
            [item.parent_asin for item in buying.candidates],
            [item.parent_asin for item in browsing.candidates],
        )


@unittest.skipUnless(
    importlib.util.find_spec("onnxruntime")
    and (Path(__file__).resolve().parents[2] / "artifacts/semantic/index-manifest.json").exists(),
    "pinned dense index/runtime not installed",
)
class RealDenseCandidateTest(unittest.TestCase):
    def test_real_text_vector_channel_is_active_in_candidate_fusion(self) -> None:
        root = Path(__file__).resolve().parents[2]
        retriever = HybridRetriever(root / "data/catalog.jsonl", root / "artifacts/semantic")
        self.addCleanup(retriever.close)
        self.assertEqual(retriever.dense_status, "ready")
        result = retriever.search(RetrievalRequest("comfortable footwear for jogging", 10, "browsing", "shoes"))
        self.assertIn("dense", result.trace.routes)
        self.assertGreater(dict(result.trace.route_candidate_counts)["dense"], 0)
        self.assertTrue(any(any(e.route == "dense" for e in item.evidence) for item in result.candidates))
        self.assertEqual(len({item.parent_asin for item in result.candidates}), len(result.candidates))


if __name__ == "__main__":
    unittest.main()
