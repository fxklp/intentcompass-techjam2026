# TASK-303: Buying/Browsing dual-route in-memory retrieval

Owner: Wang Siwen
Integration owner: Team lead

## Allowed paths

- `solution/retrieval/**`
- `tests/retrieval/**`
- `experiments/retrieval/**`
- `scripts/benchmark_retrieval.py`
- `artifacts/manifests/**`
- `reports/experiments/TASK-303-*`
- `docs/team/tasks/TASK-303-dual-route-inmemory.md`

## Outcome

Run an isolated, deterministic experiment that preserves the current FTS5
candidate retriever as a fallback and compares it with explicit Buying and
Browsing in-memory candidate routes. The experiment must not change the main
Agent, shared contracts, evaluator, data, CI, dependencies, or demo.

## Constraints

- Retrieval product code must never read labels, targets, public sessions, or
  evaluator state.
- Buying prioritizes exact attributes, category fields, and price constraints.
- Browsing prioritizes category, use case, query expansion, and candidate
  diversity.
- Candidate fusion must combine genuinely different routes deterministically.
- No external vector database, runtime network service, training, multimodal
  processing, UI, LLM, or falsely labelled dense/semantic retrieval.
- Dense retrieval is not implemented in this task.

## Proof

- Baseline wrapper matches the current FTS5 candidate order on fixed fixtures.
- Route decisions and fusion evidence are available as structured traces.
- Public and deterministic shadow comparisons include overall and scenario
  metrics, candidate recall, startup time, latency, memory, and asset size.
- The experiment runs fully offline after the frozen catalog is available.
- `python scripts/team_gate.py` and every retrieval-specific test pass.

## Recommended integration thresholds

- Public HitRate@10 >= 0.91.
- Public TechnicalScore >= 0.777107.
- Shadow HitRate@10 >= 0.895.
- No unexplained material scenario regression.
- Latency, memory, and reproduction cost remain acceptable.
