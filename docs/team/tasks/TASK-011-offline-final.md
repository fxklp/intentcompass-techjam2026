# TASK-011: extract terminal recovery and test final-turn guard

Owner: lead integration Agent, local-only under the user's offline optimization
instruction. No teammate dispatch, API calls, new dependencies or remote writes.

## Allowed paths

- This task card; `docs/team/TASK-011-RESULTS.md`
- `solution/adaptive.py`, `solution/terminal_recovery.py`
- `tests/core/check_terminal.py`, `tests/core/test_terminal_recovery.py`
- Ignored `reports/generated/**`

Official evaluator/data/contracts, retrieval ownership files and RC2 untouched.

## Frozen input

RC2 10f899a2c205fed8386a84d8a44f06f57dc28199. TASK-010 policy freeze a5e496f.
The terminal-only ngram policy passed Public and original Shadow all-metric and
all-scenario gates; its separate fresh 800 confirmation is in progress. No
TASK-010 frozen policy will be altered or its results overwritten.

## Independent boundary hypothesis

Test exactly two extracted modes: `terminal` reproduces TASK-010 late_ngram;
`lastchance` additionally allows recovery at turn >=10 only when active intent
is unchanged, the new baseline output exactly equals the actually shown prior
output, and the user says no additional preference or rejects the options.
Never treat a new preference, override, reset, different output, empty prior
output, or no-match popularity fallback as this condition. This is a new
protocol-boundary hypothesis, not retuning from Shadow sample records.

Only the final turn is added: it cannot introduce an earlier low-rank hit at
the expense of a later high-rank conversion. Normal explicit terminal rejection
recovery keeps its original priority. Non-regression remains empirical and
must include exact preservation of previously successful Public sessions.

## Engineering and validation

Extract only the selected lexical feature score and session-local recovery.
Do not ship the failed RankNet model, its training code or experiment modes.
Compute primary-field evidence lazily; keep normal retrieval pool at 50, expand
to 200 only when recovery can be relevant. Respect actual top_k in shown history.
Reject malformed configuration; reset clears all per-session rejection state.

1. Require exact Public sessions and aggregate Shadow/TASK-010 confirmation
   equivalence for `terminal` against the frozen research policy.
2. Freeze `lastchance` before its Public and original Shadow evaluation; require
   HR/MRR nondecrease and MTTC nonincrease overall and in all four scenarios
   against both RC2 and terminal; do not tune after results.
3. If qualified, evaluate once on another fresh 800 synthetic sessions excluding
   Public, original Shadow, TASK-008 and TASK-010 confirmation targets.
4. Final exact default equivalence, three alternating timing pairs vs RC2,
   normal/override/reset/fallback/zero-top_k tests, full team gate, source and
   protected-file audit. Do not claim an official hidden-set score or theoretical
   global optimum. Preserve RC2; no release ZIP replacement in this task.

Reproduction commands use `python -B -m tests.core.check_terminal` and
`python -B scripts/team_gate.py --full-eval`; outputs are append-only JSON with
commit/source/data hashes, network blocking, timings and memory.

Source rationale: the same original catalog n-gram feature implementation and
negative-feedback idea recorded in TASK-010, informed by ProductAgent,
ConvPS and conversational product-search negative-feedback literature. No
third-party code/model, new training, external corpus, fee or license asset.
