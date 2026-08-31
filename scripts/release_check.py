"""Credential-free acceptance runner for the frozen offline release."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import socket
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RELEASE_ID = "intentcompass-rc3"
ALGORITHM_COMMIT = "4968804054bc1159007d34fe40e976bca508fb4f"
PRESET = {
    "INTENTCOMPASS_AGENT_MODE": "integrated",
    "INTENTCOMPASS_RETRIEVAL": "baseline",
    "INTENTCOMPASS_OFFLINE_RANKING": "constraints",
    "INTENTCOMPASS_SEMANTIC": "off",
    "INTENTCOMPASS_LLM_ALLOW_NETWORK": "0",
    "INTENTCOMPASS_CATEGORY_ORDER": "head",
    "INTENTCOMPASS_TERMINAL_RECOVERY": "lastchance",
    "INTENTCOMPASS_PRECISION_ORDER": "separate",
    "INTENTCOMPASS_FINAL_POLICY": "on",
}
SECRET_ENV = {"OPENAI_API_KEY", "DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY"}


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def activate_preset() -> list[str]:
    removed = []
    for name in list(os.environ):
        if name.startswith("INTENTCOMPASS_") or name in SECRET_ENV:
            removed.append(name)
            os.environ.pop(name)
    os.environ.update(PRESET)
    return sorted(removed)  # Names only. Never disclose inherited values.


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and ":" not in name and "\\" not in name and str(path) == name


def verify_manifest(root: Path) -> dict:
    manifest = json.loads((root / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 2 or manifest.get("release_id") != RELEASE_ID
            or manifest.get("algorithm_commit") != ALGORITHM_COMMIT):
        raise ValueError("unexpected release version or algorithm freeze")
    if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("source_commit", "")):
        raise ValueError("invalid source commit")
    if manifest.get("preset") != PRESET or not manifest.get("files"):
        raise ValueError("invalid release preset or empty manifest")
    for name, digest in manifest["files"].items():
        if not safe_member(name):
            raise ValueError("unsafe manifest path")
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
            raise ValueError("payload leaves release directory")
        if not path.is_file() or sha256(path) != digest:
            raise ValueError(f"payload missing or modified: {name}")
    code = list(root.glob("*.py"))
    for directory in ("solution", "starter", "evaluator", "scripts", "demo"):
        code.extend((root / directory).rglob("*.py"))
    if any(p.relative_to(root).as_posix() not in manifest["files"] for p in code):
        raise ValueError("unexpected executable Python payload")
    return manifest


def validate_payload(payload: dict, catalog_ids: set[str], top_k: int = 10) -> None:
    from solution.contracts import ALLOWED_ATTRIBUTES
    if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
        raise ValueError("invalid message")
    if payload.get("ask_attribute") not in {*ALLOWED_ATTRIBUTES, None}:
        raise ValueError("invalid ask_attribute")
    rows = payload.get("recommendations")
    if not isinstance(rows, list) or len(rows) > min(10, max(0, top_k)):
        raise ValueError("invalid recommendation count")
    ids = [p.get("parent_asin") if isinstance(p, dict) else None for p in rows]
    if any(not isinstance(p, str) or p not in catalog_ids for p in ids) or len(ids) != len(set(ids)):
        raise ValueError("invalid or duplicate catalog identifiers")
    if payload.get("usage") != {"prompt_tokens": 0, "completion_tokens": 0}:
        raise ValueError("default offline release must report zero model tokens")


def assert_public_metrics(result: dict) -> None:
    # Test-side expectations only: never passed to production Agent.
    expected = {"sample_count": 200, "hit_rate_at_10": .98, "mrr": .696861, "mttc": 3.755,
                "efficiency": .7245, "recommended_technical_score": .843958}
    scenarios = {"boundary": (10, 1., .678333, 5.), "browsing": (80, .9875, .745273, 2.95),
                 "buying": (80, .9875, .70369, 3.4625), "intent_override": (30, .933333, .555728, 6.266667)}

    def same(actual, expected):
        return (type(actual) in (int, float) and math.isfinite(actual)
                and abs(actual-expected) <= 1e-6)

    for key, value in expected.items():
        if not same(result.get(key), value):
            raise ValueError(f"frozen Public metric mismatch: {key}")
    if set(result["scenario_metrics"]) != set(scenarios):
        raise ValueError("missing scenario")
    for name, values in scenarios.items():
        for key, value in zip(("sample_count", "hit_rate_at_10", "mrr", "mttc"), values):
            if not same(result["scenario_metrics"][name].get(key), value):
                raise ValueError(f"frozen scenario metric mismatch: {name}.{key}")
    if result.get("reported_token_usage") != {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}:
        raise ValueError("frozen release must report zero total model tokens")


def verify_runtime(agent) -> dict:
    core = agent._core._adaptive
    effective = {"mode": core.mode, "retrieval": core.backend_name, "ranking": core.offline_ranking,
                 "semantic_enabled": core.semantic.enabled, "category_order": core.category_order is not None,
                 "terminal_recovery": core.terminal.mode if core.terminal else "off",
                 "precision_order": core.precision.variant if core.precision else "off",
                 "final_policy": core.final_policy is not None}
    if effective != {"mode": "integrated", "retrieval": "baseline", "ranking": "constraints",
                     "semantic_enabled": False, "category_order": True, "terminal_recovery": "lastchance",
                     "precision_order": "separate", "final_policy": True}:
        raise ValueError("effective runtime is not frozen RC3 offline preset")
    return effective


def assert_demo(result: dict) -> None:
    if (result.get("hit") is not True or result.get("override_seen") is not True
            or result.get("first_hit_turn") != 5 or result.get("best_rank") != 8):
        raise ValueError("frozen intent-override demo mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="NEW directory under reports/generated")
    args = parser.parse_args()
    output = (args.output or ROOT / "reports/generated" / datetime.now(timezone.utc).strftime("release-%Y%m%dT%H%M%S%fZ")).resolve()
    if output.exists() or not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("choose a new reports/generated subdirectory")
    output.mkdir(parents=True)
    removed = activate_preset()
    sys.dont_write_bytecode = True
    manifest = verify_manifest(ROOT) if (ROOT / "RELEASE-MANIFEST.json").exists() else None
    from scripts.setup_data import CATALOG_SHA256, require_hash
    catalog = ROOT / "data/catalog.jsonl"
    require_hash(catalog, CATALOG_SHA256, "catalog")
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE VIRTUAL TABLE fts_probe USING fts5(text)")
    protected = {p.relative_to(ROOT).as_posix(): sha256(p) for p in [catalog, ROOT / "data/public_set.jsonl", *sorted((ROOT / "evaluator").glob("*.py")), *sorted((ROOT / "solution").rglob("*.py")), *sorted((ROOT / "starter").glob("*.py")), *sorted((ROOT / "scripts").glob("*.py")), *sorted((ROOT / "demo").rglob("*.py"))]}
    network_attempts = []
    invalid_outputs = []

    def deny_network(*args, **kwargs):
        network_attempts.append(True)
        raise OSError("network forbidden during offline release verification")

    with patch.object(socket.socket, "connect", deny_network), patch.object(socket.socket, "connect_ex", deny_network):
        from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl
        from starter.agent import Agent
        from demo.run_demo import run_session
        ids, categories, products = catalog_index(catalog)
        agent = Agent(catalog)
        try:
            effective_runtime = verify_runtime(agent)
            for sid in ("release-smoke-a", "release-smoke-b"):
                agent.reset(sid, {})
            first = agent.respond("release-smoke-a", "I'm looking for shoes.", 1, 10)
            validate_payload(first, ids)
            agent.reset("release-smoke-a", {})
            if first != agent.respond("release-smoke-a", "I'm looking for shoes.", 1, 10):
                raise ValueError("reset is not deterministic")
            validate_payload(agent.respond("release-smoke-b", "zzzxxyyqqq", 1, 0), ids, 0)

            class CheckedAgent:
                def reset(self, *items):
                    return agent.reset(*items)

                def respond(self, *items):
                    payload = agent.respond(*items)
                    try:
                        validate_payload(payload, ids, items[-1])
                    except (ValueError, TypeError) as exc:
                        invalid_outputs.append(str(exc))
                        raise
                    return payload

            result = evaluate(CheckedAgent(), load_jsonl(ROOT / "data/public_set.jsonl"), ids, categories, products)
        finally:
            agent.close()
        (output / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        if invalid_outputs:
            raise ValueError(f"invalid Agent responses: {len(invalid_outputs)}")
        assert_public_metrics(result)
        demo_result = run_session(verbose=True)
        assert_demo(demo_result)
    if network_attempts:
        raise ValueError(f"network attempted {len(network_attempts)} times")
    if any(sha256(ROOT / name) != value for name, value in protected.items()):
        raise ValueError("solution, evaluator or data mutated during verification")
    if manifest:
        verify_manifest(ROOT)
    report = {
        "status": "RELEASE CHECK PASSED", "source_commit": manifest["source_commit"] if manifest else None,
        "release_id": RELEASE_ID, "algorithm_commit": ALGORITHM_COMMIT,
        "manifest_sha256": sha256(ROOT / "RELEASE-MANIFEST.json") if manifest else None,
        "python": platform.python_version(), "python_executable": sys.executable,
        "platform": platform.platform(), "machine": platform.machine(), "sqlite": sqlite3.sqlite_version,
        "effective_runtime": effective_runtime,
        "preset": PRESET, "ignored_environment_names": removed, "network_attempts": 0,
        "metrics": {k: v for k, v in result.items() if k != "sessions"}, "demo": demo_result,
        "protected_sha256": protected, "results_sha256": sha256(output / "results.json"),
        "scope": "Public release reproduction; not hidden evaluation or submission completion",
    }
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("source_commit", "python", "metrics", "network_attempts")}, indent=2))
    print("RELEASE CHECK PASSED")
    print(f"Evidence: {output}")


if __name__ == "__main__":
    main()
