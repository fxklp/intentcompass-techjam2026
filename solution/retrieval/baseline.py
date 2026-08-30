from __future__ import annotations

from pathlib import Path

from solution.retrieval.contracts import Candidate, RetrievalRequest, RetrievalResult, RetrievalTrace
from solution.retrieval.index import FTS5CatalogIndex, or_expression, terms


BASELINE_WEIGHTS = (6.0, 4.0, 2.5, 2.5, 1.5, 1.0)


class BaselineFTS5Retriever:
    """Exact fallback wrapper for the FTS5 bridge in solution.agent_impl."""

    def __init__(self, catalog_path: str | Path) -> None:
        self.index = FTS5CatalogIndex(catalog_path)

    def close(self) -> None:
        self.index.close()

    def search(self, request: RetrievalRequest) -> RetrievalResult:
        limit = max(0, int(request.limit))
        query_terms = tuple(list(dict.fromkeys(terms(request.query)))[:40])
        rows = self.index.search(or_expression(query_terms), limit, BASELINE_WEIGHTS)
        fallback_used = not rows and limit > 0
        if fallback_used:
            rows = [(parent_asin, 0.0) for parent_asin in self.index.fallback_ids[:limit]]
        candidates = tuple(
            self._candidate(parent_asin, rank, score)
            for rank, (parent_asin, score) in enumerate(rows)
        )
        return RetrievalResult(
            candidates=candidates,
            trace=RetrievalTrace(
                selected_path="baseline",
                reason_codes=("compatibility_fallback",),
                routes=("baseline_fts",),
                route_candidate_counts=(("baseline_fts", len(candidates)),),
                query_terms=query_terms,
                fallback_used=fallback_used,
            ),
        )

    def _candidate(self, parent_asin: str, rank: int, score: float) -> Candidate:
        product = self.index.candidate_data(parent_asin)
        return Candidate(
            parent_asin=parent_asin,
            retrieval_rank=rank,
            retrieval_score=-float(score),
            searchable_text=product.searchable_text,
            price=product.price,
            categories=product.categories,
        )
