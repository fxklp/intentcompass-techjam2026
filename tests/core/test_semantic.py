from __future__ import annotations

import copy
import json
import os
import unittest
from unittest.mock import patch

from solution.contracts import Candidate
from solution.semantic import SemanticReranker, request_body, response_usage, validated_order


POOL = [Candidate("A", 0, 1.0, "red shoes", 40), Candidate("B", 1, 0.5, "blue shoes", 50)]


def response(ids: list[str] | None = None) -> dict:
    return {
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"ordered_ids": ids if ids is not None else ["B", "A"]})}]}],
        "usage": {"input_tokens": 123, "output_tokens": 27},
    }


class SemanticTest(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {
            "INTENTCOMPASS_SEMANTIC": "openai", "INTENTCOMPASS_LLM_ALLOW_NETWORK": "1",
            "INTENTCOMPASS_LLM_MODEL": "test-model", "INTENTCOMPASS_LLM_MAX_CALLS": "2",
            "OPENAI_API_KEY": "test-only",
        })
        environment.start()
        self.addCleanup(environment.stop)

    def test_valid_model_order_and_actual_usage(self) -> None:
        ranker = SemanticReranker()
        with patch("solution.semantic.post_response", return_value=response()) as transport:
            result = ranker.rerank(POOL, {})
        self.assertEqual([item.parent_asin for item in result.candidates], ["B", "A"])
        self.assertEqual(result.usage, {"prompt_tokens": 123, "completion_tokens": 27})
        self.assertTrue(result.attempted)
        self.assertEqual(transport.call_count, 1)

    def test_unknown_duplicate_missing_and_non_string_ids_rejected(self) -> None:
        for ids in (["B", "UNKNOWN"], ["A", "A"], ["A"], ["A", 1]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                validated_order(response(ids), POOL)

    def test_invalid_ranking_keeps_known_usage_and_baseline(self) -> None:
        with patch("solution.semantic.post_response", return_value=response(["A", "unknown"])):
            result = SemanticReranker().rerank(POOL, {})
        self.assertEqual(result.candidates, POOL)
        self.assertEqual(result.usage["prompt_tokens"], 123)
        self.assertEqual(result.reason, "model_failed_offline_fallback")

    def test_refusal_incomplete_and_malformed_fail_closed(self) -> None:
        refusal = response()
        refusal["output"][0]["content"] = [{"type": "refusal", "refusal": "no"}]
        incomplete = dict(response(), status="incomplete")
        malformed = response()
        malformed["output"][0]["content"][0]["text"] = "not JSON"
        for value in (refusal, incomplete, malformed, None, {"output": None}):
            with self.subTest(value=value), patch("solution.semantic.post_response", return_value=value):
                self.assertEqual(SemanticReranker().rerank(POOL, {}).candidates, POOL)

    def test_timeout_unknown_usage_and_no_retry(self) -> None:
        ranker = SemanticReranker()
        with patch("solution.semantic.post_response", side_effect=TimeoutError) as transport:
            first = ranker.rerank(POOL, {})
            second = ranker.rerank(POOL, {})
        self.assertIsNone(first.usage)
        self.assertTrue(first.attempted)
        self.assertFalse(second.attempted)
        self.assertEqual(transport.call_count, 1)

    def test_offline_missing_key_and_request_cap_never_send(self) -> None:
        for environment in (
            {"INTENTCOMPASS_SEMANTIC": "off"},
            {"INTENTCOMPASS_LLM_ALLOW_NETWORK": "0"},
            {"OPENAI_API_KEY": ""},
            {"INTENTCOMPASS_LLM_MAX_CALLS": "0"},
            {"INTENTCOMPASS_LLM_MODEL": ""},
        ):
            with self.subTest(environment=environment), patch.dict(os.environ, environment), patch("solution.semantic.post_response") as transport:
                result = SemanticReranker().rerank(POOL, {})
                transport.assert_not_called()
                self.assertFalse(result.attempted)
                self.assertEqual(result.candidates, POOL)

    def test_cap_is_global_to_agent_not_session(self) -> None:
        with patch.dict(os.environ, {"INTENTCOMPASS_LLM_MAX_CALLS": "1"}):
            ranker = SemanticReranker()
        with patch("solution.semantic.post_response", return_value=response()) as transport:
            ranker.rerank(POOL, {"category": "shoes"})
            second = ranker.rerank(POOL, {"category": "bags"})
        self.assertEqual(transport.call_count, 1)
        self.assertFalse(second.attempted)

    def test_payload_bounded_and_no_profile_identity_or_history(self) -> None:
        context = {"session_id": "DO-NOT-SEND", "summary": "PRIVATE", "transcript": "RAW", "category": "x" * 200, "explicit": {"color": ["y" * 200] * 6, "identity": ["PRIVATE"]}, "profile_priors": {}}
        body = request_body("test-model", context, POOL)
        serialized = json.dumps(body)
        for value in ("DO-NOT-SEND", "PRIVATE", "RAW"):
            self.assertNotIn(value, serialized)
        self.assertFalse(body["store"])
        self.assertTrue(body["text"]["format"]["strict"])
        self.assertEqual(body["text"]["format"]["schema"]["properties"]["ordered_ids"]["items"]["enum"], ["A", "B"])
        safe = json.loads(body["input"])["context"]
        self.assertEqual(len(safe["category"]), 160)
        self.assertEqual(len(safe["explicit"]["color"]), 4)
        self.assertEqual(len(safe["explicit"]["color"][0]), 120)

    def test_bad_usage_not_presented_as_zero(self) -> None:
        for usage in (None, {}, {"input_tokens": -1, "output_tokens": 2}, {"input_tokens": True, "output_tokens": 2}):
            self.assertIsNone(response_usage({"usage": usage}))
        reply = copy.deepcopy(response())
        reply.pop("usage")
        with patch("solution.semantic.post_response", return_value=reply):
            result = SemanticReranker().rerank(POOL, {})
        self.assertIsNone(result.usage)
        self.assertEqual(result.candidates, POOL)


if __name__ == "__main__":
    unittest.main()
