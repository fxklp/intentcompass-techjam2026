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
