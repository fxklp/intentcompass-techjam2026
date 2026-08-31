# TASK-402: reproducible teammate onboarding

Owner: Integration owner
Reviewer: Liu Chunyi

## Allowed paths

- `README.md`
- `data/README.md`
- `scripts/setup_data.py`
- `tests/test_setup_data.py`
- `docs/team/tasks/TASK-402-onboarding.md`

## Outcome

A fresh clone of the private team repository must obtain the ignored 60 MB
catalog from the organizer's public `participant-kit` release, verify both the
published compressed SHA-256 and the accepted extracted SHA-256, and then run
the demo without manually copying data between teammates.

## Proof

```text
python scripts/setup_data.py
python demo/run_demo.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
```
