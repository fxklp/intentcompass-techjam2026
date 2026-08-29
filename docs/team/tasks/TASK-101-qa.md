# TASK-101: evaluation and regression harness

Owner: Liu Chunyi  
Reviewer: Team lead

## Allowed paths

- `tests/**`
- `scripts/evaluate_*.py`
- `scripts/validate_*.py`
- `reports/metrics/**`

## Outcome

Produce reproducible overall/per-scenario metrics, contract tests, offline smoke
tests, and a locked-holdout process that does not leak case details to developers.

## Proof

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
```
