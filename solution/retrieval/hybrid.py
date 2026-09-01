"""Keyword/category/dense recall, one lexical index, explicit safe fallback."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from solution.retrieval.baseline import BaselineFTS5Retriever, BASELINE_WEIGHTS
from solution.retrieval.contracts import Candidate, RetrievalResult, RetrievalTrace, RouteEvidence
from solution.retrieval.index import and_expression, terms


class HybridRetriever(BaselineFTS5Retriever):
    def __init__(self, catalog_path: Path, assets: Path) -> None:
        super().__init__(catalog_path)
        self.dense = None
        self.dense_status = "unavailable_lexical_fallback"
        try:
            from solution.retrieval.dense import DenseIndex
            dense = DenseIndex(assets, catalog_path)
            if set(dense.ids) != set(self.index.products):
                raise ValueError("dense IDs not identical to catalog")
            self.dense = dense
            self.dense_status = "ready"
        except Exception:
            # Missing/invalid assets never trigger downloads or invalid IDs.
            # ONNX has provider-specific exception classes; this boundary is
            # intentionally fail-closed for all optional initialization errors.
            pass

    def close(self) -> None:
        self.dense = None
        super().close()

    def search(self, request) -> RetrievalResult:
        baseline = super().search(request)
        if self.dense is None or not baseline.candidates:
            return baseline
        route = request.route_hint if request.route_hint in {"buying", "browsing"} else ("buying" if request.constraints else "browsing")
        try:
            dense_rows = self.dense.search(request.query, 30 if route == "browsing" else 15)
        except Exception:
            self.dense = None
            self.dense_status = "runtime_failure_lexical_fallback"
            return baseline
        # Unlike the old DualRoute experiment, a real semantic match may recover
        # an otherwise empty keyword search. If none, preserve exact fallback.
        if baseline.trace.fallback_used and (not dense_rows or dense_rows[0][1] < 0.25):
            return baseline
        category_rows = self.index.search(and_expression(terms(request.category or ""), column="categories"), 20, BASELINE_WEIGHTS)
        sources = []
        if not baseline.trace.fallback_used:
            sources.append(("keyword", [(item.parent_asin, item.retrieval_score) for item in baseline.candidates], 1.0))
        sources.extend((("category", [(key, -value) for key, value in category_rows], 0.2), ("dense", dense_rows, 0.7 if route == "browsing" else 0.35)))
        fused, evidence = defaultdict(float), defaultdict(list)
        for name, rows, weight in sources:
            for rank, (identifier, score) in enumerate(rows):
                fused[identifier] += weight / (60 + rank + 1)
                evidence[identifier].append(RouteEvidence(name, rank, score))
        identifiers = sorted(fused, key=lambda key: (-fused[key], key))[:request.limit]
        candidates = []
        for rank, identifier in enumerate(identifiers):
            product = self.index.products[identifier]
            candidates.append(Candidate(identifier, rank, fused[identifier], product.searchable_text, product.price, product.categories, tuple(evidence[identifier])))
        return RetrievalResult(tuple(candidates), RetrievalTrace(route, ("real_dense_rrf", self.dense_status), tuple(name for name, _, _ in sources), tuple((name, len(rows)) for name, rows, _ in sources), baseline.trace.query_terms, fallback_used=False))
