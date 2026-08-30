from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from solution.agent_impl import _BaselineBM25Index
from solution.contracts import RetrievalRequest as CoreRetrievalRequest
from solution.retrieval import (
    BaselineFTS5Retriever,
    DualRouteInMemoryRetriever,
    RetrievalConstraint,
    RetrievalRequest,
)


PRODUCTS = (
    {
        "parent_asin": "A1",
        "title": "Black Trail Running Shoes",
        "features": ["lightweight", "breathable mesh"],
        "description": ["outdoor athletic footwear"],
        "price": 49.0,
        "categories": ["Shoes", "Running"],
        "details": {"Department": "mens", "Color": "black"},
        "average_rating": 4.8,
        "rating_number": 100,
        "store": "Trail Co",
    },
    {
        "parent_asin": "A2",
        "title": "Blue Cotton Travel Shirt",
        "features": ["packable", "comfortable cotton"],
        "description": ["casual travel top"],
        "price": 29.0,
        "categories": ["Clothing", "Shirts"],
        "details": {"Department": "mens", "Material": "cotton"},
        "average_rating": 4.7,
        "rating_number": 80,
        "store": "Journey",
    },
    {
        "parent_asin": "A3",
        "title": "Formal Leather Office Shoes",
        "features": ["durable leather"],
        "description": ["professional work footwear"],
        "price": 89.0,
        "categories": ["Shoes", "Oxfords"],
        "details": {"Department": "mens", "Color": "brown"},
        "average_rating": 4.5,
        "rating_number": 60,
        "store": "Office Step",
    },
    {
        "parent_asin": "A4",
        "title": "Warm Winter Jacket",
        "features": ["thermal insulated coat"],
        "description": ["winter outerwear"],
        "price": 75.0,
        "categories": ["Clothing", "Jackets"],
        "details": {"Department": "womens"},
        "average_rating": 4.6,
        "rating_number": 90,
        "store": "North",
    },
)


class RetrieverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.catalog = Path(self.temporary.name) / "catalog.jsonl"
        self.catalog.write_text(
            "".join(json.dumps(product) + "\n" for product in PRODUCTS),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_baseline_wrapper_reproduces_existing_fts_order(self) -> None:
        old = _BaselineBM25Index(self.catalog)
        new = BaselineFTS5Retriever(self.catalog)
        try:
            for query in ("black running shoes", "cotton travel", "", "missing-token"):
                expected = old.search(CoreRetrievalRequest(query=query, limit=3))
                actual = new.search(RetrievalRequest(query=query, limit=3)).candidates
                self.assertEqual(
                    [candidate.parent_asin for candidate in expected],
                    [candidate.parent_asin for candidate in actual],
                )
                self.assertEqual(
                    [candidate.retrieval_score for candidate in expected],
                    [candidate.retrieval_score for candidate in actual],
                )
        finally:
            old.close()
            new.close()

    def test_buying_route_uses_distinct_routes_and_budget(self) -> None:
        baseline = BaselineFTS5Retriever(self.catalog)
        retriever = DualRouteInMemoryRetriever(self.catalog)
        request = RetrievalRequest(
            query="mens cotton shirt under 30",
            limit=4,
            category="mens shirts",
            constraints=(
                RetrievalConstraint("material", ("cotton",)),
                RetrievalConstraint("budget", ("under $30",)),
            ),
        )
        try:
            baseline_result = baseline.search(
                RetrievalRequest(query=request.query, limit=request.limit)
            )
            result = retriever.search(request)
            self.assertEqual("buying", result.trace.selected_path)
            self.assertIn("exact_constraints", result.trace.routes)
            self.assertIn("baseline_fts", result.trace.routes)
            self.assertIn("category_fields", result.trace.routes)
            self.assertEqual("A2", result.candidates[0].parent_asin)
            self.assertEqual(
                len(result.candidates),
                len({candidate.parent_asin for candidate in result.candidates}),
            )
            self.assertEqual(
                {candidate.parent_asin for candidate in baseline_result.candidates},
                {candidate.parent_asin for candidate in result.candidates},
            )
        finally:
            baseline.close()
            retriever.close()

    def test_browsing_route_expands_use_case_and_is_deterministic(self) -> None:
        request = RetrievalRequest(
            query="something for travel",
            limit=4,
            category="clothing",
            route_hint="browsing",
        )
        first = DualRouteInMemoryRetriever(self.catalog)
        second = DualRouteInMemoryRetriever(self.catalog)
        try:
            first_result = first.search(request)
            second_result = second.search(request)
            self.assertEqual("browsing", first_result.trace.selected_path)
            self.assertIn("packable", first_result.trace.expanded_terms)
            self.assertGreaterEqual(len(first_result.trace.routes), 3)
            self.assertEqual(
                [candidate.parent_asin for candidate in first_result.candidates],
                [candidate.parent_asin for candidate in second_result.candidates],
            )
        finally:
            first.close()
            second.close()

    def test_auto_route_treats_use_case_as_browsing_until_hard_constraint(self) -> None:
        retriever = DualRouteInMemoryRetriever(self.catalog)
        try:
            browsing = retriever.search(
                RetrievalRequest(
                    query="something for travel",
                    limit=4,
                    constraints=(RetrievalConstraint("use_case", ("travel",)),),
                )
            )
            buying = retriever.search(
                RetrievalRequest(
                    query="cotton shirt for travel",
                    limit=4,
                    constraints=(
                        RetrievalConstraint("use_case", ("travel",)),
                        RetrievalConstraint("material", ("cotton",)),
                    ),
                )
            )
            self.assertEqual("browsing", browsing.trace.selected_path)
            self.assertEqual(
                ("use_case_without_hard_constraint",), browsing.trace.reason_codes
            )
            self.assertEqual("buying", buying.trace.selected_path)
        finally:
            retriever.close()

    def test_empty_limit_does_not_query_or_fallback(self) -> None:
        retriever = DualRouteInMemoryRetriever(self.catalog)
        try:
            result = retriever.search(RetrievalRequest("shoes", 0))
            self.assertEqual((), result.candidates)
            self.assertEqual((), result.trace.routes)
            self.assertFalse(result.trace.fallback_used)
        finally:
            retriever.close()

    def test_unmatched_query_has_deterministic_popularity_fallback(self) -> None:
        retriever = DualRouteInMemoryRetriever(self.catalog)
        try:
            result = retriever.search(RetrievalRequest("zzzz-unmatched", 2))
            self.assertTrue(result.trace.fallback_used)
            self.assertEqual("popularity_fallback", result.trace.routes[0])
            self.assertEqual(["A1", "A4"], [item.parent_asin for item in result.candidates])
        finally:
            retriever.close()

    def test_candidate_unmatched_query_ignores_matching_category_for_fallback(self) -> None:
        baseline = BaselineFTS5Retriever(self.catalog)
        candidate = DualRouteInMemoryRetriever(self.catalog)
        request = RetrievalRequest(
            query="zzzz-unmatched",
            limit=3,
            category="Shoes",
            route_hint="browsing",
        )
        try:
            baseline_result = baseline.search(
                RetrievalRequest(query=request.query, limit=request.limit)
            )
            candidate_result = candidate.search(request)
            expected_ids = [item.parent_asin for item in baseline_result.candidates]

            self.assertEqual(["A1", "A4", "A2"], expected_ids)
            self.assertEqual(
                expected_ids,
                [item.parent_asin for item in candidate_result.candidates],
            )
            self.assertEqual(
                [item.retrieval_rank for item in baseline_result.candidates],
                [item.retrieval_rank for item in candidate_result.candidates],
            )
            self.assertTrue(candidate_result.trace.fallback_used)
            self.assertEqual(
                ("popularity_fallback",), candidate_result.trace.routes
            )
            self.assertEqual(
                (("popularity_fallback", 3),),
                candidate_result.trace.route_candidate_counts,
            )
            self.assertEqual(
                ("no_fts_match", "deterministic_popularity_fallback"),
                candidate_result.trace.reason_codes,
            )
        finally:
            baseline.close()
            candidate.close()

    def test_baseline_unmatched_query_exactly_uses_legacy_popularity_fallback(self) -> None:
        legacy = _BaselineBM25Index(self.catalog)
        retriever = BaselineFTS5Retriever(self.catalog)
        try:
            for query in ("", "zzzz-unmatched"):
                expected = legacy.search(CoreRetrievalRequest(query=query, limit=3))
                result = retriever.search(RetrievalRequest(query=query, limit=3))
                self.assertTrue(result.trace.fallback_used)
                self.assertEqual(("popularity_fallback",), result.trace.routes)
                self.assertEqual(
                    ("no_fts_match", "deterministic_popularity_fallback"),
                    result.trace.reason_codes,
                )
                self.assertEqual(
                    [item.parent_asin for item in expected],
                    [item.parent_asin for item in result.candidates],
                )
                self.assertEqual(
                    [item.retrieval_score for item in expected],
                    [item.retrieval_score for item in result.candidates],
                )
        finally:
            legacy.close()
            retriever.close()


if __name__ == "__main__":
    unittest.main()
