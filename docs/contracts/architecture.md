# IntentCompass architecture contract

Status: **frozen for parallel implementation**  
Contract owner: Team lead / integration Agent

## Product statement

IntentCompass is a multi-turn shopping Agent that maintains replaceable active
preferences, asks only high-value clarification questions, and returns its best
current Top 10 on every turn.

## Pipeline

```text
reset(profile)
  -> SessionState

respond(message)
  -> state update / override replacement
  -> buying-vs-browsing route
  -> CandidateRetriever.search(query, limit)
  -> constraint-aware rerank
  -> clarification-value policy
  -> natural message + ask_attribute + ordered parent_asin values
```

## Stable boundaries

### Official adapter

- File: `starter/agent.py`
- Owner: integration owner only
- Responsibility: expose the official `Agent` class and delegate to
  `solution.agent_impl.Agent`.
- It must not contain retrieval, state, ranking, or clarification logic.

### Core and policy

- Paths: `solution/contracts.py`, `solution/state.py`,
  `solution/question_policy.py`, `solution/ranker.py`,
  `solution/agent_impl.py`
- Owner: team-lead automation Agent
- Responsibility: shared types, session state, override semantics, question
  selection, reranking, orchestration, and offline fallback.

### Candidate retrieval

- Path: `solution/retrieval/**`
- Owner: Wang Siwen
- Contract: return catalog-valid candidates and retrieval evidence; do not
  decide conversational state or `ask_attribute`.

```python
class CandidateRetriever(Protocol):
    def search(self, request: RetrievalRequest) -> list[Candidate]: ...
```

The core will define `RetrievalRequest` and `Candidate`. Retrieval must not read
public targets or evaluator state.

### Evaluation and regression

- Paths: `tests/**`, `scripts/evaluate_*.py`, `reports/metrics/**`
- Owner: Liu Chunyi
- Responsibility: contract tests, scenario regressions, locked holdout process,
  metric comparison, latency and offline smoke tests.
- Evaluation code may import the Agent but may never change product code or the
  official evaluator during a test run.

### Analysis and submission evidence

- Paths: `analysis/**`, `docs/submission/**`, `demo/**`
- Owner: Cheng Xianyun
- Responsibility: failure taxonomy, experiment summaries, verified claims,
  demo script, diagrams, and submission drafts.
- Reports must cite an immutable result JSON and commit SHA. No manually typed
  metric is treated as evidence.

## State semantics

- State is keyed by `session_id` and cleared/replaced by `reset`.
- Active preferences are structured slots, not an ever-growing prompt string.
- A later explicit correction replaces the old value; it does not append a
  contradictory value.
- `no preference` clears or marks a slot unconstrained and prevents repeated
  questioning of that slot.
- Price is a soft preference when catalog price is absent or inconsistent.

## Recommendation semantics

- Every turn should return the best available recommendations, even when asking
  a clarification question.
- Outputs are ordered best to worst; duplicate and invalid IDs are forbidden.
- Numeric internal scores are implementation details. Official correctness is
  exact `parent_asin` equality.
- Offline deterministic behavior is the reference path. Optional LLM behavior
  must fail closed to that path without breaking the response schema.

## Contract-change procedure

1. Add `docs/decisions/ADR-XXXX-short-name.md` containing context, proposed
   change, affected owners, migration, tests, and rollback.
2. Obtain approval from the integration owner and every affected owner.
3. Merge contract plus failing acceptance tests first.
4. Rebase all affected branches before implementation continues.

Chat messages and generated code do not change this contract.
