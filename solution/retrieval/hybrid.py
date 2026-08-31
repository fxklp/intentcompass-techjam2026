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
        # The lexical channel is the precision anchor established by RC3.
        # Category and dense evidence are bounded tie-breakers: they can recover
        # and reorder candidates, but cannot swamp an exact multi-token match.
        # Browsing deliberately gives semantic/diversity evidence twice the
        # influence used by the exact-condition Buying route.
        keyword_weight, category_weight, dense_weight = (
            (1.0, 0.005, 0.010) if route == "buying" else (1.0, 0.010, 0.020)
        )
        if not baseline.trace.fallback_used:
            sources.append(("keyword", [(item.parent_asin, item.retrieval_score) for item in baseline.candidates], keyword_weight))
        sources.extend((("category", [(key, -value) for key, value in category_rows], category_weight), ("dense", dense_rows, dense_weight)))
        fused, evidence = defaultdict(float), defaultdict(list)
        for name, rows, weight in sources:
            for rank, (identifier, score) in enumerate(rows):
                fused[identifier] += weight / (60 + rank + 1)
                evidence[identifier].append(RouteEvidence(name, rank, score))
        identifiers = sorted(fused, key=lambda key: (-fused[key], key))
        if not baseline.trace.fallback_used:
            # Preserve the proven lexical precision head.  Independent dense
            # and category recall still fuse into the decision tail and can
            # recover candidates outside the lexical channel.
            lexical_head = [item.parent_asin for item in baseline.candidates[:8]]
            identifiers = [*lexical_head, *(key for key in identifiers if key not in set(lexical_head))]
        if route == "browsing":
            identifiers = self._diversify(identifiers[:max(request.limit * 3, 30)], fused)
        identifiers = identifiers[:request.limit]
        candidates = []
        for rank, identifier in enumerate(identifiers):
            product = self.index.products[identifier]
            candidates.append(Candidate(identifier, rank, fused[identifier], product.searchable_text, product.price, product.categories, tuple(evidence[identifier])))
        return RetrievalResult(tuple(candidates), RetrievalTrace(route, ("real_dense_rrf", "bounded_vector_diversity" if route == "browsing" else "exact_intent_weights", self.dense_status), tuple(name for name, _, _ in sources), tuple((name, len(rows)) for name, rows, _ in sources), baseline.trace.query_terms, fallback_used=False))

    def _diversify(self, ordered: list[str], scores: dict[str, float]) -> list[str]:
        """Deterministic, bounded MMR over real vectors and leaf categories."""
        if not ordered:
            return []
        tail = ordered[30:]
        ordered = ordered[:30]
        # Preserve the highest-confidence lexical head, then diversify the
        # remainder.  This keeps exact category matches stable while making
        # browsing results measurably less redundant.
        stable_head = 8 if len(ordered) >= 10 else 1
        selected: list[str] = list(ordered[:stable_head])
        remaining = list(ordered[stable_head:])
        original_rank = {identifier: rank for rank, identifier in enumerate(ordered)}
        while remaining:
            def key(identifier: str) -> tuple[float, int, str]:
                product = self.index.products[identifier]
                leaf = product.categories[-1].casefold() if product.categories else ""
                same_category = sum(
                    bool(leaf) and leaf == (
                        self.index.products[chosen].categories[-1].casefold()
                        if self.index.products[chosen].categories else ""
                    )
                    for chosen in selected
                )
                similarities: list[float] = []
                for chosen in selected:
                    try:
                        value = float(self.dense.similarity(identifier, chosen))
                    except (AttributeError, TypeError, ValueError):
                        value = 0.0
                    similarities.append(value)
                similarity = max(similarities, default=0.0)
                novelty_score = scores[identifier] - 0.00035 * same_category - 0.00035 * max(0.0, similarity)
                return (-novelty_score, original_rank[identifier], identifier)
            chosen = min(remaining, key=key)
            remaining.remove(chosen)
            selected.append(chosen)
        return [*selected, *tail]
