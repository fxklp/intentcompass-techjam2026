from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.setup_data import file_sha256, require_hash


class SetupDataTest(unittest.TestCase):
    def test_hash_verification_accepts_expected_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.jsonl"
            path.write_bytes(b'{"parent_asin":"demo"}\n')
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            require_hash(path, expected, "fixture")
            self.assertEqual(file_sha256(path), expected)

    def test_hash_verification_rejects_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.jsonl"
            path.write_bytes(b"corrupted")
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                require_hash(path, "0" * 64, "fixture")


if __name__ == "__main__":
    unittest.main()
