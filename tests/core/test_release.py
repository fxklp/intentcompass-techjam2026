from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_release import included, scan_payload
from scripts.release_check import PRESET, activate_preset, assert_public_metrics, safe_member, validate_payload, verify_manifest


class ReleaseTest(unittest.TestCase):
    def test_allowlist_excludes_secrets_models_and_experiments(self):
        for name in ("api_key.txt", ".env", "data/catalog.jsonl", "artifacts/budget.sqlite3", "organizer/private.json", "reports/generated/raw.json", "experiments/run.py"):
            self.assertFalse(included(name), name)
        for name in ("solution/state.py", "starter/agent.py", "evaluator/local_evaluator.py", "README.md"):
            self.assertTrue(included(name), name)

    def test_unsafe_paths_rejected(self):
        for name in ("../escape.py", "/absolute.py", "C:/escape.py", "solution/../escape.py", "solution\\state.py"):
            self.assertFalse(safe_member(name))

    def test_environment_cannot_enable_experimental_or_paid_path(self):
        with patch.dict(os.environ, {"INTENTCOMPASS_SEMANTIC":"qwen", "INTENTCOMPASS_LLM_ALLOW_NETWORK":"1", "INTENTCOMPASS_LLM_MODEL":"test-model", "DASHSCOPE_API_KEY":"unit-test-only"}):
            removed = activate_preset()
            self.assertIn("DASHSCOPE_API_KEY", removed)
            self.assertNotIn("DASHSCOPE_API_KEY", os.environ)
            self.assertNotIn("INTENTCOMPASS_LLM_MODEL", os.environ)
            self.assertEqual({key:os.environ[key] for key in PRESET}, PRESET)

    def test_manifest_detects_tampering_missing_and_extra_python(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            code=root/"agent.py"
            code.write_bytes(b"pass\n")
            manifest={"source_commit":"a"*40,"preset":PRESET,"files":{"agent.py":hashlib.sha256(code.read_bytes()).hexdigest()}}
            (root/"RELEASE-MANIFEST.json").write_text(json.dumps(manifest),encoding="utf-8")
            verify_manifest(root)
            code.write_bytes(b"print(1)\n")
            with self.assertRaises(ValueError):
                verify_manifest(root)
            code.unlink()
            with self.assertRaises(ValueError):
                verify_manifest(root)
            code.write_bytes(b"pass\n")
            (root/"surprise.py").write_bytes(b"pass\n")
            with self.assertRaises(ValueError):
                verify_manifest(root)

    def test_secret_scanner_does_not_print_values(self):
        credential="sk-"+"A"*20
        with self.assertRaises(ValueError) as failure:
            scan_payload("bad.py",credential.encode())
        self.assertNotIn(credential,str(failure.exception))
        scan_payload("ok.py",b"import os\n")

    def test_output_requires_valid_unique_ids_and_zero_tokens(self):
        payload={"message":"hello","ask_attribute":None,"recommendations":[{"parent_asin":"A"}],"usage":{"prompt_tokens":0,"completion_tokens":0}}
        validate_payload(payload,{"A"})
        payload["recommendations"]*=2
        with self.assertRaises(ValueError):
            validate_payload(payload,{"A"})
        payload["recommendations"]=[{"parent_asin":"B"}]
        with self.assertRaises(ValueError):
            validate_payload(payload,{"A"})

    def test_public_gate_checks_scenarios_not_only_overall(self):
        result={"sample_count":200,"hit_rate_at_10":.91,"mrr":.624024,"mttc":4.255,"recommended_technical_score":.777107,"scenario_metrics":{}}
        with self.assertRaises(ValueError):
            assert_public_metrics(result)


if __name__ == "__main__":
    unittest.main()
