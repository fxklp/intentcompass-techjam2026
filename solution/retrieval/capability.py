"""Capability-complete, target-blind retrieval with conservative Top-10 safety."""
from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path

from solution.constraint_semantics import contradicts_exclusion, excluded_term, upper_budget
from solution.retrieval.baseline import BaselineFTS5Retriever
from solution.retrieval.contracts import Candidate, RetrievalRequest, RetrievalResult, RetrievalTrace, RouteEvidence
from solution.retrieval.dual_route import BUYING_WEIGHTS, CATEGORY_WEIGHTS, USE_CASE_WEIGHTS, QUERY_EXPANSIONS
from solution.retrieval.index import and_expression, or_expression, terms


BROAD_RE = re.compile(r"^(?:something|anything|show me options|surprise me|i(?:'m| am) not sure)[.! ]*$", re.I)


class CapabilityRetriever(BaselineFTS5Retriever):
    """Real multi-route retrieval with demand-driven in-memory dense inference."""

    def __init__(self, catalog_path: str | Path, assets: Path) -> None:
        super().__init__(catalog_path)
        self.dense = None
        self.dense_status = "unavailable_lexical_fallback"
        try:
            from solution.retrieval.dense import DenseIndex
            dense = DenseIndex(assets, Path(catalog_path))
            if set(dense.ids) != set(self.index.products):
                raise ValueError("dense IDs differ from catalog")
            self.dense = dense
            self.dense_status = "ready"
        except Exception:
            pass

    def close(self) -> None:
        self.dense = None
        super().close()

    @staticmethod
    def _route(request: RetrievalRequest) -> str:
        if request.route_hint in {"buying", "browsing"}:
            return request.route_hint
        return "buying" if request.constraints else "browsing"

    @staticmethod
    def _broad(request: RetrievalRequest) -> bool:
        return not request.category and not request.constraints and (
            bool(BROAD_RE.fullmatch(" ".join(request.query.split()))) or not terms(request.query)
        )

    def _cutoff(self, request: RetrievalRequest, route: str) -> RetrievalResult:
        rows = self.index.fallback_ids[:max(0, request.limit)]
        candidates = tuple(self._candidate(identifier, rank, 0.0) for rank, identifier in enumerate(rows))
        return RetrievalResult(candidates, RetrievalTrace(
            route, ("early_overgenerality_cutoff", "expensive_retrieval_skipped"),
            ("clarification_cutoff",), (("clarification_cutoff", len(rows)),),
            tuple(terms(request.query)), fallback_used=True,
        ))

    @staticmethod
    def _constraint_state(product, constraints: tuple) -> str:
        """Three-valued check: conflict wins; absent metadata stays unknown."""
        observed = set(terms(product.searchable_text))
        states = []
        for constraint in constraints:
            values = tuple(value for value in constraint.values if value.strip())
            if not values:
                continue
            if constraint.attribute == "budget":
                cap = upper_budget(values)
                if cap is None or product.price is None:
                    states.append("unknown")
                else:
                    states.append("satisfied" if product.price <= cap else "conflict")
                continue
            negatives = tuple(term for value in values if (term := excluded_term(value)))
            if negatives:
                states.append("conflict" if any(
                    contradicts_exclusion(product.searchable_text, term) for term in negatives
                ) else "unknown")
                continue
            wanted = set(token for value in values for token in terms(value))
            if wanted and wanted <= observed:
                states.append("satisfied")
                continue
            # A parent product can represent unlisted SKU variants. Another
            # observed colour/material is therefore not proof of conflict.
            states.append("unknown")
        if "conflict" in states:
            return "conflict"
        return "satisfied" if states and all(state == "satisfied" for state in states) else "unknown"

    def _apply_buying_constraints(self, identifiers: list[str], request: RetrievalRequest) -> tuple[list[str], tuple[str, ...]]:
        groups = {state: [] for state in ("satisfied", "unknown", "conflict")}
        states = {}
        for identifier in identifiers:
            state = self._constraint_state(self.index.products[identifier], request.constraints)
            states[identifier] = state
            groups[state].append(identifier)
        # Satisfaction is evidence, not permission to disturb the proven
        # relevance order. Only a known conflict can be filtered/demoted.
        eligible = [identifier for identifier in identifiers if states[identifier] != "conflict"]
        relaxed = len(eligible) < request.limit and bool(groups["conflict"])
        ordered = [*eligible, *(groups["conflict"] if relaxed else [])]
        reasons = (
            f"constraints_satisfied:{len(groups['satisfied'])}",
            f"constraints_unknown:{len(groups['unknown'])}",
            f"constraints_conflict:{len(groups['conflict'])}",
            "explicit_constraint_relaxation_for_result_fill" if relaxed else
            "known_conflicts_filtered" if groups["conflict"] else "no_known_constraint_conflict",
        )
        return ordered, reasons

    def _diversify(self, identifiers: list[str], limit: int) -> list[str]:
        """Bound category repetition on exploratory paths, then deterministically fill."""
        selected, deferred, counts = [], [], defaultdict(int)
        for identifier in identifiers:
            categories = self.index.products[identifier].categories
            signature = categories[-1].casefold() if categories else "uncategorized"
            if counts[signature] < 2:
                selected.append(identifier)
                counts[signature] += 1
            else:
                deferred.append(identifier)
        return [*selected, *deferred][:limit]

    def search(self, request: RetrievalRequest) -> RetrievalResult:
        route = self._route(request)
        if self._broad(request):
            return self._cutoff(request, route)
        baseline = super().search(request)
        if request.limit <= 0:
            return RetrievalResult((), RetrievalTrace(route, ("zero_limit",), (), (), tuple(terms(request.query))))

        routes: dict[str, list[tuple[str, float]]] = {
            "keyword": [(c.parent_asin, c.retrieval_score) for c in baseline.candidates]
        }
        category_terms = tuple(dict.fromkeys(terms(request.category or "")))[:20]
        if category_terms:
            routes["category"] = self.index.search(
                or_expression(category_terms, column="categories"), max(request.limit, 40), CATEGORY_WEIGHTS,
            )
        constraint_terms = tuple(dict.fromkeys(
            token for item in request.constraints if item.attribute != "budget"
            for value in item.values for token in terms(value)
        ))[:16]
        if route == "buying" and constraint_terms:
            routes["exact_constraints"] = self.index.search(
                and_expression(constraint_terms), max(request.limit, 40), BUYING_WEIGHTS,
            )
        expanded = ()
        if route == "browsing":
            expanded = tuple(dict.fromkeys(
                extra for token in terms(request.query) for extra in QUERY_EXPANSIONS.get(token, ())
            ))
            if expanded:
                routes["expanded"] = self.index.search(
                    or_expression(tuple(dict.fromkeys((*terms(request.query), *expanded)))),
                    max(request.limit, 40), USE_CASE_WEIGHTS,
                )

        exploratory = bool(re.search(r"\b(?:surprise|unexpected|inspire|inspiration)\b", request.query, re.I))
        dense_trigger = route == "browsing" and self.dense is not None and (
            baseline.trace.fallback_used
            or exploratory
            or os.environ.get("INTENTCOMPASS_FORCE_SEMANTIC") == "1"
        )
        if dense_trigger:
            try:
                routes["dense"] = self.dense.search(request.query, 30)
            except Exception:
                self.dense = None
                self.dense_status = "runtime_failure_lexical_fallback"

        if baseline.trace.fallback_used:
            dense_rows = routes.get("dense", [])
            if not dense_rows or dense_rows[0][1] < .25:
                return RetrievalResult(baseline.candidates, RetrievalTrace(
                    route, ("no_fts_match", "deterministic_popularity_fallback"),
                    ("popularity_fallback",), (("popularity_fallback", len(baseline.candidates)),),
                    baseline.trace.query_terms, expanded, True,
                ))

        scores: defaultdict[str, float] = defaultdict(float)
        evidence: defaultdict[str, list[RouteEvidence]] = defaultdict(list)
        weights = {"keyword": 1.0, "category": .15, "exact_constraints": .25, "expanded": .10, "dense": .35}
        baseline_ids = {c.parent_asin for c in baseline.candidates}
        for name, rows in routes.items():
            for rank, (identifier, raw) in enumerate(rows):
                scores[identifier] += weights[name] / (60 + rank + 1)
                evidence[identifier].append(RouteEvidence(name, rank, float(raw)))

        if baseline.trace.fallback_used and routes.get("dense"):
            identifiers = [identifier for identifier, _ in routes["dense"][:request.limit]]
            reason = ("dense_recovered_lexical_miss", "semantic_candidate")
        elif exploratory and routes.get("dense"):
            original = [c.parent_asin for c in baseline.candidates]
            union = set(original) | {identifier for identifier, _ in routes["dense"]}
            identifiers = sorted(union, key=lambda i: (-scores[i], original.index(i) if i in baseline_ids else len(original), i))[:request.limit]
            identifiers = self._diversify(identifiers, request.limit)
            reason = ("true_browsing_route", "multi_route_dense_fusion", "bounded_category_diversity", "semantic_candidate")
        else:
            original = [c.parent_asin for c in baseline.candidates]
            route_only = sorted(
                (identifier for identifier in scores if identifier not in baseline_ids),
                key=lambda identifier: (-scores[identifier], identifier),
            )
            identifiers = original
            reason = (
                "true_buying_route" if route == "buying" else "true_browsing_route",
                "independent_routes_preserve_proven_head",
                f"route_only_candidates:{len(route_only)}",
            )

        if route == "buying" and request.constraints:
            identifiers, constraint_reasons = self._apply_buying_constraints(identifiers, request)
            reason = (*reason, *constraint_reasons)

        candidates = []
        original_by_id = {c.parent_asin: c for c in baseline.candidates}
        for rank, identifier in enumerate(identifiers[:request.limit]):
            product = self.index.candidate_data(identifier)
            score = scores[identifier]
            if not exploratory and identifier in original_by_id:
                score = original_by_id[identifier].retrieval_score
            candidates.append(Candidate(
                identifier, rank, score, product.searchable_text,
                product.price, product.categories, tuple(evidence[identifier]),
            ))
        nonempty = tuple(name for name, rows in routes.items() if rows)
        return RetrievalResult(tuple(candidates), RetrievalTrace(
            route, reason, nonempty,
            tuple((name, len(rows)) for name, rows in routes.items() if rows),
            baseline.trace.query_terms, expanded, False,
        ))
