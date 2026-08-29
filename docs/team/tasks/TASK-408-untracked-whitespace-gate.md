# TASK-408: close the untracked whitespace gate gap

Owner: Integration owner
Reviewer: Liu Chunyi

## Allowed paths

- `docs/submission/P0_P1_ACCEPTANCE_AUDIT.md`
- `scripts/team_gate.py`
- `tests/test_team_gate.py`
- `docs/team/tasks/TASK-408-untracked-whitespace-gate.md`

## Outcome

Remove the two Markdown trailing-space line breaks that failed the first Linux
CI run. Extend the local gate to scan every changed or untracked text file for
trailing spaces/tabs, because `git diff --check` cannot inspect an untracked
file before its first commit.

## Proof

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
```

The pull request must pass the remote `full-evaluator` job before merge.
