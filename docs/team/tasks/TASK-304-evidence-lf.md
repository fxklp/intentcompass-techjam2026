# TASK-304: Evidence LF consistency

Owner: Wang Siwen
Integration owner: Team lead

## Allowed paths

- `artifacts/manifests/TASK-303-dual-route-inmemory.json`
- `experiments/retrieval/evaluate.py`
- `scripts/benchmark_retrieval.py`
- `tests/retrieval/test_manifest.py`
- `tests/retrieval/test_benchmark.py`
- `reports/experiments/TASK-303-summary.md`
- `docs/team/tasks/TASK-304-evidence-lf.md`

## Outcome

Make TASK-303 evidence hashes portable by defining them over the committed raw
UTF-8 LF bytes, and prevent either generator from emitting platform-dependent
newlines. Preserve the original experiment commit, JSON evidence, and metrics.

## Constraints

- Do not change the retrieval algorithm, Agent, evaluator, data, CI, or metrics.
- Do not rewrite the checked-in TASK-303 result or benchmark JSON.
- Do not normalize unrelated repository files or rerun the four experiment
  combinations.

## Proof

- Recompute both SHA-256 values directly from the committed evidence bytes.
- Verify both evidence files are UTF-8, LF-terminated, and exactly match their
  manifest hashes.
- Prove that changing an evidence byte causes validation to fail.
- Exercise both JSON generators with lightweight fixtures and verify their
  output parses and contains no CRLF.
- Run all tests and `python scripts/team_gate.py`.
