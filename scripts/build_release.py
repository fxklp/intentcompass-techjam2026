"""Build an allowlisted, deterministic, source-only release ZIP from HEAD."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.release_check import ALGORITHM_COMMIT, PRESET, RELEASE_ID, safe_member

EXACT = {"README.md", "requirements.txt", "DATA_ATTRIBUTION.md", "data/public_set.jsonl",
         "scripts/setup_data.py", "scripts/release_check.py", "scripts/run_offline.py", "docs/agent_api_contract.json",
         "docs/evaluation_config.json", "docs/baseline_results.json"}


def included(name: str) -> bool:
    if not safe_member(name):
        return False
    return name in EXACT or (name.startswith(("solution/", "starter/", "evaluator/", "demo/")) and name.endswith(".py")) or (name.startswith("docs/release/") and name.endswith(".md"))


def scan_payload(name: str, content: bytes) -> None:
    text = content.decode("utf-8")
    if re.search(r"\bsk-[A-Za-z0-9_-]{16,}\b|\bAKIA[0-9A-Z]{16}\b|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----", text):
        raise ValueError(f"possible credential in {name}")
    if re.search(r"[A-Za-z]:[\\/]Users[\\/]|/Users/[^/\s]+/|/home/[^/\s]+/", text):
        raise ValueError(f"personal absolute path in {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "artifacts").resolve()) or output.suffix != ".zip":
        parser.error("choose a NEW .zip under artifacts")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        parser.error("commit all intended changes and use a clean worktree")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit], cwd=ROOT, text=True).splitlines()
    payload = {}
    for name in sorted(filter(included, names)):
        content = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
        scan_payload(name, content)
        payload[name] = content
    if not EXACT.issubset(payload):
        raise ValueError("missing required release file")
    manifest = {"schema_version": 2, "release_id": RELEASE_ID, "algorithm_commit": ALGORITHM_COMMIT,
                "source_commit": commit, "preset": PRESET,
                "files": {name: hashlib.sha256(content).hexdigest() for name, content in payload.items()},
                "excluded": ["catalog (download using setup_data.py)", "credentials", "models", "indexes", "API budget ledger", "private/final labels", "Git metadata", "historical experiment outputs"],
                "integrity_note": "Checksums detect accidental changes; this is not a digital signature."}
    payload["RELEASE-MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 31, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    print(json.dumps({"source_commit": commit, "file_count": len(payload), "bytes": output.stat().st_size,
                      "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
