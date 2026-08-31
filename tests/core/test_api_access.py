from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solution.api_budget import BudgetLedger, BudgetUnavailable
from solution.api_transport import endpoint_for
from solution.chat_reranker import BudgetedChatReranker, chat_payload, cost_micro_rmb, validate_index_order
from scripts.api_credentials import load_credentials
from tests.core.test_final import POOL


class AccountLimitsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "budget.sqlite3"
        BudgetLedger.initialize(self.path)
        self.ledger = BudgetLedger(self.path)

    def test_restriction_retains_charges_and_provider_limits(self):
        reservation = self.ledger.reserve("qwen3.8-flash", 1_000_000)
        self.ledger.settle(reservation, 100, 10, 10)
        self.ledger.restrict(43_970_000, {"qwen": 20_000_000, "deepseek": 23_970_000})
        self.assertEqual(self.ledger.summary()["conservative_cost_rmb"], .0001)
        self.assertEqual(self.ledger.summary()["cap_rmb"], 43.97)
        with self.assertRaises(BudgetUnavailable):
            self.ledger.reserve("qwen3.7-flash", 20_000_000)
        self.ledger.reserve("deepseek-v4-flash", 23_970_000)
        with self.assertRaises(BudgetUnavailable):
            self.ledger.reserve("deepseek-v4-pro", 1)
        with self.assertRaises(BudgetUnavailable):
            self.ledger.reserve("unpriced", 1)

    def test_restriction_cannot_raise_reset_or_erase_spend(self):
        self.ledger.restrict(30_000_000, {"qwen": 10_000_000, "deepseek": 20_000_000})
        self.ledger.reserve("qwen3.8-flash", 100)
        for cap, limits in [(31_000_000, {"qwen":10_000_000,"deepseek":20_000_000}), (30_000_000, {"qwen":11_000_000,"deepseek":19_000_000}), (30_000_000, {"qwen":99,"deepseek":20_000_000})]:
            with self.assertRaises(BudgetUnavailable):
                self.ledger.restrict(cap, limits)
        self.assertEqual(self.ledger.summary()["provider_caps_rmb"], {"qwen":10,"deepseek":20})
        self.assertEqual(self.ledger.summary()["conservative_cost_rmb"], .0001)


