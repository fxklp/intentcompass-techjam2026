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
