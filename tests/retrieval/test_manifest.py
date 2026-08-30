from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.retrieval.evaluate import main as evaluate_main


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "artifacts" / "manifests" / "TASK-303-dual-route-inmemory.json"


def validate_evidence(path: Path, expected_sha256: str) -> None:
    raw = path.read_bytes()
    if b"\r" in raw or not raw.endswith(b"\n"):
        raise ValueError(f"{path.name} is not an LF-terminated file")
    raw.decode("utf-8")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"{path.name} SHA-256 mismatch: {actual_sha256} != {expected_sha256}"
        )


class EvidenceManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_checked_in_evidence_uses_lf_and_matches_manifest(self) -> None:
        for evidence in self.manifest["evidence"].values():
            with self.subTest(path=evidence["path"]):
                validate_evidence(ROOT / evidence["path"], evidence["sha256"])

    def test_tampered_evidence_fails_hash_validation(self) -> None:
        evidence = self.manifest["evidence"]["results"]
        original = (ROOT / evidence["path"]).read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            tampered = Path(temporary) / "tampered.json"
            tampered_bytes = original.replace(
                b'"schema_version": 1', b'"schema_version": 2', 1
            )
            self.assertNotEqual(original, tampered_bytes)
            tampered.write_bytes(tampered_bytes)
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                validate_evidence(tampered, evidence["sha256"])

    def test_evaluate_worker_writes_utf8_lf_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            argv = [
                "evaluate.py",
                "--worker",
                "--mode",
                "baseline",
                "--dataset",
                "public",
                "--catalog",
                str(Path(temporary) / "catalog.jsonl"),
                "--output",
                str(output),
            ]
            with patch.object(sys, "argv", argv), patch(
                "experiments.retrieval.evaluate.worker",
                return_value={"message": "caf\u00e9"},
            ):
                evaluate_main()
            raw_output = output.read_bytes()
            self.assertTrue(raw_output.endswith(b"\n"))
            self.assertNotIn(b"\r\n", raw_output)
            self.assertEqual({"message": "caf\u00e9"}, json.loads(raw_output.decode("utf-8")))


if __name__ == "__main__":
    unittest.main()
