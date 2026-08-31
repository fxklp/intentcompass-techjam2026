from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from solution.api_budget import BudgetLedger, BudgetUnavailable, CAP_MICRO_RMB
from solution.chat_reranker import BudgetedChatReranker, chat_payload, cost_micro_rmb
from solution.contracts import Candidate
from solution.retrieval.query_cache import QueryCache


POOL = [Candidate("A", 0, 1, "red shoes", 40), Candidate("B", 1, .5, "blue shoes", 50)]


class BudgetTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "budget.sqlite3"
        BudgetLedger.initialize(self.path)
        self.ledger = BudgetLedger(self.path)

    def test_missing_or_existing_ledger_cannot_reset_cap(self):
        with self.assertRaises(BudgetUnavailable):
            BudgetLedger(self.path.with_name("missing"))
        with self.assertRaises(FileExistsError):
            BudgetLedger.initialize(self.path)

    def test_budget_shared_between_models_and_instances(self):
        self.ledger.reserve("qwen", CAP_MICRO_RMB-1)
        other = BudgetLedger(self.path)
        with self.assertRaises(BudgetUnavailable):
            other.reserve("deepseek", 2)
        other.reserve("deepseek", 1)
        self.assertEqual(other.summary()["conservative_cost_rmb"], 100)

    def test_unknown_usage_retains_reservation(self):
        self.ledger.reserve("a", 2_000_000)
        self.assertEqual(BudgetLedger(self.path).summary()["conservative_cost_rmb"], 2)
        self.assertEqual(self.ledger.summary()["groups"][0]["status"], "reserved")

    def test_settle_and_double_settlement(self):
        identifier = self.ledger.reserve("a", 100)
        self.ledger.settle(identifier, 20, 10, 10)
        self.assertEqual(self.ledger.summary()["conservative_cost_rmb"], .00002)
        with self.assertRaises(BudgetUnavailable):
            self.ledger.settle(identifier, 0, 0, 0)

    def test_over_reservation_blocks_future_calls(self):
        identifier = self.ledger.reserve("a", 100)
        with self.assertRaises(BudgetUnavailable):
            self.ledger.settle(identifier, 101, 100, 1)
        self.assertTrue(self.ledger.summary()["blocked"])
        with self.assertRaises(BudgetUnavailable):
            self.ledger.reserve("b", 1)

    def test_concurrent_reservations_cannot_overspend(self):
        def reserve(_):
            try:
                BudgetLedger(self.path).reserve("a", 30_000_000)
                return True
            except BudgetUnavailable:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve, range(8))), 3)
        self.assertEqual(self.ledger.summary()["conservative_cost_rmb"], 90)

    def test_invalid_policy_fails_closed(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE policy SET cap=200000000")
        with self.assertRaises(BudgetUnavailable):
            self.ledger.reserve("a", 1)


class ChatTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "budget.sqlite3"
        BudgetLedger.initialize(self.path)
        environment = patch.dict(os.environ, {"INTENTCOMPASS_SEMANTIC": "qwen", "INTENTCOMPASS_LLM_ALLOW_NETWORK": "1", "INTENTCOMPASS_LLM_MODEL": "qwen3.8-flash", "INTENTCOMPASS_QWEN_REGION": "beijing", "DASHSCOPE_API_KEY": "test-only", "INTENTCOMPASS_BUDGET_LEDGER": str(self.path)})
        environment.start()
        self.addCleanup(environment.stop)

    def response(self, ids=None):
        return {"finish_reason": "stop", "content": json.dumps({"ordered_ids": ids or ["B", "A"]}), "usage": {"prompt_tokens": 200, "completion_tokens": 50}}

    def test_actual_usage_settled_and_exact_order(self):
        with patch("solution.chat_reranker.chat_post", return_value=self.response()):
            result = BudgetedChatReranker().rerank(POOL, {})
        self.assertEqual([item.parent_asin for item in result.candidates], ["B", "A"])
        self.assertEqual(result.usage, {"prompt_tokens": 200, "completion_tokens": 50})
        self.assertEqual(BudgetLedger(self.path).summary()["conservative_cost_rmb"], .00035)

    def test_invalid_ids_fall_back_but_keep_charge(self):
        with patch("solution.chat_reranker.chat_post", return_value=self.response(["A", "FOREIGN"])):
            result = BudgetedChatReranker().rerank(POOL, {})
        self.assertEqual(result.candidates, POOL)
        self.assertEqual(result.reason, "model_failed_offline_fallback")
        self.assertGreater(BudgetLedger(self.path).summary()["conservative_cost_rmb"], 0)

    def test_timeout_unknown_usage_no_retry(self):
        ranker = BudgetedChatReranker()
        with patch("solution.chat_reranker.chat_post", side_effect=TimeoutError) as transport:
            result = ranker.rerank(POOL, {})
            ranker.rerank(POOL, {})
        self.assertIsNone(result.usage)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(BudgetLedger(self.path).summary()["groups"][0]["status"], "reserved")

    def test_no_opt_in_key_region_ledger_or_budget_no_network(self):
        for env in ({"INTENTCOMPASS_LLM_ALLOW_NETWORK":"0"}, {"DASHSCOPE_API_KEY":""}, {"INTENTCOMPASS_QWEN_REGION":"singapore"}, {"INTENTCOMPASS_BUDGET_LEDGER":""}, {"INTENTCOMPASS_LLM_MODEL":"unpriced"}):
            with self.subTest(env=env), patch.dict(os.environ, env), patch("solution.chat_reranker.chat_post") as transport:
                result = BudgetedChatReranker().rerank(POOL, {})
                self.assertFalse(result.attempted)
                transport.assert_not_called()
        BudgetLedger(self.path).reserve("other", CAP_MICRO_RMB)
        with patch("solution.chat_reranker.chat_post") as transport:
            self.assertFalse(BudgetedChatReranker().rerank(POOL, {}).attempted)
            transport.assert_not_called()

    def test_provider_payloads_disable_thinking_and_bound_output(self):
        qwen = chat_payload("qwen3.8-flash", {"secret":"never-export"}, POOL)
        deepseek = chat_payload("deepseek-v4-flash", {}, POOL)
        self.assertFalse(qwen["enable_thinking"])
        self.assertEqual(deepseek["thinking"], {"type":"disabled"})
        self.assertEqual(qwen["max_tokens"], 1024)
        self.assertNotIn("never-export", json.dumps(qwen))
        self.assertEqual(cost_micro_rmb("deepseek-v4-flash", 1_000_000, 1_000_000), 12_000_000)


class CacheTest(unittest.TestCase):
    def test_bounded_catalog_cache_not_mutable_by_caller(self):
        cache = QueryCache(2)
        compute = Mock(return_value=[("A", 1)])
        first = cache.get(("shoes", 10), compute)
        first.clear()
        self.assertEqual(cache.get(("shoes", 10), compute), [("A", 1)])
        self.assertEqual(compute.call_count, 1)
        cache.get(("bags", 10), compute)
        cache.get(("shirts", 10), compute)
        self.assertEqual(len(cache.rows), 2)
        self.assertNotIn(("shoes", 10), cache.rows)
        cache.clear()
        self.assertEqual(len(cache.rows), 0)


class IntegratedContractTest(unittest.TestCase):
    def setUp(self):
        from tests.core.test_agent import CATALOG
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "catalog.jsonl"
        self.path.write_text("".join(json.dumps(item)+"\n" for item in CATALOG), encoding="utf-8", newline="\n")
        env = patch.dict(os.environ, {"INTENTCOMPASS_AGENT_MODE":"integrated", "INTENTCOMPASS_RETRIEVAL":"baseline", "INTENTCOMPASS_SEMANTIC":"off", "INTENTCOMPASS_LLM_ALLOW_NETWORK":"0"})
        env.start()
        self.addCleanup(env.stop)
        from starter.agent import Agent
        self.agent = Agent(self.path)
        self.addCleanup(self.agent.close)

    def test_profile_evolves_without_leaking_or_resurrecting_overrides(self):
        self.agent.reset("a", {"preference_tags":["red","cotton"]})
        self.agent.respond("a", "I'm looking for shoes. A key requirement is: blue.", 1, 10)
        memory = self.agent._core._adaptive.sessions["a"].memory
        self.assertIn("blue", memory.export_profile()["preference_tags"])
        self.assertNotIn("red", memory.export_profile()["preference_tags"])
        self.agent.respond("a", "Actually, ignore my earlier preference. What I need is: leather.", 2, 10)
        self.assertEqual(memory.export_profile()["preference_tags"], ["leather"])
        self.agent.respond("a", "I have no preference for material.", 3, 10)
        self.assertEqual(memory.export_profile()["preference_tags"], [])
        self.agent.reset("a", {})
        self.assertEqual(self.agent._core._adaptive.sessions["a"].memory.export_profile(), {"preference_tags":[]})

    def test_plain_numeric_budget_not_size(self):
        from solution.state import SessionState
        state = SessionState.create("a", {})
        state.mark_asked("budget")
        state.apply_user_message("50", 2, flexible=True)
        self.assertEqual(state.preferences["budget"].values, ("around $50",))
        self.assertNotIn("size", state.preferences)

    def test_turn_guard_and_no_clarification_after_turn_ten(self):
        self.agent.reset("a", {})
        for turn in (0,11):
            with self.assertRaises(ValueError):
                self.agent.respond("a", "shoes", turn, 10)
        self.assertIsNone(self.agent.respond("a", "I'm looking for shoes.", 10, 10)["ask_attribute"])

    def test_stable_questions_and_real_api_usage_through_adapter(self):
        from solution.semantic import SemanticResult
        from scripts.model_probe import ProbeAgent
        probe = ProbeAgent(self.path)
        self.addCleanup(probe.agent.close)
        probe.reset("a", {})
        with patch.object(probe.agent._core._adaptive.semantic, "rerank", side_effect=lambda pool, context: SemanticResult(pool,"model_ranked",{"prompt_tokens":20,"completion_tokens":5}, True)):
            payload = probe.respond("a", "I'm looking for shoes.", 1, 10)
        self.assertEqual(payload["ask_attribute"], "feature")
        self.assertEqual(payload["usage"], {"prompt_tokens":20,"completion_tokens":5})
        self.assertEqual(probe.semantic_reasons["model_ranked"], 1)


if __name__ == "__main__":
    unittest.main()
