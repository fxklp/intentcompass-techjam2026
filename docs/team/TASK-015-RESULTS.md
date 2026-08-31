# TASK-015: Final offline algorithm adopted

## Decision and version

The user's explicit acceptance changes the decision for the already-frozen
TASK-014 `title_tie+other3` combination. It is now the default offline algorithm
in this local worktree, not merely an opt-in research candidate.

- Branch: `core/TASK-015-final-algorithm`.
- Worktree: `D:/TikTok TechJam 2026/worktrees/track4-final-algorithm`.
- Runtime/tests freeze: `3d01e363b561071a7f9f4a1a97beb8b6027d9f53`.
- Previous stable baseline: `69687506ea557e9796123d10e3a619a24effb6f3` (TASK-013).
- Selected research freeze: `f597e9681fe2909d0abae4cba1f2404c48d600fa` (TASK-014).
- Default: `INTENTCOMPASS_FINAL_POLICY=on`; explicit `off` restores TASK-013.

No further tuning was performed. The old strict non-regression rejection is
preserved in TASK-014. Adoption is based on the user's scoped acceptance of
two scenario-level MRR decreases, not a retroactive claim that every metric
in every scenario improved. No theoretical optimum or hidden-set guarantee
is claimed.

## Minimal production extraction

Only `solution/adaptive.py` and new `solution/final_policy.py` change production
code relative to TASK-013. The final module is 86 lines, with 17 integration
lines in the controller. The implementation keeps:

1. Title evidence: within contiguous category/full-phrase groups in the Top 10,
   move a strict title-evidence superset past its neighbor only when their
   retrieval-rank gap is at most 3. Preserve membership, tail, ties and
   incomparable evidence; bypass on fallback, budget or recognized exclusion.
2. Clarification: after three consecutive explicit no-preference replies,
   advance the unasked `other` question once when eligible. Preserve turn,
   fallback, no-output, known/unconstrained attribute and session-reset guards.

The selected behavior reuses PrecisionOrder's lazy bounded catalog field cache.
Unused rare-term statistics and unselected lookahead/other2 research variants
were not copied. No second index, dependency, API call, training or UI was added.
The policy is only activated in the compatible existing offline pipeline.
No official data, evaluator, scoring/stopping rules, retrieval lane or adapter
contract changed. Existing tests were not weakened or rewritten.

## Exact quality reproduction

Each cell is **TASK-013 off -> adopted default**. Public is the official local
200-session set. Shadow and A/B are local synthetic diagnostic sets; A/B are
the SAME existing TASK-014 sets, not newly independent confirmation evidence.

| Set | N | HitRate@10 | MRR | MTTC (lower better) | Local recommended technical score |
|---|---:|---|---|---|---|
| Public | 200 | .975 -> .980 | .693046 -> .696861 | 4.190 -> 3.755 | .831614 -> .843958 |
| Shadow | 200 | .960 -> .965 | .698732 -> .703615 | 3.740 -> 3.545 | .834820 -> .842684 |
| TASK-014 A | 800 | .94875 -> .95625 | .694759 -> .695408 | 3.73125 -> 3.45375 | .828178 -> .837672 |
| TASK-014 B | 800 | .95125 -> .95625 | .698647 -> .698810 | 3.81875 -> 3.515 | .828844 -> .837468 |

All eight off/default runs reproduced their frozen expected aggregate AND
scenario metrics exactly, with identical target-manifest hashes. Public
per-session records also match exactly. A/B session-level records were not
exposed; these comparisons are aggregate/scenario equivalence, not proof of
identical individual dialogue trajectories on A/B.

Accepted exceptions, with no additional observed scenario regressions:

| Set / scenario | Previous MRR | Adopted MRR | Delta |
|---|---:|---:|---:|
| A / buying | .692729 | .690502 | -.002227 |
| B / intent_override | .633509 | .629838 | -.003671 |

All four overall HR/MRR/MTTC results improve. Every scenario's HR is
non-decreasing and MTTC non-increasing. These measured results are not an
official leaderboard score or a prediction of the hidden evaluation.

## Controlled runtime

Windows, Python 3.13.9; three alternating sequential fresh-process pairs,
pinned to the same first permitted CPU. No other task QA/evaluation jobs ran
concurrently during this timing phase. Each timing run also reproduced exact
Public quality, rather than measuring a simplified or different workload.
Values below are medians of three runs, except peak memory uses the maximum.

