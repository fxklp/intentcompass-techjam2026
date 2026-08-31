# TASK-403: deterministic resource lifecycle

Owner: Core automation Agent
Reviewer: Liu Chunyi

## Allowed paths

- `solution/agent_impl.py`
- `starter/agent.py`
- `tests/core/test_agent.py`
- `scripts/team_gate.py`
- `docs/team/tasks/TASK-403-resource-lifecycle.md`

## Outcome

The in-memory SQLite FTS index must close deterministically when requested and
automatically when an Agent is discarded. Closing twice must be safe. The team
gate must surface `ResourceWarning` output as a failure instead of allowing a
green result with hidden resource debt.

## Proof

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
python scripts/team_gate.py --full-eval
```
