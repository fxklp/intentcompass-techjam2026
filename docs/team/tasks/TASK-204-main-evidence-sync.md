# TASK-204: Synchronize V2 materials to accepted main

Owner: Cheng Xianyun

Status: PR #10 submitted, pending documentation fix and independent review,
not merged.

## Baseline and branch

- Required base: `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`
- Local branch: `submission/TASK-204-main-evidence-sync`
- PR #6, #7, #8, and #9 are merged into the required base.
- This task updates submission evidence only. It does not activate retrieval
  experiments or change the formal Agent.

## Allowed paths

- `docs/submission/v2/requirements-matrix.md`
- `docs/submission/v2/storyboard-3min.md`
- `docs/submission/v2/shot-list.md`
- `docs/submission/v2/asset-checklist.md`
- `docs/submission/v2/claim-evidence-ledger.md`
- `docs/team/tasks/TASK-204-main-evidence-sync.md`

No source, tests, evaluator, data, frozen result JSON, manifest, CI, root
configuration, demo program, or existing task card may be modified.

## Outcome

Synchronize the reviewed V2 production plan with accepted main while preserving
a truthful boundary between the formal Agent and merged isolated retrieval
experiments. Update merged contribution evidence, reproduce the current Demo
and full gate, retain historical measurements with their original provenance,
and leave every unproduced media asset `Pending`.

## Accepted-main facts

- PR #6 cross-platform head
  `35927230574ddbf983f66aa6f54f897dec157d99` merged as
  `ce87a192964c6a10fcb9f2a3239bb48c7653789f`.
- PR #7 V2 materials head
  `89293876231e21ebeca9c112ccfd19ce00a3a939` merged as
  `ceea73f219c5082e968c2ab99e4c7465d2457690`.
- PR #8 isolated retrieval head
  `8003f8077d5357800a8d8738bde83087035c3fa0` merged as
  `970f0b754bba06f93b889e1b87f4ee9174e43ecb`.
- PR #9 evidence-fix head
  `ae5589ef66024dbe562de456783f1d159e8ec64f` merged as the required base
  `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`.
- The formal path still delegates from `starter.agent.Agent` to
  `solution.agent_impl.Agent`, which directly uses `_BaselineBM25Index`.
- Buying/Browsing dual-route lexical code is merged under the isolated
  retrieval and experiment paths but is not imported or enabled by the formal
  Agent.

## Deliverables

1. The requirements matrix separates official requirements, team policies,
   formal-Agent state, and isolated-experiment state.
2. The storyboard retains the exact 180-second headless story and narration,
   using only the formal path in its architecture.
3. The shot list defines real CLI captures, a historical-runtime evidence
   display, and an isolated-experiment decision card.
4. The asset checklist keeps all unrecorded and unproduced media items
   `Pending`.
5. The claim ledger records PR #6-#9 heads, merge commits, contribution
   evidence, historical measurements, and formal/experiment claim boundaries.
6. This task card records the base, scope, reproduction, and upload gate.

## Local reproduction on accepted main

Environment and code state used before the documentation-only edit:

- Platform: Windows
- Python: 3.12.13
- SHA: `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`
- Tracked worktree before reproduction: clean

Observed results:

- `python demo/run_demo.py`: `public_0183`; the first score-eligible hit occurs
  on turn 5 at rank 8; turns 1-3 remain unscored before the override.
- `python scripts/team_gate.py --full-eval`: 49 tests pass; 200 public sessions;
  HR@10 `0.91`; MRR `0.624024`; MTTC `4.255`; Efficiency `0.6745`;
  TechnicalScore `0.777107`; zero reported model tokens; `TEAM GATE PASSED`.

These current reproduction results do not remeasure historical latency. The
runtime values in `reports/metrics/first-version-runtime.json` remain tied to
code commit `424781522f52e9c1ef1c814ca8dc64eaf24cfead` and its recorded
Windows 11/Python 3.13.9 environment.

## Acceptance criteria

- Only the six allowed paths differ from the required base.
- The formal architecture contains no Buying/Browsing route or dual-route
  retrieval node.
- The merged dual-route lexical experiment is acknowledged as implemented and
  isolated, not absent from the repository and not enabled in the formal Agent.
- Dense retrieval, hybrid lexical-dense retrieval, semantic reranking, deep
  personalization, and learned/value-based clarification are not overstated.
- Current 49-test, Demo, and full-gate results match actual reproduction.
- TechnicalScore is not presented as the final competition score.
- Shadow and isolated experiment results are not presented as official private
  evaluation or deployed Agent performance.
- Historical latency retains its original commit, environment, and method.
- Contributions reflect accepted or merged evidence for Fang Tianchen, Liu
  Chunyi, Wang Siwen, and Cheng Xianyun.
- No media is recorded or uploaded; every unproduced production asset remains
  `Pending`.

## Proof commands

Run from the repository root with the existing project interpreter:

```text
python demo/run_demo.py
python scripts/team_gate.py --full-eval
git diff --check
git diff --name-only 5bd5d6fac91aad718862baded99eaf8b21cdd2bf...HEAD
git status --short
```

Also verify every PR/SHA anchor resolves, storyboard timing totals 180 seconds,
all O/I/E/C references resolve, and the six files contain no unsupported formal
capability, current-performance, private-result, or completed-media claim.

## Upload gate

Upload completed. PR #10 has been created on branch
`submission/TASK-204-main-evidence-sync`. Pending documentation fix and
independent review. Do not create a second PR, force-push, assign a reviewer,
contact Liu or Wang, or merge.