| Measure | TASK-013 off | Adopted default |
|---|---:|---:|
| Initialization | 3.467128 s | 3.242453 s |
| Response p50 | 18.6652 ms | 25.6621 ms |
| Response p95 | 96.9776 ms | 102.4571 ms |
| Response p99 | 135.3821 ms | 141.0839 ms |
| Responses for the same 200 sessions | 833 | 747 |
| Maximum whole-process peak memory | 463351808 bytes | 462934016 bytes |

The p95 increase is about 5.48 ms. Peak memory includes the evaluator and its
catalog structures, not just Agent memory. Fewer responses follow from earlier
conversion; p95 is measured over each policy's actual responses, not a fixed
identical-turn microbenchmark. Initialization/memory differences are small
measurements, not claims of architectural speed or memory improvements.

## Safety and verification

- Clean preimplementation Public baseline reproduced before runtime edits.
- 13 new final-policy unit tests; full suite: 190 tests, 189 passed, 1 skipped.
  The skip is the existing optional pinned semantic-model/assets integration
  test, not part of this offline default.
- Full team gate passed, including the unchanged local evaluator.
- Demo: `OFFICIAL HIT after intent override`, first hit turn 5, rank 8.
- Synthetic dialogue check: unique questions, `other` after the third empty
  preference reply, reset/isolation, override reset, zero K, and identical
  initial fallback/budget/exclusion payloads versus off.
- All instrumented evaluation runs: zero network attempts, zero model tokens,
  zero runtime errors, immutable source inventory and clean worktree.
- Generated evidence is UTF-8/LF and kept under ignored `reports/generated/`.

Main reproduction commands (use fresh output filenames, never overwrite proof):

```text
python -B -m unittest tests.core.test_final_policy
python -B -m unittest discover -s tests -p "test_*.py"
python -B scripts/team_gate.py --full-eval
python -B -m demo.run_demo
python -B -m tests.core.check_final_policy --variant default --split public --expected "../track4-ranking-lookahead/reports/generated/task014-title_tie+other3-public.json" --output reports/generated/my-final-public.json
python -B -m tests.core.check_final_policy --variant off --split public --expected "../track4-ranking-lookahead/reports/generated/task014-off-public.json" --output reports/generated/my-rollback-public.json
git diff --check
git status --short
```

The proof runner clears inherited experiment/API settings and blocks sockets.
For manual Agent use, set the rollback environment variable before constructing
Agent; if calling `activate_preset()`, set it AFTER that helper clears settings.

Evidence includes `task015-{default,off}-{public,shadow,confirm_a,confirm_b}.json`,
six `task015-timing-*` files, three `task015-qa-*` command records and the clean
preimplementation report. `TASK-015-MANUAL-SAFETY.json` has SHA256
`a601c20de9753b96c084993553269628a00d42eda8435b01ed9b8467f5179244`.
`TASK-015-TIMING.json` has SHA256
`de02fdaa3baf7ed6c370b85f089b4de663a57fd55b78818b34cb7dabe17fedb2`.

After this documentation commit, run `reports/generated/manage_task015.py audit`.
Its `TASK-015-FINAL-AUDIT.json` is the final machine-readable acceptance record:
require `audit_passed: true`. It validates 15 immutable proof inventories against
their Git archives, historical reference inventories, metric equivalence,
exactly the two accepted exceptions, allowed paths, hashes and preserved ZIP.
`strict_all_scenario_nonregression_pass` deliberately remains false.

## Release boundary and next step

This is the final LOCAL algorithm, not a new packaged submission. No remote
push, PR or merge was executed. Previous stable/research worktrees remain
clean. The existing RC2 ZIP is untouched, SHA256:
`5c404574c2cff1b0549a078e2b7e0484cb38c4aa1f8841370a1603a6cd246379`.

The legacy release checker still expects RC2 metrics and its release manifest;
do not use or relabel it as acceptance for this new algorithm. Next release
work must deliberately update release expectations/manifests, build a new
versioned ZIP, and obtain Windows/macOS reproduction through the team lead.
The present local Windows checks do not establish cross-platform acceptance
of the new release. Algorithm tuning stops at this adopted snapshot.
