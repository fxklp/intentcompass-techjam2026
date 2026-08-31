from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCENARIO_LABELS = {
    "buying": "Buying",
    "browsing": "Browsing",
    "intent_override": "Intent Override",
    "boundary": "Boundary",
}
DIFFICULTY_LABELS = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
}
EXPECTED_FAILURES = {
    "buying": 6,
    "browsing": 4,
    "intent_override": 7,
    "boundary": 1,
}
TAXONOMY = (
    {
        "name": "Post-override recovery",
        "scenarios": ("intent_override",),
        "interpretation": (
            "Failures concentrate after the active intent changes, indicating that "
            "state replacement, query reconstruction, or post-change candidate recovery "
            "remains the highest-risk path."
        ),
        "direction": (
            "Test slot replacement and query rebuilding as one invariant; after a material "
            "change, retrieve a fresh and sufficiently broad candidate pool before reranking."
        ),
    },
    {
        "name": "Constrained-buying recall or ranking",
        "scenarios": ("buying",),
        "interpretation": (
            "Failures remain even when a hard constraint is disclosed early. Outcome-only "
            "evidence cannot separate candidate-recall loss from incorrect final ordering."
        ),
        "direction": (
            "Measure candidate recall before reranking, normalize equivalent constraint wording, "
            "and combine field-aware lexical retrieval with a general semantic fallback."
        ),
    },
    {
        "name": "Ambiguity and no-preference handling",
        "scenarios": ("browsing", "boundary"),
        "interpretation": (
            "Vague requests and absent preferences form a shared clarification problem: the "
            "agent must ask useful questions without narrowing too early or repeating a cleared slot."
        ),
        "direction": (
            "Choose clarifications by expected information gain, preserve diverse recommendations "
            "while evidence is sparse, and mark no-preference attributes as non-blocking."
        ),
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the TASK-201 public failure taxonomy from evaluator evidence."
    )
    parser.add_argument(
        "--result",
        type=Path,
        default=Path("reports/analysis/evidence/team-gate-results.json"),
        help="Evaluator result JSON containing per-session outcomes.",
    )
    parser.add_argument(
        "--public-set",
        type=Path,
        default=Path("data/public_set.jsonl"),
        help="Public-set JSONL containing scenario and difficulty metadata.",
    )
    parser.add_argument(
        "--baseline-commit",
        default="ccd58846a286ae1f102c28388ffe8364787df764",
        help="Immutable baseline commit associated with the evaluator result.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/analysis/TASK-201-failure-taxonomy.md"),
        help="Generated Markdown report path.",
    )
    return parser.parse_args()


def canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_jsonl_by_id(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            sample_id = record.get("sample_id")
            if not isinstance(sample_id, str) or not sample_id:
                raise ValueError(f"{path}:{line_number} has no valid sample_id")
            if sample_id in records:
                raise ValueError(f"duplicate public sample_id: {sample_id}")
            records[sample_id] = record
    return records


def validate_commit(commit: str) -> None:
    if not 7 <= len(commit) <= 40 or any(character not in "0123456789abcdef" for character in commit.lower()):
        raise ValueError("baseline commit must be a 7-40 character hexadecimal Git revision")
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ValueError(f"baseline commit {commit} not found in the local repository") from exc


def analyze(
    result: dict[str, Any],
    public_records: dict[str, dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    Counter[str],
    Counter[str],
    dict[str, Counter[str]],
]:
    sessions = result.get("sessions")
    if not isinstance(sessions, list):
        raise ValueError("result JSON must contain a sessions array")
    if result.get("sample_count") != len(sessions):
        raise ValueError("result sample_count does not match the sessions array")

    seen_ids: set[str] = set()
    failures: list[dict[str, Any]] = []
    for index, session in enumerate(sessions):
        if not isinstance(session, dict):
            raise ValueError(f"result session {index} must be an object")
        sample_id = session.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            raise ValueError(f"result session {index} has no valid sample_id")
        if sample_id in seen_ids:
            raise ValueError(f"duplicate result sample_id: {sample_id}")
        seen_ids.add(sample_id)
        public_record = public_records.get(sample_id)
        if public_record is None:
            raise ValueError(f"result sample is absent from the public set: {sample_id}")

        result_scenario = session.get("scenario_type")
        public_scenario = public_record.get("scenario_type")
        if result_scenario != public_scenario:
            raise ValueError(f"scenario mismatch for result sample: {sample_id}")
        if result_scenario not in SCENARIO_LABELS:
            raise ValueError(f"unknown scenario type: {result_scenario!r}")
        difficulty = public_record.get("difficulty_bucket")
        if difficulty not in DIFFICULTY_LABELS:
            raise ValueError(f"unknown difficulty bucket: {difficulty!r}")
        if not isinstance(session.get("hit"), bool):
            raise ValueError(f"result sample has a non-boolean hit field: {sample_id}")
        if not session["hit"]:
            failures.append({
                "scenario": result_scenario,
                "difficulty": difficulty,
                "best_rank": session.get("best_rank"),
                "first_hit_turn": session.get("first_hit_turn"),
                "reciprocal_rank": session.get("reciprocal_rank"),
                "category": public_record.get("category_bucket"),
            })

    if len(seen_ids) != len(public_records):
        raise ValueError(
            f"result/public-set size mismatch: {len(seen_ids)} results vs "
            f"{len(public_records)} public records"
        )

    scenario_failures = Counter(failure["scenario"] for failure in failures)
    difficulty_failures = Counter(failure["difficulty"] for failure in failures)
    cross_failures: dict[str, Counter[str]] = defaultdict(Counter)
    for failure in failures:
        cross_failures[failure["scenario"]][failure["difficulty"]] += 1

    if len(failures) != sum(EXPECTED_FAILURES.values()):
        raise ValueError(
            f"expected {sum(EXPECTED_FAILURES.values())} failures, observed {len(failures)}"
        )
    for scenario, expected_count in EXPECTED_FAILURES.items():
        observed = scenario_failures[scenario]
        if observed != expected_count:
            raise ValueError(
                f"expected {expected_count} {SCENARIO_LABELS[scenario]} failures, observed {observed}"
            )

    return failures, scenario_failures, difficulty_failures, cross_failures


def percentage(numerator: int, denominator: int) -> str:
    return f"{(100.0 * numerator / denominator):.2f}%" if denominator else "n/a"


def observable_evidence_section(failures: list[dict[str, Any]]) -> list[str]:
    null_rank = sum(1 for f in failures if f["best_rank"] is None)
    null_turn = sum(1 for f in failures if f["first_hit_turn"] is None)
    zero_rr = sum(1 for f in failures if f["reciprocal_rank"] == 0.0)
    categories = Counter(f["category"] for f in failures)
    total = len(failures)

    lines = [
        "## Observable evidence from failed sessions",
        "",
        "The evaluator records four session-level signals per sample: `hit`, `best_rank`, "
        "`first_hit_turn`, and `reciprocal_rank`. Aggregating across the 18 failures:",
        "",
        "| Signal | Observation | Count |",
        "| --- | --- | ---: |",
        f"| `best_rank` | `null` (target never appeared in any recommendation list) | {null_rank}/{total} |",
        f"| `first_hit_turn` | `null` (target never surfaced at any turn) | {null_turn}/{total} |",
        f"| `reciprocal_rank` | `0.0` (complete recall miss) | {zero_rr}/{total} |",
        f"| `category_bucket` | {', '.join(f'{c} ({n})' for c, n in categories.most_common())} | {total}/{total} |",
        "",
        "All 18 failures are **complete recall misses**: the target product was never retrieved "
        "into any recommendation list at any conversational turn. The evaluator data contains "
        "no partial-hit or near-miss signals that could differentiate failure mechanisms "
        "across scenarios. Consequently, the failure classes below are hypotheses derived from "
        "scenario metadata and difficulty concentration, not from fine-grained behavioral traces.",
        "",
    ]
    return lines


def markdown_report(
    *,
    result_path: Path,
    result_canonical_sha256: str,
    public_path: Path,
    public_canonical_sha256: str,
    baseline_commit: str,
    result: dict[str, Any],
    public_records: dict[str, dict[str, Any]],
    failures: list[dict[str, Any]],
    scenario_failures: Counter[str],
    difficulty_failures: Counter[str],
    cross_failures: dict[str, Counter[str]],
) -> str:
    scenario_totals = Counter(
        str(record["scenario_type"]) for record in public_records.values()
    )
    difficulty_totals = Counter(
        str(record["difficulty_bucket"]) for record in public_records.values()
    )
    command = (
        f"python analysis/failure_taxonomy.py "
        f"--result {result_path.as_posix()} "
        f"--public-set {public_path.as_posix()} "
        f"--baseline-commit {baseline_commit} "
        f"--output reports/analysis/TASK-201-failure-taxonomy.md"
    )

    lines = [
        "# TASK-201 public-set failure taxonomy",
        "",
        "## Evidence ledger",
        "",
        f"- Baseline commit: `{baseline_commit}` (`{baseline_commit[:7]}`).",
        f"- Evaluator result: `{result_path.as_posix()}`.",
        f"- Evaluator result Canonical-LF SHA-256: `{result_canonical_sha256}`.",
        f"- Public metadata: `{public_path.as_posix()}`.",
        f"- Public metadata Canonical-LF SHA-256: `{public_canonical_sha256}`.",
        f"- Evaluated sessions: {result['sample_count']}.",
        "- The report aggregates metadata only; it emits no sample identifiers or target products.",
        "",
        "Regeneration command:",
        "",
        "```bash",
        command,
        "```",
        "",
        "The script validates unique session identifiers, a complete one-to-one join with the public set, "
        "scenario consistency, supported difficulty buckets, the expected 18-failure breakdown, and "
        "that the baseline commit exists in the local repository. "
        "A mismatch exits non-zero instead of generating a report.",
        "",
        "## Failure classification",
        "",
        "### By scenario",
        "",
        "| Scenario | Public sessions | Failures | Failure rate | Expected failures | Check |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for scenario in ("buying", "browsing", "intent_override", "boundary"):
        observed = scenario_failures[scenario]
        expected = EXPECTED_FAILURES[scenario]
        lines.append(
            f"| {SCENARIO_LABELS[scenario]} | {scenario_totals[scenario]} | {observed} | "
            f"{percentage(observed, scenario_totals[scenario])} | {expected} | "
            f"{'Pass' if observed == expected else 'Fail'} |"
        )
    total_pass = len(failures) == sum(EXPECTED_FAILURES.values())
    lines.extend(
        [
            f"| **Total** | **{len(public_records)}** | **{len(failures)}** | "
            f"**{percentage(len(failures), len(public_records))}** | "
            f"**{sum(EXPECTED_FAILURES.values())}** | "
            f"**{'Pass' if total_pass else 'Fail'}** |",
            "",
            "### By difficulty",
            "",
            "| Difficulty | Public sessions | Failures | Failure rate | Share of failures |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for difficulty in ("easy", "medium", "hard"):
        observed = difficulty_failures[difficulty]
        lines.append(
            f"| {DIFFICULTY_LABELS[difficulty]} | {difficulty_totals[difficulty]} | {observed} | "
            f"{percentage(observed, difficulty_totals[difficulty])} | "
            f"{percentage(observed, len(failures))} |"
        )
    lines.extend(
        [
            "",
            "### Scenario by difficulty",
            "",
            "| Scenario | Easy | Medium | Hard | Total |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for scenario in ("buying", "browsing", "intent_override", "boundary"):
        lines.append(
            f"| {SCENARIO_LABELS[scenario]} | {cross_failures[scenario]['easy']} | "
            f"{cross_failures[scenario]['medium']} | {cross_failures[scenario]['hard']} | "
            f"{scenario_failures[scenario]} |"
        )
    lines.append(
        f"| **Total** | **{difficulty_failures['easy']}** | "
        f"**{difficulty_failures['medium']}** | **{difficulty_failures['hard']}** | "
        f"**{len(failures)}** |"
    )

    lines.extend([""])
    lines.extend(observable_evidence_section(failures))

    lines.extend(
        [
            "## Top three failure-class hypotheses",
            "",
            "Because all 18 failures are complete recall misses with no differentiating "
            "session-level signals (see above), these classes are **hypotheses** informed by "
            "scenario metadata and difficulty concentration. They identify where failures cluster "
            "and propose plausible mechanisms, but proving the actual internal defect requires "
            "conversation-level traces and candidate-recall logs that the evaluator result does "
            "not contain.",
            "",
        ]
    )
    ranked_taxonomy = []
    for entry in TAXONOMY:
        count = sum(scenario_failures[scenario] for scenario in entry["scenarios"])
        ranked_taxonomy.append((count, entry))
    ranked_taxonomy.sort(key=lambda item: item[0], reverse=True)
    for rank, (count, entry) in enumerate(ranked_taxonomy, start=1):
        scenarios = ", ".join(SCENARIO_LABELS[name] for name in entry["scenarios"])
        lines.extend(
            [
                f"### {rank}. {entry['name']} ({count}/18; {percentage(count, len(failures))})",
                "",
                f"Evidence slice: {scenarios}.",
                "",
                f"Hypothesis: {entry['interpretation']}",
                "",
                f"General improvement direction: {entry['direction']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitations and next steps",
            "",
            "The evaluator result records only final outcomes (`hit`, `best_rank`, "
            "`reciprocal_rank`). All 18 failures share identical signals (target never "
            "retrieved), so scenario-level aggregation is the finest granularity available. "
            "To upgrade these hypotheses into confirmed root causes, the following additional "
            "evidence is needed:",
            "",
            "1. **Conversation traces**: full dialogue turns to observe where slot-filling "
            "or clarification diverged from the user profile.",
            "2. **Candidate-recall logs**: the retrieval stage's candidate set at each turn, "
            "to separate recall failure from reranking failure.",
            "3. **Query reconstruction diffs**: for Intent Override sessions, the before/after "
            "query state to verify whether slot replacement occurred correctly.",
            "",
            "## Interpretation boundary",
            "",
            "The taxonomy is suitable for prioritizing scenario-level experiments. It must not be used "
            "to add rules keyed by public sample identifiers, ground-truth identifiers, or particular "
            "products. Any proposed retrieval or policy change should be evaluated on the full public set "
            "and an independent shadow or locked split before adoption.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    validate_commit(args.baseline_commit)
    result = load_json(args.result)
    public_records = load_jsonl_by_id(args.public_set)
    failures, scenario_failures, difficulty_failures, cross_failures = analyze(
        result, public_records
    )
    report = markdown_report(
        result_path=args.result,
        result_canonical_sha256=canonical_lf_sha256(args.result),
        public_path=args.public_set,
        public_canonical_sha256=canonical_lf_sha256(args.public_set),
        baseline_commit=args.baseline_commit,
        result=result,
        public_records=public_records,
        failures=failures,
        scenario_failures=scenario_failures,
        difficulty_failures=difficulty_failures,
        cross_failures=cross_failures,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote {args.output.as_posix()}")
    print(f"Evaluator result Canonical-LF SHA-256: {canonical_lf_sha256(args.result)}")
    print(
        "Failures: "
        + ", ".join(
            f"{SCENARIO_LABELS[scenario]}={scenario_failures[scenario]}"
            for scenario in ("buying", "browsing", "intent_override", "boundary")
        )
        + f", Total={len(failures)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
