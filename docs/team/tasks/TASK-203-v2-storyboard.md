# TASK-203: V2 submission storyboard

Owner: Cheng Xianyun

Status: local documentation work. Do not push or open a pull request until the
local result receives explicit approval.

## Baseline and branch

- Required base: `a81b042d3010fb254519ab56573d03beba111396`
- Local branch: `submission/TASK-203-v2-storyboard`
- The automated Python Agent and headless evaluator are the only execution path
  covered by this task.

## Allowed paths

- `docs/submission/v2/requirements-matrix.md`
- `docs/submission/v2/storyboard-3min.md`
- `docs/submission/v2/shot-list.md`
- `docs/submission/v2/asset-checklist.md`
- `docs/submission/v2/claim-evidence-ledger.md`
- `docs/team/tasks/TASK-203-v2-storyboard.md`

No code, evaluator, data, existing submission document, or other task card may
be modified.

## Outcome

Produce a truthful, evidence-linked production plan for a three-minute video.
The plan must connect each official requirement to a repository artifact and a
specific shot. It must cover the problem, solution, real multi-turn Agent run,
official metrics, feasibility, limitations, and merged team contributions, and prepare
exact narration, subtitle text, capture actions, and required assets without
recording or uploading media.

## Deliverables

1. `requirements-matrix.md` is the official-requirement, repository-evidence,
   and video-shot crosswalk.
2. `storyboard-3min.md` contains the exact 180-second narrative, picture plan,
   voice-over, subtitles, and evidence anchors.
3. `shot-list.md` defines each real terminal capture and its rejection rules.
4. `asset-checklist.md` separates available evidence from production items that
   remain Pending.
5. `claim-evidence-ledger.md` bounds every functional, metric, performance,
   cost, limitation, and contribution statement.
6. This task card freezes the scope, allowed files, proof commands, and upload
   gate.

## Acceptance criteria

- The story uses real commands and outputs from `Agent.reset/respond`,
  `demo/run_demo.py`, the full evaluator, and the runtime benchmark.
- The Intent Override segment shows the old state disappearing, the new state
  becoming active, all ten recommendation identifiers, and the eligible hit.
- Every numeric or functional statement cites a repository file and commit.
- Reference-machine latency is labeled as machine-specific.
- Public and shadow metrics are not presented as private-set guarantees.
- Team credit is limited to merged PR #1, #2, #4, and #5 at the required base.
- No mock output, retyped terminal result, or prepared image is used as proof of
  an executed capability.
- Only the six allowed files are added.
- Recording, upload, review assignment, and merge are not performed in the
  local phase.

## Proof commands

Use a Python 3.10+ interpreter from the repository root:

```text
python demo/run_demo.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python scripts/benchmark_runtime.py
git diff --check
git diff --name-status a81b042d3010fb254519ab56573d03beba111396...HEAD
git status --short
```

Also search the six new files for prohibited interface-oriented scope terms and
for unsupported score, performance, cost, feature, or contribution statements.

## Upload gate

After local approval, commit the six files, push only the task branch, and open
one pull request. Leave it open with no review assignment and do not merge or
contact teammates. Until that approval, the expected remote PR and remote commit
SHA are `Pending`.
