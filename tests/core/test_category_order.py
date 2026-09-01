from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from solution.category_order import CategoryHeadOrder
from solution.field_evidence import FieldEvidence
from solution.retrieval.baseline import BaselineFTS5Retriever
from starter.agent import Agent


class CategoryOrderTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "catalog.jsonl"
        products = [{"parent_asin": "WALLET", "title": "leather wallet", "categories": ["Wallets"], "rating_number": 100},
                    {"parent_asin": "SHOE", "title": "leather shoes", "categories": ["Shoes"], "features": ["leather"]}]
        self.path.write_text(''.join(json.dumps(p) + '\n' for p in products), encoding="utf-8")
        self.retriever = BaselineFTS5Retriever(self.path)
        self.addCleanup(self.retriever.close)
        self.order = CategoryHeadOrder(self.retriever.index)
        self.items = [self.retriever._candidate("WALLET", 0, 1), self.retriever._candidate("SHOE", 1, 1)]

    def test_matching_category_moves_first_without_changing_membership(self):
        result = self.order.reorder(self.items, "shoes")
        self.assertEqual([c.parent_asin for c in result], ["SHOE", "WALLET"])
        self.assertEqual(set(result), set(self.items))
        self.assertEqual(self.retriever.index.query_cache.capacity, 512)

    def test_unknown_empty_and_no_match_preserve_order(self):
        for category in (None, "", "unseen category"):
            self.assertEqual(self.order.reorder(self.items, category), self.items)
        self.assertEqual(self.order.reorder([], "shoes"), [])
        self.assertEqual(self.order.reorder(self.items, "shoes", fallback=True), self.items)

    def test_top10_membership_and_tail_are_unchanged(self):
        head = []
        for i in range(10):
            pid = f"fixture-{i}"
            self.retriever.index.products[pid] = replace(self.retriever.index.products["WALLET"], parent_asin=pid)
            head.append(replace(self.items[0], parent_asin=pid, retrieval_rank=i))
        self.assertEqual(self.order.reorder([*head, self.items[1]], "shoes"), [*head, self.items[1]])

    def test_category_override_does_not_reuse_previous_request(self):
        self.assertEqual(self.order.reorder(self.items, "shoes")[0].parent_asin, "SHOE")
        self.assertEqual(self.order.reorder(self.items, "wallets")[0].parent_asin, "WALLET")

    def test_requested_field_survives_lru_eviction(self):
        fields = FieldEvidence(self.retriever.index.connection)
        self.addCleanup(fields.close)
        expected = fields.get(["SHOE"])["SHOE"]
        for i in range(255):
            fields.cache[f"irrelevant-{i}"] = "unused"
        self.assertEqual(fields.get(["WALLET", "SHOE"])["SHOE"], expected)
        self.assertLessEqual(len(fields.cache), 256)

    def test_default_on_off_control_reset_and_zero_tokens(self):
        clean = {k: v for k, v in os.environ.items() if not k.startswith("INTENTCOMPASS_")}
        with patch.dict(os.environ, clean, clear=True):
            agent = Agent(self.path)
            try:
                self.assertIsNotNone(agent._core._adaptive.category_order)
                agent.reset("one", {})
                first = agent.respond("one", "I'm looking for shoes. leather", 1, 10)
                agent.reset("one", {})
                self.assertEqual(first, agent.respond("one", "I'm looking for shoes. leather", 1, 10))
                self.assertEqual(first["usage"], {"prompt_tokens": 0, "completion_tokens": 0})
                self.assertEqual(agent.respond("one", "no preference", 2, 0)["recommendations"], [])
            finally:
                agent.close()
            os.environ["INTENTCOMPASS_CATEGORY_ORDER"] = "off"
            agent = Agent(self.path)
            try:
                self.assertIsNone(agent._core._adaptive.category_order)
                self.assertEqual(agent._core._adaptive.retriever.index.query_cache.capacity, 128)
            finally:
                agent.close()
