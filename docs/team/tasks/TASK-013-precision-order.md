# TASK-013: research-led, pure precision ordering

Owner: lead integration Agent, local-only continuation authorized by the user.
Start at accepted TASK-011 d33c1d39ce036cb8a747779702700a56d38a1ac3. Preserve
that worktree, failed TASK-012 evidence, RC2 ZIP and remote branches. No teammate
assignment, API, secret access, new dependency, training or downloaded assets.

## Allowed paths

- This task card, `docs/team/TASK-013-RESEARCH.md`, `docs/team/TASK-013-RESULTS.md`
- `solution/adaptive.py`, `solution/precision_order.py`
- `tests/core/check_precision.py`, `tests/core/test_precision_order.py`
- Ignored `reports/generated/**`, append-only result evidence

Core-local wrappers/tests belong to the integration owner for this local task.
Do not edit official evaluator/data/contracts, retrieval modules, older tests,
release preset, submission materials, or ZIP artifacts. Copy only the identical
ignored frozen catalog, then verify protected-file hashes.

## Predeclared candidates

Reproduce the clean TASK-011 Public baseline, including exact sessions, before
runtime edits. Freeze both candidates and tests before evaluation:

1. `joined`: extract TASK-012 safe_phrase only. Require every explicit positive
   preference phrase in normalized primary catalog text and at least one
   multi-token preference. Stable-partition matching products before others
   within contiguous equal-category-evidence groups of the existing Top10.
2. `separate`: identical, except each preference phrase must occur wholly within
   one primary field (title, features, or details); different preferences may
   match different fields. Prevent synthetic phrases spanning field boundaries.

Both leave ranking untouched with explicit budget, recognized exclusions,
no positive preferences, no-match fallback or fewer than two candidates. They
preserve head membership, tail, and tie order. Reuse existing FieldEvidence and
its bounded cache, not a second index. No model, learned score, ID-specific rule,
extra data, query expansion, question changes, or terminal-policy changes.

This tests an original lexical adaptation of research principles, not a neural
paper reproduction. Source/license/rationale are in TASK-013-RESEARCH.md.

## Selection and independent confirmation

- Default initially off, exactly TASK-011. Confirm `joined` matches the frozen
  TASK-012 safe_phrase Public sessions and Shadow metrics before selection.
- Evaluate both on reused Public200 and original Shadow200; require HR/MRR
  nondecrease and MTTC nonincrease overall AND all four scenarios (1e-6), with
  a strict overall improvement. Select highest Public technical score among
  passers, prefer `separate` on exact ties for field-boundary safety.
- Write immutable selection evidence before generating either new target set.
- Run baseline and ONLY the selected candidate on TWO fresh, disjoint 800-session
  synthetic sets. Exclude Public, original Shadow, TASK-008/010/011/012 targets.
  Seeds: `intentcompass-task013-confirm-a-20260831` and
  `intentcompass-task013-confirm-b-20260831`, with B also excluding A.
- No inspection of fresh target/session records, post-confirmation tuning,
  replacement winner, or gate relaxation. Failure retains TASK-011 default.
  These are simulator-based confirmations, not official hidden scores and not
  evidence of theoretical optimality or realistic dialogue robustness.
- If both pass, permit changing only the default to the selected policy in this
  isolated worktree. Require exact metric equivalence after that change on all
  four sets, three alternating fresh-process paired timings on Public, unchanged
  original tests, full team gate, demo, source/data/allowed-path audit, zero
  attempted network connections and token usage. Never package or push here.

## Proof commands

`python -B -m tests.core.check_precision --variant NAME --split SPLIT --output
reports/generated/NEW.json` with `--baseline FILE` or `--expected FILE` where
applicable; `python -B -m unittest tests.core.test_precision_order`;
`python -B scripts/team_gate.py --full-eval`; `git diff --check`.

Tests include field boundaries, complete conjunction, exact token boundaries,
ties/categories/membership, missing fields, budget/exclusions/fallback, reset,
override, independent sessions, zero top_k and malformed configuration.
