# TASK-203: V2 submission storyboard

Owner: Cheng Xianyun

Status: reviewer-requested documentation correction for PR #7. Prepare and
verify the revision locally. Do not push it until explicit local approval; after
an approved branch update, wait for independent review.

## Baseline and branch

- Required base: `a81b042d3010fb254519ab56573d03beba111396`
- Local branch: `submission/TASK-203-v2-storyboard`
- The automated Python Agent and headless evaluator are the only execution path
  covered by this task.
- The architecture figure describes the current implementation at the required
  base, not unimplemented target architecture.

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
official metrics, feasibility, limitations, and merged team contributions. It
must distinguish official requirements, team policies, and current
implementation; retain the narration; and prepare exact subtitle text, capture
actions, and required assets without recording or uploading media.

## Deliverables

1. `requirements-matrix.md` separates official requirements, team policies, and
   current implementation, then maps them to evidence and video shots.
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
- The architecture diagram contains only the implemented state update, lexical
  query, SQLite FTS5/BM25 retrieval, lexical constraint rerank, deterministic
  clarification, and Top 10 response path. It contains no routing node.
- Buying/Browsing routing, dual-route retrieval, dense retrieval, hybrid
  retrieval, and semantic reranking are marked `Not implemented`.
- Dynamic clarification and aggregate-profile personalization are marked
  `Partial` with their exact current boundaries.
- The Intent Override segment shows the old state disappearing, the new state
  becoming active, all ten recommendation identifiers, and the eligible hit.
- Every numeric or functional statement cites a repository file and commit.
- Reference-machine latency is labeled as machine-specific.
- TechnicalScore is identified as an objective input to Technical Execution,
  not the competition's final overall score.
- Public and shadow metrics are not presented as private-set guarantees.
- Contribution narration credits Fang Tianchen with the accepted initial
  end-to-end Agent and demo baseline, accurately labels its public result as
  HR@10 `0.91`, and names Wang Siwen (backend/retrieval) and Liu Chunyi and
  Cheng Xianyun (testing/demo production). It distinguishes the founding
  baseline, current roles, and later completed contributions. Supporting PR
  numbers, SHAs, and open/merged status appear only in the evidence ledger;
  open PR #6 and PR #8 are not credited as completed work.
- The displayed test count comes from the final submission commit rather than a
  number fixed during storyboard drafting.
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

Also search the six files for prohibited interface-oriented scope terms,
unsupported score, performance, cost, feature, or contribution statements, and
architecture nodes that are absent from the current implementation.

## Upload gate

After local approval, push only the existing task branch to update PR #7. Do not
create another pull request, assign a reviewer, merge, or contact teammates.
After the approved update, wait for independent review.
