from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from solution.retrieval.baseline import BaselineFTS5Retriever
from solution.retrieval.contracts import RetrievalRequest
from solution.retrieval.hybrid import HybridRetriever
from solution.retrieval.onnx_models import MODEL_FILES, MODELS, sha256, verify_model


class HybridTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.catalog = self.directory / "catalog.jsonl"
        products = [
            {"parent_asin":"A", "title":"red running shoes", "categories":["shoes"], "price":40, "rating_number":5},
            {"parent_asin":"B", "title":"blue walking sneakers", "categories":["shoes"], "price":50, "rating_number":20},
            {"parent_asin":"C", "title":"formal leather bag", "categories":["bags"], "price":80, "rating_number":10},
        ]
        self.catalog.write_text("".join(json.dumps(value)+"\n" for value in products), encoding="utf-8", newline="\n")

    def make_hybrid(self, dense=None):
        with patch("solution.retrieval.dense.DenseIndex", return_value=dense, side_effect=None if dense is not None else FileNotFoundError):
            retriever = HybridRetriever(self.catalog, self.directory)
        self.addCleanup(retriever.close)
        return retriever

    def test_missing_assets_exact_lexical_fallback_no_download(self):
        retriever = self.make_hybrid()
        baseline = BaselineFTS5Retriever(self.catalog)
        self.addCleanup(baseline.close)
        for query in ("shoes", "zzzznomatch"):
            request = RetrievalRequest(query, 10)
            with patch("socket.create_connection", side_effect=AssertionError("offline")):
                self.assertEqual(retriever.search(request), baseline.search(request))

    def test_real_route_names_fusion_unique_catalog_ids(self):
        dense = Mock(ids=["A","B","C"])
        dense.search.return_value = [("B", .8), ("A", .7)]
        retriever = self.make_hybrid(dense)
        for route, expected_limit in (("buying",15),("browsing",30)):
            result = retriever.search(RetrievalRequest("shoes", 3, route, "shoes"))
            self.assertEqual(result.trace.selected_path, route)
            self.assertEqual(result.trace.routes, ("keyword","category","dense"))
            self.assertEqual(len({item.parent_asin for item in result.candidates}), len(result.candidates))
            dense.search.assert_called_with("shoes", expected_limit)
            self.assertTrue(any(any(item.route == "dense" for item in candidate.evidence) for candidate in result.candidates))

    def test_semantic_recovery_and_weak_no_match_fallback(self):
        dense = Mock(ids=["A","B","C"])
        dense.search.return_value = [("B", .7)]
        retriever = self.make_hybrid(dense)
        request = RetrievalRequest("trainers", 3, "browsing")
        result = retriever.search(request)
        self.assertFalse(result.trace.fallback_used)
        self.assertEqual(result.candidates[0].parent_asin, "B")
        dense.search.return_value = [("B", .1)]
        result = retriever.search(request)
        self.assertTrue(result.trace.fallback_used)
        self.assertEqual([item.parent_asin for item in result.candidates], retriever.index.fallback_ids)

    def test_model_failure_opens_circuit_and_preserves_baseline(self):
        dense = Mock(ids=["A","B","C"])
        dense.search.side_effect = RuntimeError("inference failed")
        retriever = self.make_hybrid(dense)
        request = RetrievalRequest("shoes", 3)
        result = retriever.search(request)
        self.assertEqual(result.trace.selected_path, "baseline")
        retriever.search(request)
        self.assertEqual(dense.search.call_count, 1)
        self.assertEqual(retriever.dense_status, "runtime_failure_lexical_fallback")

    def test_foreign_index_rejected(self):
        retriever = self.make_hybrid(Mock(ids=["A","B","ALIEN"]))
        self.assertIsNone(retriever.dense)

    def test_category_storage_shared_without_changing_values(self):
        retriever = BaselineFTS5Retriever(self.catalog)
        self.addCleanup(retriever.close)
        first = retriever.index.products["A"]
        second = retriever.index.products["B"]
        self.assertEqual(first.categories, ("shoes",))
        self.assertIs(first.categories[0], second.categories[0])
        self.assertFalse(hasattr(first, "__dict__"))

    def test_artifact_hash_tamper_rejected_before_model_load(self):
        directory = self.directory / "model"
        for name in MODEL_FILES:
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")
        repository, revision = MODELS["embedding"]
        manifest = {"repository":repository, "revision":revision, "sha256":{name:sha256(directory / name) for name in MODEL_FILES}}
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        verify_model(directory, "embedding")
        (directory / "tokenizer.json").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            verify_model(directory, "embedding")


@unittest.skipUnless(importlib.util.find_spec("onnxruntime") and (Path(__file__).resolve().parents[2] / "artifacts/semantic/embedding/manifest.json").exists(), "optional pinned assets/runtime not installed")
class RealLocalModelSmoke(unittest.TestCase):
    def test_real_embeddings_normalized_and_cross_encoder_fits_text(self):
        import numpy as np
        from solution.retrieval.onnx_models import LocalModel
        assets = Path(__file__).resolve().parents[2] / "artifacts/semantic"
        encoder = LocalModel(assets / "embedding", "embedding")
        vectors = encoder.predict(["red running shoes", "red running shoes", "formal leather bag"])
        self.assertEqual(vectors.shape, (3,384))
        self.assertTrue(np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5))
        self.assertTrue(np.allclose(vectors[0], vectors[1]))
        self.assertGreater(float(vectors[0] @ vectors[1]), float(vectors[0] @ vectors[2]))
        ranker = LocalModel(assets / "reranker", "reranker")
        scores = ranker.predict([("red running shoes","red breathable running shoes"),("red running shoes","formal blue leather bag")])
        self.assertGreater(scores[0], scores[1])


if __name__ == "__main__":
    unittest.main()
