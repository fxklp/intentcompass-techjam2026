# TASK-405: runtime and disclosure evidence

Owner: Liu Chunyi
Reviewer: Cheng Xianyun

## Allowed paths

- `scripts/benchmark_runtime.py`
- `tests/test_runtime_benchmark.py`
- `tests/test_team_gate.py`
- `scripts/team_gate.py`
- `.github/workflows/team-gate.yml`
- `docs/submission/first-version-report.md`
- `docs/team/tasks/TASK-405-runtime-evidence.md`

## Outcome

Generate reproducible latency evidence around the real Agent and unchanged
official evaluator, including commit, Python/platform, workload, initialization,
mean/p50/p95/p99/max response latency, score, token use, and network requirement.
Document model choice, cost, offline behavior, limitations, and only actually
accepted team contributions.

## Proof

```text
python scripts/benchmark_runtime.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
```