class RegionalApiTest(unittest.TestCase):
    def test_pricing_tiers_use_decimal_k_not_binary_kib(self):
        self.assertEqual(cost_micro_rmb("qwen3.7-flash", 32000, 0, "singapore"), 7200)
        self.assertEqual(cost_micro_rmb("qwen3.7-flash", 32001, 0, "singapore"), 23969)
        self.assertEqual(cost_micro_rmb("qwen3.7-flash", 256000, 0, "singapore"), 191744)
        self.assertEqual(cost_micro_rmb("qwen3.7-flash", 256001, 0, "singapore"), 383746)
        self.assertEqual(cost_micro_rmb("qwen3.7-flash", 32001, 0), 19201)

    def test_indices_map_exactly_and_never_repair_missing_or_foreign_items(self):
        self.assertEqual(validate_index_order({"ordered_indices":[1,0]}, POOL), list(reversed(POOL)))
        for indices in ([0], [0,0], [0,2], [-1,0], [0,True], ["0","1"], [0,1,2]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                validate_index_order({"ordered_indices":indices}, POOL)
        payload = chat_payload("deepseek-v4-flash", {}, POOL, "indices")
        supplied = json.loads(payload["messages"][1]["content"])["candidates"]
        self.assertEqual([item["index"] for item in supplied], [0,1])
        self.assertTrue(all("id" not in item for item in supplied))

    def test_indices_live_boundary_preserves_real_product_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "budget.sqlite3"
            BudgetLedger.initialize(ledger)
            env = {"INTENTCOMPASS_SEMANTIC":"deepseek", "INTENTCOMPASS_LLM_ALLOW_NETWORK":"1", "INTENTCOMPASS_LLM_MODEL":"deepseek-v4-flash", "DEEPSEEK_API_KEY":"test-only", "INTENTCOMPASS_LLM_OUTPUT_FORMAT":"indices", "INTENTCOMPASS_BUDGET_LEDGER":str(ledger)}
            response = {"finish_reason":"stop", "content":json.dumps({"ordered_indices":[1,0]}), "usage":{"prompt_tokens":100,"completion_tokens":10}}
            with patch.dict(os.environ, env), patch("solution.chat_reranker.chat_post", return_value=response):
                result = BudgetedChatReranker().rerank(POOL, {})
            self.assertEqual([item.parent_asin for item in result.candidates], ["B","A"])
            self.assertEqual(result.reason, "model_ranked")

    def test_transport_decodes_utf8_independently_of_windows_console(self):
        from solution.api_transport import read_request
        payload = {"provider":"deepseek", "payload":{"text":"é shoes 中文 ☃"}}
        stream = io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        self.assertEqual(read_request(stream), payload)

    def test_probe_abort_is_not_swallowed_by_evaluator_exception_handler(self):
        from scripts.model_probe import LiveScreenAborted
        with self.assertRaises(LiveScreenAborted):
            try:
                raise LiveScreenAborted()
            except Exception:
                self.fail("screen failure must not be counted as a normal missed turn")

    def test_endpoint_and_price_match_region(self):
        self.assertEqual(endpoint_for("qwen", "singapore"), "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions")
        with self.assertRaises(KeyError):
            endpoint_for("qwen", "https://untrusted.example")
        self.assertEqual(cost_micro_rmb("qwen3.8-flash", 1000, 1000, "singapore"), 4521)
        self.assertEqual(cost_micro_rmb("qwen3.7-flash", 1000, 1000, "singapore"), 1199)
        self.assertGreater(cost_micro_rmb("qwen3.7-flash", 33000, 1000, "singapore"), 26000)
        with self.assertRaises(ValueError):
            cost_micro_rmb("qwen3.8-flash", 10, 10, "unconfirmed")

    def test_singapore_live_boundary_uses_regional_billing_and_no_error_text(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "budget.sqlite3"
            BudgetLedger.initialize(ledger)
            env = {"INTENTCOMPASS_SEMANTIC":"qwen", "INTENTCOMPASS_LLM_ALLOW_NETWORK":"1", "INTENTCOMPASS_LLM_MODEL":"qwen3.8-flash", "INTENTCOMPASS_QWEN_REGION":"singapore", "DASHSCOPE_API_KEY":"test-only", "INTENTCOMPASS_BUDGET_LEDGER":str(ledger)}
            response = {"finish_reason":"stop", "content":json.dumps({"ordered_ids":["B","A"]}), "usage":{"prompt_tokens":1000,"completion_tokens":1000}}
            with patch.dict(os.environ, env), patch("solution.chat_reranker.chat_post", return_value=response):
                self.assertEqual(BudgetedChatReranker().rerank(POOL, {}).reason, "model_ranked")
            self.assertEqual(BudgetLedger(ledger).summary()["conservative_cost_rmb"], .004521)
            with patch.dict(os.environ, env), patch("solution.chat_reranker.chat_post", return_value={"error":"http_error","http_status":401,"detail":"do-not-log"}):
                ranker = BudgetedChatReranker()
                self.assertEqual(ranker.rerank(POOL, {}).candidates, POOL)
                self.assertEqual(ranker.last_failure, {"category":"http_error","http_status":401})


class CredentialFileTest(unittest.TestCase):
    def test_dot_delimited_provider_key_is_not_truncated(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / "credentials.txt"
            value = "sk-v2-x.test.segment.signature"
            path.write_text("Qwen: " + value + "\nhttps://dashscope-intl.aliyuncs.com/compatible-mode/v1", encoding="utf-8")
            load_credentials(path)
            self.assertEqual(os.environ["DASHSCOPE_API_KEY"], value)

    def test_labeled_keys_only_enter_environment(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / "credentials.txt"
            path.write_text("DeepSeek: sk-testD\nQwen: sk-testQ\nQwen base_url: https://dashscope-intl.aliyuncs.com/compatible-mode/v1\n", encoding="utf-8")
            result = load_credentials(path)
            self.assertEqual(os.environ["DEEPSEEK_API_KEY"], "sk-testD")
            self.assertEqual(result["qwen_region"], "singapore")
            self.assertNotIn("sk-", json.dumps(result))

    def test_ambiguous_or_untrusted_file_fails_without_partial_environment_update(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / "credentials.txt"
            for text in ["sk-test", "Qwen DeepSeek: sk-test", "DeepSeek: sk-test\nhttps://bad.example", "Qwen: sk-test"]:
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError) as error:
                    load_credentials(path)
                self.assertNotIn("sk-test", str(error.exception))
                self.assertNotIn("DASHSCOPE_API_KEY", os.environ)
                self.assertNotIn("DEEPSEEK_API_KEY", os.environ)


if __name__ == "__main__":
    unittest.main()
