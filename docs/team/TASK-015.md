# TASK-015: Adopt the explicitly accepted final offline policy

## Authorization and decision

The user said: "我觉得可以接受，最终版算法就用新方案吧。"
Adopt exactly TASK-014 `title_tie+other3`, frozen at
`f597e9681fe2909d0abae4cba1f2404c48d600fa`, as the default offline policy.
Start from TASK-013 `69687506ea557e9796123d10e3a619a24effb6f3`.

This explicitly accepts two measured scenario MRR decreases:
- TASK-014 confirmation A, buying: 0.692729 -> 0.690502.
- TASK-014 confirmation B, intent_override: 0.633509 -> 0.629838.

This is a scoped user tradeoff decision, NOT a pass under the previous strict
all-scenario non-regression rule. Preserve the historical TASK-014 rejection.
No further tuning or additional regressions are authorized by this decision.

## Ownership and allowed paths

Core owner implements locally; no teammate assignment, remote push or merge.
Only these paths may change relative to TASK-013:
- `docs/team/TASK-015.md`
- `docs/team/TASK-015-RESULTS.md`
- `solution/adaptive.py`
- `solution/final_policy.py`
- `tests/core/test_final_policy.py`
- `tests/core/check_final_policy.py`
- ignored `reports/generated/` evidence and bounded audit helpers

Do not modify evaluator, official data, scoring/stop rules, retrieval lane,
adapter contracts, existing tests, API credentials, or previous releases.
Runtime uses only observable dialogue and catalog text; no target/sample rules,
new dependency, network call, model training, external index or UI.

## Implementation

Extract only the selected title-evidence strict-superset tie break and the
three-consecutive-no-preference question rule. Preserve guards and integration
order. Reuse PrecisionOrder's existing lazy field cache, not a second index.
Default `INTENTCOMPASS_FINAL_POLICY=on`; `off` restores TASK-013 behavior.
The final policy applies only to the established compatible offline pipeline.
Remove unselected research algorithms by not copying them into this branch.

## Acceptance and evidence

1. Reproduce clean TASK-013 Public baseline before implementation.
2. Freeze code/tests; reproduce TASK-014 selected results on Public, Shadow,
   and the SAME two existing TASK-014 confirmation sets. These are extraction
   reproduction checks, NOT new independent confirmation datasets.
3. Require exact aggregate/scenario metrics and Public session equivalence;
   compare split manifests; validate default-on and explicit-off rollback.
4. Preserve network blocking, response validation, immutable source inventory,
   source/data hashes, clean worktree evidence and accepted regression labels.
5. Run regression suite, full team gate, demo, and three alternating fresh
   paired Public timing runs pinned to the same CPU. Do not overlap benchmarks.
6. Audit allowed paths and frozen evidence; report exact local final commit.

Existing ZIP and GitHub state remain unchanged. This task establishes the final
local algorithm, not a newly packaged/independently release-tested submission.
