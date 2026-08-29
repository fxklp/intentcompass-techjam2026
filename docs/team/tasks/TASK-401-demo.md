# TASK-401: deterministic first demo

Owner: Cheng Xianyun
Reviewer: Liu Chunyi

## Allowed paths

- `demo/**`
- `tests/test_repeatable_demo.py`
- `docs/submission/**`
- `docs/team/tasks/TASK-401-demo.md`

## Outcome

Provide one command that runs a labeled public Intent Override session through
the real Agent and official deterministic simulator. Show each customer message,
active state, selected clarification, Top 10, and target rank. The harness may
know the public target for display/scoring, but the Agent must receive only the
official profile and customer messages.

Acceptance also requires proving that the old preference is absent and the new
preference is present in active state after the correction.

## Proof

```text
python demo/run_demo.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
```
