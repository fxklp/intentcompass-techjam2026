# TASK-406: reproducible non-public-target shadow gate

Owner: Liu Chunyi
Reviewer: Integration owner

## Allowed paths

- `scripts/shadow_evaluator.py`
- `tests/test_shadow_evaluator.py`
- `.github/workflows/team-gate.yml`
- `reports/metrics/first-version-shadow.json`
- `docs/submission/first-version-report.md`
- `docs/submission/first-demo-evidence.md`
- `docs/submission/demo-script-3min.md`
- `docs/team/tasks/TASK-406-shadow-gate.md`

## Outcome

Replace the deleted one-off robustness script with a deterministic evaluator
over 200 catalog targets that do not overlap any public target. Use the unchanged
official simulator and exact 80/80/30/10 scenario mix. Record a digest rather
than exposing the target list, fail below HitRate@10 0.70, and retain generated
evidence in CI.

## Proof

```text
python scripts/shadow_evaluator.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
```
