# TASK-407: P0/P1 completion audit

Owner: Integration owner
Reviewer: Liu Chunyi

## Allowed paths

- `docs/submission/P0_P1_ACCEPTANCE_AUDIT.md`
- `docs/team/tasks/TASK-407-acceptance-audit.md`

## Outcome

Map every P0 and P1 requirement to current authoritative evidence, distinguish
local first-version acceptance from unfinished remote/P2 work, and avoid using
plans, old chat claims, or unrepeatable results as proof.

## Proof

```text
python scripts/setup_data.py
python scripts/team_gate.py --full-eval
python scripts/benchmark_runtime.py
python scripts/shadow_evaluator.py
python demo/run_demo.py
```
