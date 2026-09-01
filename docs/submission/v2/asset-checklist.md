# V2 production asset checklist

> **Superseded TASK-203 checklist.** Do not use it as the final production state.

Status: reviewer-requested local checklist revision for PR #7. It inventories
what exists and what must be produced after independent review. No media has
been recorded or uploaded.

## Repository evidence available now

| Asset or source | Purpose | Evidence anchor | Status |
|---|---|---|---|
| `docs/competition_specification.md` and `docs/submission_rules.md` | Official objective, protocol, deliverables, and execution constraints. | `34078351e1c3615e5505a2e829600b56a542e462` and `2a6cc8e776da66ce69b1cbd237838fbc43f32587` | Ready |
| `solution/agent_impl.py`, `solution/state.py`, `solution/ranker.py`, and `solution/question_policy.py` | Source of truth for the current implementation diagram. | TASK-203 base `a81b042d3010fb254519ab56573d03beba111396` | Ready as source |
| `demo/run_demo.py` | Real multi-turn Intent Override run with per-turn state and Top 10. | `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`, merged in PR #5 at `a81b042d3010fb254519ab56573d03beba111396` | Ready to record |
| `reports/metrics/first-version-runtime.json` | Accepted public metrics, latency, token, network, workload, and environment evidence. | measured commit `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Ready |
| `reports/metrics/first-version-shadow.json` | Robustness evidence with zero public-target overlap. It is not an official score and is not required in the core 180-second cut. | measured commit `4ea2cff794318baa5e05ab77e089f2997edbc3cc`, evidence commit `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad` | Reserve only |
| `reports/analysis/TASK-201-failure-taxonomy.md` | Evidence-based failure categories and interpretation limits. | `cac52211e4d0eea13c27512689a4e59d13acc86b`, merged in PR #4 at `184ef33a9cf686b5ef55bc60d6d0b223d762d666` | Ready |
| `docs/submission/v2/claim-evidence-ledger.md` | Single source of truth for team names, current responsibilities, merged contributions, open-PR boundaries, and merge SHAs. | Team-role and contribution-evidence section; remote status checked 2026-08-30 | Ready |
| Local verified catalog at `data/catalog.jsonl` | Required input for demo, evaluator, and benchmark captures. | Verify with `python scripts/setup_data.py` before recording. | Present locally, final preflight Pending |

## Production items

| Item | Acceptance condition | Status |
|---|---|---|
| Final submission commit ID | Visible in every capability capture, with a clean repository before recording. | Pending |
| Architecture graphic | Shows only the current implemented path. It excludes routing, dual-route, dense, hybrid, semantic-reranking, and learned-clarification nodes. | Pending |
| Raw demo terminal take | One continuous S03-S06 run with command, turns 1-5, Top 10, and success exit. | Pending |
| Raw full-evaluator terminal take | Real S07 run from the same final commit, including the test count produced by that commit and the gate result. | Pending |
| Raw benchmark terminal take | Real S08 run with environment and machine-specific latency visible. | Pending |
| English voice-over | Follows `storyboard-3min.md`, sounds natural, and stays within 180 seconds. | Script Ready, recording Pending |
| English subtitles | Match spoken wording and every displayed number, then export as a timed subtitle file. | Text Ready, timing Pending |
| Highlight and caption overlays | Identify Active Intent, override replacement, Top 10, metric provenance, and shortened waiting time. | Pending |
| Limitation card | Uses only the four limitations in the approved script. | Pending |
| Team-role and contribution card | Shows `Fang Tianchen — initial Agent and demo baseline, public HR@10 0.91`, `Wang Siwen — backend/retrieval`, and `Liu Chunyi and Cheng Xianyun — testing/demo production`. It visually separates the accepted founding baseline, current roles, and later completed merged contributions; PR, SHA, and merge status stay in the ledger. | Pending |
| Final 180-second video | Legible at delivery resolution, audio synchronized, no unsupported claims, no secrets or private data. | Pending |
| Export manifest | Records final commit, commands, capture date, video checksum, duration, resolution, and subtitle checksum. | Pending |

## Final preflight commands

Run these from the repository root with the same Python 3.10+ interpreter that
will appear in the capture:

```text
git rev-parse HEAD
git status --short
python scripts/setup_data.py
python demo/run_demo.py
python scripts/team_gate.py --full-eval
python scripts/benchmark_runtime.py
git status --short
```

If any command fails, if the two status checks are not clean for tracked files,
or if the generated numbers differ from the prepared subtitles, stop production
and update the evidence ledger before recording again. The test count shown in
the video must come from this final preflight run.
