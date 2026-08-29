from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PROTECTED_PREFIXES = ("evaluator/",)
PROTECTED_FILES = {
    "data/public_set.jsonl",
    "docs/agent_api_contract.json",
    "docs/evaluation_config.json",
    "docs/baseline_results.json",
}
TEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".yaml", ".yml", ".txt"}
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "assigned secret": re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|secret)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"
    ),
}


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command))
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )


def git_lines(*args: str) -> set[str]:
    result = run(["git", *args], capture=True)
    if result.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def changed_paths() -> set[str]:
    paths = set()
    paths |= git_lines("diff", "--name-only")
    paths |= git_lines("diff", "--cached", "--name-only")
    paths |= git_lines("ls-files", "--others", "--exclude-standard")
    base = run(["git", "rev-parse", "--verify", "origin/main"], capture=True)
    if base.returncode == 0:
        paths |= git_lines("diff", "--name-only", "origin/main...HEAD")
    return paths


def check_protected(paths: set[str]) -> list[str]:
    violations = []
    for path in sorted(paths):
        if path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES):
            violations.append(f"protected official file changed: {path}")
    return violations


def check_secrets_and_sizes(paths: set[str]) -> list[str]:
    violations = []
    for relative in sorted(paths):
        path = ROOT / relative
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.stat().st_size > 1_000_000:
            violations.append(f"large text artifact must not be committed: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            violations.append(f"non-UTF-8 text file: {relative}")
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                violations.append(f"possible {label} in {relative}")
    return violations


def contract_smoke() -> list[str]:
    agent = None
    try:
        from starter.agent import Agent

        agent = Agent(ROOT / "data" / "catalog.jsonl")
        agent.reset("team-gate-smoke", {})
        payload = agent.respond("team-gate-smoke", "comfortable black shoes", 1, 10)
    except Exception as exc:  # noqa: BLE001 - gate must report any integration failure
        return [f"Agent smoke test failed: {exc}"]
    finally:
        if agent is not None:
            agent.close()

    violations = []
    if not isinstance(payload, dict):
        return ["Agent.respond must return a dict"]
    if not isinstance(payload.get("message"), str):
        violations.append("response.message must be a string")
    ask_attribute = payload.get("ask_attribute")
    allowed = {
        None, "category", "material", "color", "size", "style", "brand",
        "budget", "feature", "use_case", "other",
    }
    if ask_attribute not in allowed:
        violations.append(f"invalid ask_attribute: {ask_attribute!r}")
    recommendations = payload.get("recommendations")
    if not isinstance(recommendations, list):
        violations.append("response.recommendations must be a list")
    elif len(recommendations) > 10:
        violations.append("response.recommendations exceeds Top 10")
    else:
        identifiers = []
        for item in recommendations:
            if not isinstance(item, dict) or not str(item.get("parent_asin", "")).strip():
                violations.append("every recommendation must contain parent_asin")
                break
            identifiers.append(str(item["parent_asin"]))
        if len(identifiers) != len(set(identifiers)):
            violations.append("response contains duplicate parent_asin values")
    return violations


def syntax_check() -> list[str]:
    violations = []
    for directory_name in ("starter", "solution", "tests", "scripts"):
        directory = ROOT / directory_name
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                violations.append(f"Python syntax check failed for {path.relative_to(ROOT)}: {exc}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Track 4 team quality gate")
    parser.add_argument("--full-eval", action="store_true", help="also run the official public evaluator")
    args = parser.parse_args()

    paths = changed_paths()
    violations = check_protected(paths)
    violations += check_secrets_and_sizes(paths)

    diff_check = run(["git", "diff", "--check"])
    if diff_check.returncode != 0:
        violations.append("git diff --check failed")
    base = run(["git", "rev-parse", "--verify", "origin/main"], capture=True)
    if base.returncode == 0:
        committed_diff_check = run(["git", "diff", "--check", "origin/main...HEAD"])
        if committed_diff_check.returncode != 0:
            violations.append("committed diff check against origin/main failed")

    violations += syntax_check()

    tests = run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        capture=True,
    )
    if tests.stdout:
        print(tests.stdout, end="")
    if tests.stderr:
        print(tests.stderr, end="", file=sys.stderr)
    if tests.returncode != 0:
        violations.append("unit tests failed")
    if "ResourceWarning" in f"{tests.stdout}\n{tests.stderr}":
        violations.append("unit tests emitted a ResourceWarning")

    violations += contract_smoke()

    if args.full_eval:
        output = ROOT / "reports" / "generated" / "team-gate-results.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        evaluation = run([
            sys.executable,
            "-m",
            "evaluator.local_evaluator",
            "--output",
            str(output),
        ])
        if evaluation.returncode != 0:
            violations.append("official public evaluation failed")
        elif output.exists():
            try:
                json.loads(output.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                violations.append(f"evaluation output is invalid JSON: {exc}")

    if violations:
        print("\nTEAM GATE FAILED")
        for violation in violations:
            print("-", violation)
        return 1

    print("\nTEAM GATE PASSED")
    print(f"Checked {len(paths)} changed/untracked paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
