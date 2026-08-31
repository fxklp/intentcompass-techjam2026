# TASK-004: local final integration and bounded model comparison

Owner: team lead / integration Agent. Base: 414d6c4.
Authorization: on 2026-08-31 the team lead explicitly assigned all remaining
implementation to the local integration Agent. Wang is unavailable and receives
no task. Liu and Cheng perform only simple final reproduction after freeze.
This temporarily supersedes the lane restrictions in TASK-003 and OWNERSHIP;
no other worktree or teammate branch is changed.

## Allowed paths

- `solution/**`, preserving the official adapter signature
- `tests/core/**`, `tests/retrieval/**` (add assertions, never weaken old tests)
- `scripts/build_semantic_index.py`, `scripts/model_probe.py`
- `requirements-semantic.txt`
- `docs/decisions/ADR-0012-final-integration.md`
- this task card and `docs/team/TASK-004-RUNBOOK.md`
- ignored `artifacts/**`, `reports/generated/**`

Evaluator, data, official contracts, old experimental evidence, CI, UI, and
submission prose remain unchanged. No merge or self-approval.

## Experiment sequence, fixed before new metrics

1. Reproduce baseline (81 tests; public HR .91, MRR .624024, MTTC 4.255).
2. Exact-output speed optimization of lexical ranking.
3. Conservative core: retain proven question priority and baseline candidate
   pool; preserve executable context and workflow; evaluate on public only.
4. Real CPU semantic retrieval with frozen pretrained ONNX MiniLM and optional
   cross-encoder: controlled opt-in, never represented as LLM generation.
5. Qwen and DeepSeek: verify account free credits first; then inexpensive
   non-thinking APIs. A shared persistent ledger reserves conservative maximum
   costs BEFORE requests. Total authorization is RMB100, not per process/model.
   Unknown usage keeps its reservation; no automatic retries; no key in output.
6. Only public non-regressing finalists get a frozen Shadow aggregate check.
   Never inspect Shadow targets or retune from them. Retain a negative result.
7. Promotion requires no overall/scenario HR or MRR decline, no MTTC increase,
   and no material p95/memory regression. A tradeoff is not an improvement.
   Final speed screen: alternate three independent baseline/candidate processes
   on an otherwise idle CPU; compare median p95 with a predeclared 5% timing
   noise allowance. Peak-memory increase over 16 MiB is a separate feasibility
   review, not silently justified by quality gains. No timing verdict uses the
   runs overlapping index construction.
8. Strict judge simulation uses official rubric, not TechnicalScore as the full
   contest score. No claim of global optimality or organizer private accuracy.

## Proof commands

`python -m unittest discover -s tests -p "test_*.py"`

`python scripts/team_gate.py --full-eval`

Additional experiment commands, immutable JSON checksums, timing, model assets,
actual API usage/cost, and limitations go in the runbook after execution.

## Authorized continuation: TASK-005, quality-first API validation

On 2026-08-31 the lead accepted a revised acceptance protocol: bounded API
latency may increase, but final promotion requires HR and MRR to increase and
MTTC to decrease against the strong offline Agent, not the organizer starter.
This replaces the zero-relative-latency-regression rule for API candidates
only; historical TASK-004 failures remain failures under their original rules.
The local offline fallback remains mandatory as a team reliability choice.
The latest official submission rules allow network/API access and do not set
a standardized response timeout; the checked-in older rules are not edited.

Additional allowed path: `docs/team/TASK-005-QUALITY-FIRST.md`. All other
TASK-004 allowed paths and local-only integration authority remain in force.
No new model/dependency, teammate assignment, public data edit or evaluator edit.

Protocol frozen before TASK-005 live results:

- Baseline commit `2a039c0`, integrated/baseline/off, Public 200 reproduced.
- Qwen 3.8 Max first: existing strongest small-screen quality. Reuse verified
  Singapore pricing and SAME ledger, total cap 43.97, Qwen 20, DeepSeek 23.97.
- At most two initial variants: demand20 (20 candidates, 480-char evidence)
  and demand40 (40 candidates, 320-char evidence), non-thinking, strict indices.
  Use only current visible constraints/catalog. At least two non-category
  explicit attributes before calling; at most three attempts per session;
  exact-input last-result cache is session-local and cleared on reset.
- Screen the original fixed 12 public sessions (first three per scenario).
  Preliminary eligibility: overall/scenario no HR/MRR/MTTC regression and at
  least one overall strict gain. This is NOT full final acceptance.
- Prefer the eligible lower-cost candidate if quality is tied; expand once
  to all 200 Public sessions only if projected cost fits remaining allowance.
  A single cheaper DeepSeek Flash comparison is allowed if Max fails or
  cannot fund a full run. No loops of label-guided parameter searching.
- Only a full-Public finalist with all three strict gains gets frozen Shadow
  aggregate validation; no Shadow targets exposed to prompts or algorithm
  development. Existing Shadow is synthetic and previously used, not private.
- The API system's fallback/failed turns count in final metrics, not only
  successful calls. Record callback timings, usage, unknown costs, attempt
  coverage and paired per-session public outcomes. Three repeated confirmation
  screens if budget permits; no rerun selected merely for a better score.
- Team feasibility gates: all-response and attempted-response p95 <=3000 ms;
  parent request deadline 8 seconds; peak RSS <= baseline +64 MiB;
  no whole-run circuit suppression or exhausted budget in a promotable run.
- Per-run spending ceiling is reserved atomically in the existing ledger.
  Screens <=2 RMB each; expansion budget estimated before starting. Stop before
  provider/global ceilings, no recharge, retries, or replacement ledger.
