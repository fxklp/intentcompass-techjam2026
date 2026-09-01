# TASK-307: Final non-video submission materials

## Objective

Make the frozen TASK-306 implementation understandable and reproducible from the
public repository and prepare truthful, copy-ready English Devpost materials.
This task changes documentation only; it does not alter the Agent, evaluator,
official data, scoring, semantic assets, prompts or algorithm configuration.

## Allowed paths

- `README.md`
- `requirements.txt` (comments only; no dependency change)
- `docs/release/METHOD.md` (historical banner only)
- `docs/release/REQUIREMENTS.md` (historical banner only)
- `docs/release/VIDEO-HANDOFF.md` (historical banner only)
- `docs/submission/**`
- `docs/team/tasks/TASK-307-final-deliverables.md`

## Required outputs

1. A final English README with exact setup, fallback and evaluation boundaries.
2. A short final report covering architecture, models, cost, latency,
   limitations and team contributions.
3. A copy-ready Devpost description listing tools, APIs, assets and libraries.
4. Judge-facing testing instructions and third-party notices.
5. A checklist separating completed evidence from user-owned/publication steps.
6. Clear warnings on superseded RC3/TASK-203 submission drafts.

## Proof

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
python demo/run_demo.py
git diff --check
git status --short
```

Run a secret-pattern scan and confirm the diff is limited to the allowed paths.
Do not publish, upload, change repository visibility or submit Devpost from this
task.
