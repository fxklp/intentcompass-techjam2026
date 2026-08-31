from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.release_check import (
    ALGORITHM_COMMIT, PRESET, RELEASE_ID, activate_preset, assert_demo,
    assert_public_metrics, verify_manifest, verify_runtime,
)


def frozen_result():
    result = {"sample_count": 200, "hit_rate_at_10": .98, "mrr": .696861, "mttc": 3.755,
              "efficiency": .7245, "recommended_technical_score": .843958,
              "reported_token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
              "scenario_metrics": {}}
    for name, values in {"boundary": (10, 1., .678333, 5.), "browsing": (80, .9875, .745273, 2.95),
                         "buying": (80, .9875, .70369, 3.4625), "intent_override": (30, .933333, .555728, 6.266667)}.items():
        result["scenario_metrics"][name] = dict(zip(("sample_count", "hit_rate_at_10", "mrr", "mttc"), values))
    return result


class RC3ReleaseTests(unittest.TestCase):
    def test_exact_rc3_metrics_pass(self):
        assert_public_metrics(frozen_result())

    def test_rc2_and_task013_metrics_are_rejected(self):
        for values in ((.91, .648734, 4.255, .784520), (.975, .693046, 4.19, .831614)):
            result = frozen_result()
            result.update(zip(("hit_rate_at_10", "mrr", "mttc", "recommended_technical_score"), values))
            with self.assertRaises(ValueError):
                assert_public_metrics(result)

    def test_every_overall_metric_is_checked(self):
        for key in ("sample_count", "hit_rate_at_10", "mrr", "mttc", "efficiency", "recommended_technical_score"):
            result = frozen_result()
            result[key] += .001
            with self.assertRaisesRegex(ValueError, key):
                assert_public_metrics(result)

    def test_every_scenario_metric_and_count_is_checked(self):
        for scenario in frozen_result()["scenario_metrics"]:
            for key in ("sample_count", "hit_rate_at_10", "mrr", "mttc"):
                result = frozen_result()
                result["scenario_metrics"][scenario][key] += .001
                with self.assertRaisesRegex(ValueError, scenario):
                    assert_public_metrics(result)

    def test_nan_infinity_non_numeric_and_missing_fail(self):
        for value in (float("nan"), float("inf"), ".98", None, True):
            result = frozen_result()
            result["hit_rate_at_10"] = value
            with self.assertRaises(ValueError):
                assert_public_metrics(result)
        result = frozen_result()
        del result["mrr"]
        with self.assertRaises(ValueError):
            assert_public_metrics(result)

    def test_model_tokens_fail(self):
        result = frozen_result()
        result["reported_token_usage"]["total_tokens"] = 1
        with self.assertRaises(ValueError):
            assert_public_metrics(result)

    def test_final_components_cannot_be_overridden_by_inherited_environment(self):
        hostile = {"INTENTCOMPASS_TERMINAL_RECOVERY": "off", "INTENTCOMPASS_PRECISION_ORDER": "off",
                   "INTENTCOMPASS_FINAL_POLICY": "off", "INTENTCOMPASS_SEMANTIC": "qwen",
                   "INTENTCOMPASS_LLM_ALLOW_NETWORK": "1"}
        with patch.dict(os.environ, hostile):
            activate_preset()
            self.assertEqual({k: os.environ[k] for k in PRESET}, PRESET)
            self.assertEqual(os.environ["INTENTCOMPASS_FINAL_POLICY"], "on")
            self.assertEqual(os.environ["INTENTCOMPASS_TERMINAL_RECOVERY"], "lastchance")

    def test_runtime_checks_all_frozen_components(self):
        core = SimpleNamespace(mode="integrated", backend_name="baseline", offline_ranking="constraints",
                               semantic=SimpleNamespace(enabled=False), category_order=object(),
                               terminal=SimpleNamespace(mode="lastchance"), precision=SimpleNamespace(variant="separate"),
                               final_policy=object())
        def agent(value):
            return SimpleNamespace(_core=SimpleNamespace(_adaptive=value))
        self.assertTrue(verify_runtime(agent(core))["final_policy"])
        for key, value in (("mode", "adaptive"), ("backend_name", "dual_route"), ("offline_ranking", "baseline"),
                           ("semantic", SimpleNamespace(enabled=True)), ("category_order", None), ("terminal", None),
                           ("precision", None), ("final_policy", None)):
            changed = copy.copy(core)
            setattr(changed, key, value)
            with self.assertRaises(ValueError):
                verify_runtime(agent(changed))

    def test_demo_requires_hit_override_and_frozen_turn_rank(self):
        result = {"hit": True, "override_seen": True, "first_hit_turn": 5, "best_rank": 8}
        assert_demo(result)
        for key, value in (("hit", False), ("override_seen", False), ("first_hit_turn", 4), ("best_rank", 9)):
            with self.assertRaises(ValueError):
                assert_demo(dict(result, **{key: value}))

    def test_manifest_rejects_version_or_algorithm_mixing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "agent.py").write_bytes(b"pass\n")
            manifest = {"schema_version": 2, "release_id": RELEASE_ID, "algorithm_commit": ALGORITHM_COMMIT,
                        "source_commit": "a"*40, "preset": PRESET,
                        "files": {"agent.py": hashlib.sha256(b"pass\n").hexdigest()}}
            target = root / "RELEASE-MANIFEST.json"
            target.write_text(json.dumps(manifest), encoding="utf-8")
            verify_manifest(root)
            for key, value in (("schema_version", 1), ("release_id", "intentcompass-rc2"), ("algorithm_commit", "b"*40)):
                target.write_text(json.dumps(dict(manifest, **{key: value})), encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_manifest(root)


if __name__ == "__main__":
    unittest.main()
