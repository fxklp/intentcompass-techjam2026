from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from solution.retrieval.baseline import BASELINE_WEIGHTS
from solution.retrieval.contracts import (
    Candidate,
    RetrievalRequest,
    RetrievalResult,
    RetrievalTrace,
    RouteEvidence,
)
from solution.retrieval.index import FTS5CatalogIndex, and_expression, or_expression, terms


BUYING_WEIGHTS = (8.0, 6.0, 5.0, 5.0, 3.0, 1.0)
CATEGORY_WEIGHTS = (5.0, 10.0, 1.0, 2.0, 2.0, 0.5)
USE_CASE_WEIGHTS = (4.0, 3.0, 7.0, 2.0, 1.0, 5.0)
RRF_K = 30.0

QUERY_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "casual": ("everyday", "comfortable"),
    "formal": ("dress", "business", "occasion"),
    "gym": ("workout", "training", "athletic"),
    "hiking": ("outdoor", "trail", "trekking"),
    "running": ("athletic", "jogging", "workout"),
    "travel": ("lightweight", "comfortable", "packable"),
    "wedding": ("formal", "ceremony", "occasion"),
    "winter": ("warm", "thermal", "insulated"),
    "work": ("office", "professional", "durable"),
    "shoes": ("footwear", "sneaker", "boot", "sandal"),
    "shirt": ("top", "tee", "blouse"),
    "jacket": ("coat", "outerwear"),
}


