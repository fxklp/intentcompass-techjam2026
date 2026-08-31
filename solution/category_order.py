"""Stable category evidence within the existing Top10, never target labels."""
from __future__ import annotations

from solution.contracts import Candidate
from solution.retrieval.index import FTS5CatalogIndex, terms


class CategoryHeadOrder:
    def __init__(self, index: FTS5CatalogIndex) -> None:
        self.index = index
        # Only static query results are cached, never conversation or answers.
        self.index.query_cache.capacity = 512

    def reorder(self, candidates: list[Candidate], category: str | None,
                *, fallback: bool = False) -> list[Candidate]:
        if fallback:
            return candidates
        wanted = set(terms(category or ""))

        def key(candidate: Candidate) -> float:
            categories = self.index.products[candidate.parent_asin].categories
            observed = set(terms(" ".join(categories)))
            return -len(wanted & observed) / len(wanted) if wanted else 0.0

        # Python's stable sort preserves all ties and the original tail.
        # This cannot add, remove or promote a product outside the original 10.
        return [*sorted(candidates[:10], key=key), *candidates[10:]]
