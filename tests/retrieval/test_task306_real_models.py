from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from solution.contracts import Candidate
from solution.local_reranker import LocalReranker
from solution.retrieval.capability import CapabilityRetriever
from solution.retrieval.contracts import RetrievalRequest


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "artifacts/semantic"


@unittest.skipUnless(
    importlib.util.find_spec("onnxruntime") and (ASSETS / "index-manifest.json").exists(),
    "pinned semantic assets/runtime not installed",
)
class Task306RealModels(unittest.TestCase):
    def test_real_dense_and_cross_encoder_inference_drive_order(self):
        retriever = CapabilityRetriever(ROOT / "data/catalog.jsonl", ASSETS)
        self.addCleanup(retriever.close)
        self.assertEqual(retriever.dense_status, "ready")
        with patch.dict(os.environ, {"INTENTCOMPASS_FORCE_SEMANTIC": "1"}):
            found = retriever.search(RetrievalRequest(
                "surprise me with footwear for trail adventures", 20, "browsing", None, (), 1,
            ))
        self.assertIn("dense", found.trace.routes)
        self.assertTrue(any(any(e.route == "dense" for e in item.evidence) for item in found.candidates))
        ranker = LocalReranker(ASSETS)
        self.assertIsNotNone(ranker.model)
        pool = [
            Candidate("TRAIL", 0, 0, "waterproof trail hiking shoe for outdoor adventures", 70),
            Candidate("FORMAL", 1, 0, "formal leather business bag", 70),
        ]
        result = ranker.rerank(pool, {"category": "shoes", "explicit": {"use_case": ["trail hiking"]}})
        self.assertEqual(result.reason, "cross_encoder_ranked")
        self.assertEqual(result.candidates[0].parent_asin, "TRAIL")


if __name__ == "__main__":
    unittest.main()
