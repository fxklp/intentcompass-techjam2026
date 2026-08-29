# Track 4 ownership and assignments

The team uses one integration owner and three non-overlapping implementation
lanes. Each task should fit in a 2-4 hour branch; unfinished work is handed off
as a branch plus manifest, never as loose files.

## Team lead + dedicated automation Agent: core algorithm and integration

**Outcome:** deliver a valid offline Agent with structured state, override
replacement, clarification policy, reranking, and a thin official adapter.

**Owns:**

- `starter/agent.py`
- `solution/contracts.py`
- `solution/state.py`
- `solution/question_policy.py`
- `solution/ranker.py`
- `solution/agent_impl.py`
- `solution/config.py`
- `docs/contracts/**`
- `docs/decisions/**`

**Must produce:** contract tests, baseline metric, new metric, scenario breakdown,
known limitations, and an offline run.

**Must not do:** advanced retrieval owned by Wang, evaluator changes, video/UI,
or rules tuned from locked holdout labels.

## Liu Chunyi: QA, evaluator wrapper, and regression evidence

**Outcome:** make every claim falsifiable and prevent public-set overfitting or
interface breakage.

**Owns:**

- `tests/**`
- `scripts/evaluate_*.py`
- `scripts/validate_*.py`
- `reports/metrics/**`

**First tasks:**

1. Reproduce the official baseline from an untouched commit.
2. Create deterministic development/locked-holdout manifests without exposing
   locked target details to the algorithm lane.
3. Add tests for reset/respond schema, unique valid Top 10 IDs, intent override,
   boundary/no-preference, offline mode, timeout, and repeated questions.
4. Produce comparison JSON containing overall and per-scenario metrics, latency,
   commit SHA, command, and environment.

**Must not do:** edit `solution/**`, `starter/agent.py`, official evaluator,
public labels, or relax tests to accept an implementation bug.

## Cheng Xianyun: experiment analysis, documentation, and demo

**Outcome:** turn measured behavior into a credible product story and a
reproducible submission.

**Owns:**

- `analysis/**`
- `docs/submission/**`
- `demo/**`
- `reports/analysis/**`

**First tasks:**

1. Analyse baseline result JSON by Buying, Browsing, Intent Override, and
   Boundary; classify failure modes without creating target-specific rules.
2. Maintain the experiment ledger: hypothesis, commit, config, command, metrics,
   conclusion, decision.
3. Select one demonstrable session only after it is reproducible from code.
4. Draft the three-minute script, architecture figure, limitations, cost and
   team-contribution sections.

**Must not do:** type metrics manually, claim results without result JSON, edit
core/retrieval/evaluator code, or build a UI before the algorithm freeze.

## Wang Siwen: candidate retrieval and runtime engineering

**Outcome:** improve target recall with a reproducible, efficient retrieval
component that obeys the shared protocol.

**Owns:**

- `solution/retrieval/**`
- `scripts/build_index.py`
- `artifacts/manifests/**`
- retrieval-specific tests under `tests/retrieval/**` in coordination with Liu

**First tasks:**

1. Wrap the official BM25 behavior behind `CandidateRetriever` without changing
   its output on a fixed smoke fixture.
2. Add field-aware/hybrid candidate generation as an isolated experiment.
3. Record index build command, source catalog checksum, artifact checksum,
   build time, load time, peak memory, and retrieval latency.
4. Return retrieval evidence needed by reranking without deciding state or
   clarification policy.

**Must not do:** edit `starter/agent.py`, core state/ranker/question policy,
official evaluator, or commit a large generated index directly.

## Integration authority

- The team lead accepts or rejects contract changes and merges branches.
- Liu Chunyi can block a merge for failed or missing evidence.
- No author approves their own branch.
- `main` must remain runnable; experimental branches may fail but cannot be used
  as a handoff source without an explicit failure note.