class DualRouteInMemoryRetriever:
    """Label-free Buying/Browsing retrieval over one in-memory FTS5 catalog."""

    def __init__(self, catalog_path: str | Path) -> None:
        self.index = FTS5CatalogIndex(catalog_path)

    def close(self) -> None:
        self.index.close()

    def search(self, request: RetrievalRequest) -> RetrievalResult:
        limit = max(0, int(request.limit))
        query_terms = tuple(list(dict.fromkeys(terms(request.query)))[:40])
        if limit == 0:
            return RetrievalResult(
                candidates=(),
                trace=RetrievalTrace(
                    selected_path=self._select_path(request)[0],
                    reason_codes=self._select_path(request)[1],
                    routes=(),
                    route_candidate_counts=(),
                    query_terms=query_terms,
                ),
            )

        selected_path, reasons = self._select_path(request)
        route_limit = max(80, limit * 2)
        if selected_path == "buying":
            routes, expansions = self._buying_routes(request, query_terms, route_limit)
            weights = {
                "exact_constraints": 1.35,
                "baseline_fts": 3.0,
                "category_fields": 0.8,
            }
        else:
            routes, expansions = self._browsing_routes(request, query_terms, route_limit)
            weights = {
                "category_fields": 1.1,
                "baseline_fts": 3.0,
                "expanded_fts": 0.85,
                "use_case_fields": 0.7,
            }

        nonempty = {name: rows for name, rows in routes.items() if rows}
        fallback_used = not nonempty
        if fallback_used:
            nonempty = {
                "popularity_fallback": [
                    (parent_asin, 0.0) for parent_asin in self.index.fallback_ids[:limit]
                ]
            }
            weights["popularity_fallback"] = 1.0

        candidates = self._fuse(
            nonempty,
            weights,
            limit,
            request,
            diversify=selected_path == "browsing",
            retained_ids={
                parent_asin
                for parent_asin, _ in nonempty.get("baseline_fts", ())[:limit]
            },
        )
        return RetrievalResult(
            candidates=tuple(candidates),
            trace=RetrievalTrace(
                selected_path=selected_path,
                reason_codes=reasons,
                routes=tuple(nonempty),
                route_candidate_counts=tuple(
                    (name, len(rows)) for name, rows in nonempty.items()
                ),
                query_terms=query_terms,
                expanded_terms=expansions,
                fallback_used=fallback_used,
            ),
        )

    @staticmethod
    def _select_path(request: RetrievalRequest) -> tuple[str, tuple[str, ...]]:
        if request.route_hint == "buying":
            return "buying", ("explicit_route_hint",)
        if request.route_hint == "browsing":
            return "browsing", ("explicit_route_hint",)
        constrained = tuple(
            constraint
            for constraint in request.constraints
            if constraint.values and constraint.attribute != "other"
        )
        if constrained:
            attributes = ",".join(sorted({item.attribute for item in constrained}))
            return "buying", ("structured_constraints_present", f"attributes:{attributes}")
        if request.category:
            return "browsing", ("category_without_hard_constraint",)
        return "browsing", ("open_ended_query",)

    def _buying_routes(
        self,
        request: RetrievalRequest,
        query_terms: tuple[str, ...],
        route_limit: int,
    ) -> tuple[dict[str, list[tuple[str, float]]], tuple[str, ...]]:
        constraint_terms = self._constraint_terms(request, exclude={"budget"})
        exact_terms = tuple(constraint_terms[:12])
        category_terms = self._category_terms(request)
        routes = {
            "exact_constraints": self.index.search(
                and_expression(exact_terms), route_limit, BUYING_WEIGHTS
            ),
            "baseline_fts": self.index.search(
                or_expression(query_terms), route_limit, BASELINE_WEIGHTS
            ),
            "category_fields": self.index.search(
                or_expression(category_terms, column="categories"),
                route_limit,
                CATEGORY_WEIGHTS,
            ),
        }
        return routes, ()

    def _browsing_routes(
        self,
        request: RetrievalRequest,
        query_terms: tuple[str, ...],
        route_limit: int,
    ) -> tuple[dict[str, list[tuple[str, float]]], tuple[str, ...]]:
        category_terms = self._category_terms(request) or query_terms
        use_case_terms = self._constraint_terms(request, include={"use_case"})
        expansions = self._expanded_terms((*query_terms, *use_case_terms))
        expanded_query = tuple(dict.fromkeys((*query_terms, *expansions)))[:60]
        routes = {
            "category_fields": self.index.search(
                or_expression(category_terms, column="categories"),
                route_limit,
                CATEGORY_WEIGHTS,
            ),
            "baseline_fts": self.index.search(
                or_expression(query_terms), route_limit, BASELINE_WEIGHTS
            ),
            "expanded_fts": self.index.search(
                or_expression(expanded_query), route_limit, USE_CASE_WEIGHTS
            ),
            "use_case_fields": self.index.search(
                and_expression(use_case_terms[:8]), route_limit, USE_CASE_WEIGHTS
            ),
        }
        return routes, expansions

    @staticmethod
    def _constraint_terms(
        request: RetrievalRequest,
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
    ) -> tuple[str, ...]:
        selected: list[str] = []
        for constraint in request.constraints:
            if include is not None and constraint.attribute not in include:
                continue
            if exclude is not None and constraint.attribute in exclude:
                continue
            for value in constraint.values:
                selected.extend(terms(value))
        return tuple(dict.fromkeys(selected))

    @staticmethod
    def _category_terms(request: RetrievalRequest) -> tuple[str, ...]:
        return tuple(dict.fromkeys(terms(request.category or "")))[:20]

    @staticmethod
    def _expanded_terms(values: tuple[str, ...]) -> tuple[str, ...]:
        expanded: list[str] = []
        for value in values:
            expanded.extend(QUERY_EXPANSIONS.get(value, ()))
        return tuple(dict.fromkeys(expanded))

    def _fuse(
        self,
        routes: dict[str, list[tuple[str, float]]],
        weights: dict[str, float],
        limit: int,
        request: RetrievalRequest,
        *,
        diversify: bool,
        retained_ids: set[str],
    ) -> list[Candidate]:
        fused_scores: defaultdict[str, float] = defaultdict(float)
        evidence: defaultdict[str, list[RouteEvidence]] = defaultdict(list)
        first_seen: dict[str, int] = {}
        seen_counter = 0
        for route_name, rows in routes.items():
            route_weight = weights.get(route_name, 1.0)
            for rank, (parent_asin, raw_score) in enumerate(rows):
                if parent_asin not in first_seen:
                    first_seen[parent_asin] = seen_counter
                    seen_counter += 1
                fused_scores[parent_asin] += route_weight / (RRF_K + rank + 1)
                evidence[parent_asin].append(
                    RouteEvidence(route=route_name, rank=rank, score=-float(raw_score))
                )

        budget = self._budget(request)
        for parent_asin in fused_scores:
            product = self.index.candidate_data(parent_asin)
            if budget is not None and product.price is not None:
                if product.price <= budget:
                    fused_scores[parent_asin] += 0.012
                else:
                    excess = min(2.0, (product.price - budget) / max(1.0, budget))
                    fused_scores[parent_asin] -= 0.012 * excess

        # The isolated experiment keeps every candidate from the proven FTS
        # fallback. Other routes can improve ordering without silently trading
        # away known recall at the fixed pool size.
        if retained_ids:
            fused_scores = defaultdict(
                float,
                {
                    parent_asin: score
                    for parent_asin, score in fused_scores.items()
                    if parent_asin in retained_ids
                },
            )

        ordered = sorted(
            fused_scores,
            key=lambda parent_asin: (
                -fused_scores[parent_asin],
                first_seen[parent_asin],
                parent_asin,
            ),
        )
        if diversify:
            ordered = self._diversify(ordered, fused_scores)
        result: list[Candidate] = []
        for rank, parent_asin in enumerate(ordered[:limit]):
            product = self.index.candidate_data(parent_asin)
            result.append(
                Candidate(
                    parent_asin=parent_asin,
                    retrieval_rank=rank,
                    retrieval_score=fused_scores[parent_asin],
                    searchable_text=product.searchable_text,
                    price=product.price,
                    categories=product.categories,
                    evidence=tuple(evidence[parent_asin]),
                )
            )
        return result

    def _diversify(
        self,
        ordered: list[str],
        scores: dict[str, float],
    ) -> list[str]:
        """Small deterministic novelty bonus, without hard category quotas."""
        selected: list[str] = []
        remaining = ordered.copy()
        category_counts: defaultdict[str, int] = defaultdict(int)
        window = min(80, len(remaining))
        while remaining and len(selected) < window:
            best = min(
                remaining,
                key=lambda parent_asin: (
                    -(
                        scores[parent_asin]
                        + 0.004 / (1 + category_counts[self._leaf_category(parent_asin)])
                    ),
                    ordered.index(parent_asin),
                    parent_asin,
                ),
            )
            remaining.remove(best)
            selected.append(best)
            category_counts[self._leaf_category(best)] += 1
        return [*selected, *remaining]

    def _leaf_category(self, parent_asin: str) -> str:
        categories = self.index.candidate_data(parent_asin).categories
        return categories[-1].lower() if categories else ""

    @staticmethod
    def _budget(request: RetrievalRequest) -> float | None:
        for constraint in request.constraints:
            if constraint.attribute != "budget":
                continue
            for value in constraint.values:
                match = re.search(
                    r"(?:\$|\bunder\s+|\bless\s+than\s+|\baround\s+\$?)\s*(\d+(?:\.\d+)?)",
                    value,
                    re.IGNORECASE,
                )
                if match:
                    return float(match.group(1))
        return None
