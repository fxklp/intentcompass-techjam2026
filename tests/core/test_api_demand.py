from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from solution.api_budget import BudgetLedger, BudgetUnavailable
from solution.api_demand import DemandState, evidence_text
from solution.chat_reranker import BudgetedChatReranker, chat_payload
from solution.contracts import Candidate
from solution.semantic import SemanticResult
from tests.core.api_experiment import quality_verdict
from tests.core.test_final import POOL


CONTEXT = {"category": "shoes", "explicit": {"color": ["red"], "material": ["leather"]}}


class DemandPolicyTest(unittest.TestCase):
    def model(self):
        model = Mock()
        model.rerank.side_effect = lambda pool, ctx: SemanticResult(list(reversed(pool)), "model_ranked", {"prompt_tokens": 20, "completion_tokens": 5}, True)
        return model

    def test_information_gate_excludes_category_and_profile(self):
        model = self.model()
        for context in ({}, {"explicit": {"category":["shoes"],"color":["red"]}}, {"profile_priors":{"color":["red"],"material":["leather"]}}):
            result = DemandState().rerank(model, POOL, context)
            self.assertEqual(result.candidates, POOL)
            self.assertFalse(result.attempted)
        model.rerank.assert_not_called()

    def test_exact_cache_is_free_but_context_override_invalidates(self):
        state, model = DemandState(), self.model()
        first = state.rerank(model, POOL, CONTEXT)
        cached = state.rerank(model, POOL, CONTEXT)
        self.assertEqual(first.candidates, cached.candidates)
        self.assertEqual(cached.reason, "demand_exact_cache")
        self.assertEqual(cached.usage, {"prompt_tokens":0,"completion_tokens":0})
        self.assertFalse(cached.attempted)
        state.rerank(model, POOL, {"explicit":{"color":["blue"],"material":["leather"]}})
        self.assertEqual(model.rerank.call_count, 2)

    def test_pool_order_metadata_and_sessions_are_not_shared(self):
        state, model = DemandState(), self.model()
        state.rerank(model, POOL, CONTEXT)
        state.rerank(model, list(reversed(POOL)), CONTEXT)
        changed = [Candidate("A", 0, 1, "different title", 40), POOL[1]]
        state.rerank(model, changed, CONTEXT)
        self.assertEqual(model.rerank.call_count, 3)
        self.assertEqual(state.rerank(model, POOL, CONTEXT).reason, "demand_session_call_limit")
        self.assertEqual(DemandState().rerank(model, POOL, CONTEXT).reason, "model_ranked")

    def test_failure_not_cached_and_attempt_limit_counts_failures(self):
        model = Mock()
        model.rerank.return_value = SemanticResult(POOL, "model_failed_offline_fallback", None, True)
        state = DemandState()
        for _ in range(4):
            self.assertEqual(state.rerank(model, POOL, CONTEXT).candidates, POOL)
        self.assertIsNone(state.key)
        self.assertEqual(model.rerank.call_count, 3)

    def test_compact_evidence_retains_late_constraint_and_bounds_text(self):
        text = "Catalog title " + "filler "*100 + "red leather" + " suffix"*100
        compact = evidence_text(text, CONTEXT, 320)
        self.assertLessEqual(len(compact), 320)
        self.assertTrue(compact.startswith("Catalog title"))
        self.assertIn("red leather", compact)
        payload = chat_payload("qwen3.8-max", {**CONTEXT,"ground_truth":"DO_NOT_EXPORT"}, [Candidate("A",0,1,text)], "indices", text_limit=320)
        self.assertNotIn("DO_NOT_EXPORT", json.dumps(payload))

    def test_wide_policy_ranks_full_window_with_strict_existing_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"ledger.sqlite3"
            BudgetLedger.initialize(path)
            pool = [Candidate(str(i),i,1,"red leather shoe",40) for i in range(45)]
            response = {"finish_reason":"stop", "usage":{"prompt_tokens":100,"completion_tokens":50}, "content":json.dumps({"ordered_indices":list(reversed(range(40)))})}
            env = {"INTENTCOMPASS_SEMANTIC":"qwen","INTENTCOMPASS_API_POLICY":"demand40", "INTENTCOMPASS_LLM_MODEL":"qwen3.8-max", "INTENTCOMPASS_LLM_OUTPUT_FORMAT":"indices", "INTENTCOMPASS_QWEN_REGION":"singapore", "INTENTCOMPASS_LLM_ALLOW_NETWORK":"1", "DASHSCOPE_API_KEY":"test-only", "INTENTCOMPASS_BUDGET_LEDGER":str(path)}
            with patch.dict(os.environ, env), patch("solution.chat_reranker.chat_post", return_value=response):
                result = BudgetedChatReranker().rerank(pool, CONTEXT)
            self.assertEqual([c.parent_asin for c in result.candidates], [str(i) for i in reversed(range(40))]+[str(i) for i in range(40,45)])

    def test_per_run_ceiling_cannot_bypass_shared_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"ledger.sqlite3"
            BudgetLedger.initialize(path)
            ledger = BudgetLedger(path)
            ledger.reserve("qwen3.8-max", 50, ceiling_micro_rmb=100)
            with self.assertRaises(BudgetUnavailable):
                ledger.reserve("qwen3.8-max", 51, ceiling_micro_rmb=100)
            self.assertEqual(ledger.summary()["conservative_cost_rmb"], .00005)
            for limit in (-1, 0, True, 100_000_001):
                with self.assertRaises(BudgetUnavailable):
                    ledger.reserve("qwen3.8-max", 1, ceiling_micro_rmb=limit)

    def test_quality_gate_never_calls_two_gains_all_three(self):
        old = {"hit_rate_at_10":.9,"mrr":.6,"mttc":4,"scenario_metrics":{}}
        new = {**old, "mrr":.7,"mttc":3}
        self.assertTrue(quality_verdict(old,new)["preliminary_quality_pass"])
        self.assertFalse(quality_verdict(old,new)["all_three_strictly_better"])
        self.assertTrue(quality_verdict(old,{**new,"hit_rate_at_10":.91})["all_three_strictly_better"])
        self.assertFalse(quality_verdict(old,{**new,"hit_rate_at_10":.89})["preliminary_quality_pass"])


if __name__ == "__main__":
    unittest.main()