- Any full-quality regression stops promotion; retain measured tradeoffs and
  the offline default. Do not claim a theoretical optimum or official score.

### Bounded follow-up after the two initial screens

Both initial screens completed without provider failures. demand20 has zero
quality change; demand40 improves MTTC but reduces MRR, so stop the wider-pool
direction. No parameters or historical results from either screen are changed.
Code inspection exposes a coarse gate: a single explicit feature can already
contain a detailed shopping requirement. Counting two attribute categories
unnecessarily suppresses such turns (52/75 narrow-screen responses skipped).
One final target-blind variant, demand20early, changes ONLY minimum explicit
attributes from two to one; the window, evidence text, cache and call cap stay
fixed. Test Max and, if necessary, the cheaper Flash once each (<=2 RMB/run).
No further prompt/threshold searching after these comparisons. All existing
quality gates, full-set validation and budget requirements remain unchanged.

## Authorized continuation: TASK-006 offline constraint/field ranking

The lead requested execution of the offline diagnosis and improvement proposal.
Base: `2181f9952763a01d4b6d99b1a4166a5218c77401`; no API calls or new dependencies.
Additional allowed report: `docs/team/TASK-006-OFFLINE.md`. Existing solution/
and tests/core/ permissions apply; no teammate branch is changed or tasked.

Predeclare before candidate results:

1. Reproduce baseline and diagnose all Public 200 sessions outside the Agent.
   Inspect aggregate missing-recall, below-Top10 ranking, late conversion and
   visible-constraint coverage. No target identities/text in diagnostic output.
2. First fix the narrowly demonstrated negative-preference / upper-budget
   semantics as an isolated candidate. Keep ordinary affirmative and target-
   budget behavior byte-equivalent where feasible. Unknown metadata is not a
   contradiction. Treat zero metric change as robustness-only, not score gain.
3. Field-aware reranking is a separate ablation. Use original frozen catalog
   fields via the existing in-memory index, no second index/catalog copy.
   Prefer explicit field evidence over weak keyword overlap. No grid search,
   no ASIN/session rules, no enlarging candidate pools or editing questions
   simultaneously. At most three predetermined scoring policies after diagnosis.
4. Only Public overall/scenario non-regressing candidates receive frozen
   Shadow aggregate testing. Existing Shadow is previously used, not private.
   Freeze one new synthetic evaluation seed before any new holdout results;
   use it once for final validation only, never for tuning or inspecting labels:
   `intentcompass-task006-confirmation-20260831` (200 non-public targets).
5. Promotion: Public, Shadow and new confirmation overall/scenario HR/MRR
   non-decreasing, MTTC non-increasing (1e-6 rounding tolerance). Require a
   real quality gain for score-improvement claims; separately label semantic
   correctness fixes with unchanged benchmark metrics.
6. Speed: three alternating isolated baseline/candidate runs, median p95
   within +5% and memory within +16 MiB; keep cold start separate. No API
   latency relaxation is applied to this offline stage. Preserve raw failures.
7. Stop any quality-regressing direction rather than tune to Shadow. Keep
   baseline if no reliable score gain. All unit/gate/demo checks and exact
   diff/source/data audits are required before a local handoff; no push/merge.

After baseline diagnosis, freeze these field policies before their results:
F1 `field_bonus`: baseline score plus 3 times fraction of explicit phrases
found in title/features/details (budget excluded). F2 `field_groups`: number
of fully evidenced explicit attribute groups first, baseline score second.
F3 `field_top10`: F2 within the baseline Top10 only, preserving membership and
all subsequent candidate order. No tuning of weights or limits after results.
Use a rowid directory and bounded 256-product field cache over the EXISTING
SQLite FTS table, not another catalog/index; clear it on close. Added RAM is
expected to be a few MiB and must pass the declared measured allowance.

### Bounded structural follow-up (Public only, before holdout)

F1/F2 regress quality; F3 improves overall MRR but Buying MRR declines by
0.000049 and latency rises. All three remain rejected, thresholds unchanged.
Whole-attribute counts can trade away partially satisfied constraints. One
additional non-parametric policy, F4 `field_dominance`, instead permits only
adjacent Top10 swaps where the later product's primary-field evidence is a
strict superset of the earlier product's evidence for EVERY explicit phrase.
Incomparable/equal evidence preserves baseline order. This is not a scenario
switch or tuned weight; no labels enter it. Fetch fields for Top10 only, since
the rest cannot move. Verify constructive dominance/non-dominance tests first.
If F4 fails any quality gate, stop field ranking; do not search more policies.

F4 has now failed the same Buying MRR gate as F3. Field-ranking exploration
is stopped; no field variant gets Shadow or confirmation evaluation. Only
the isolated constraints candidate remains for robustness-only validation.
For its three timing pairs, use sequential fresh processes without CPU pinning,
in baseline/candidate order each pair, with no other task benchmark in parallel.
No rerun-selection or tolerance change after those measurements.
Timing baseline loads the original ranker and controller from commit 2181f99
in its child process; record their hashes, leaving the worktree untouched.
This charges candidate hot-path overhead against the actual pre-task code,
not only against another policy inside the newly expanded ranker.

Final TASK-006 decision: F1-F4 remain disabled; constraints passes all three
quality sets without any metric change, three timing pairs and full regression.
Promote constraints ONLY as a correctness fix in default integrated mode.
Baseline/adaptive mode defaults remain unchanged. No score-gain claim or
further tuning. See docs/team/TASK-006-OFFLINE.md for raw hashes and limitations.
