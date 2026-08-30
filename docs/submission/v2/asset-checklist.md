# V2 production asset checklist

Status: synchronized to accepted main
`5bd5d6fac91aad718862baded99eaf8b21cdd2bf` under TASK-204. Evidence is
prepared; no media has been recorded or uploaded.

## Repository evidence available now

| Asset or source | Purpose | Evidence anchor | Status |
|---|---|---|---|
| `docs/competition_specification.md` and `docs/submission_rules.md` | Official objective, protocol, deliverables, and execution constraints. | `34078351e1c3615e5505a2e829600b56a542e462`; `2a6cc8e776da66ce69b1cbd237838fbc43f32587` | Ready |
| `starter/agent.py`, `solution/agent_impl.py`, `solution/state.py`, `solution/ranker.py`, and `solution/question_policy.py` | Source of truth for the formal architecture diagram. | Main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`; formal core unchanged from accepted baseline `a81b042d3010fb254519ab56573d03beba111396` | Ready as source |
| `.gitattributes`, `.editorconfig`, `.github/workflows/cross_platform_ci.yml`, and `tests/test_cross_platform_contract.py` | Cross-platform reproduction and binary-safety evidence. | PR #6 head `35927230574ddbf983f66aa6f54f897dec157d99`; merge `ce87a192964c6a10fcb9f2a3239bb48c7653789f` | Ready |
| `demo/run_demo.py` | Real multi-turn Intent Override run with per-turn state and Top 10. | Demo correction `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`; PR #5 merge `a81b042d3010fb254519ab56573d03beba111396`; reproduced at main `5bd5d6f...` | Ready to record |
| TASK-204 local reproduction record | Current test count, demo result, and full-gate metrics on the accepted main code. | `docs/team/tasks/TASK-204-main-evidence-sync.md`; Windows/Python 3.12.13 run at `5bd5d6f...` | Ready as planning evidence; final capture Pending |
| `reports/metrics/first-version-runtime.json` | Historical public metrics, latency, tokens, network, workload, and environment. | Measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Ready, historical reference only |
| `reports/metrics/first-version-shadow.json` | Deterministic robustness evidence with zero public-target overlap. It is not an official private score. | Measured code `4ea2cff794318baa5e05ab77e089f2997edbc3cc`; evidence commit `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad` | Reserve only |
| `reports/analysis/TASK-201-failure-taxonomy.md` | Evidence-based failure categories and interpretation limits. | PR #4 merge `184ef33a9cf686b5ef55bc60d6d0b223d762d666` | Ready |
| TASK-303 source, manifest, and frozen experiment reports | Isolated Buying/Browsing lexical dual-route design, negative result, trade-offs, provenance, and hashes. | Code `0be74958a9833e1c6e2e0bd5a8db9abdc9c6ebcd`; PR #8 merge `970f0b754bba06f93b889e1b87f4ee9174e43ecb`; evidence fix `ae5589ef66024dbe562de456783f1d159e8ec64f`; PR #9 merge `5bd5d6fac91aad718862baded99eaf8b21cdd2bf` | Ready as isolated experiment evidence; not formal Agent evidence |
| V2 materials from TASK-203 | Reviewed storyboard foundation now synchronized by TASK-204. | PR #7 head `89293876231e21ebeca9c112ccfd19ce00a3a939`; merge `ceea73f219c5082e968c2ab99e4c7465d2457690` | Ready as historical source |
| `docs/submission/v2/claim-evidence-ledger.md` | Single source of truth for claims, formal/experiment boundaries, merged contributions, PRs, and SHAs. | TASK-204 ledger | Ready |
| Local verified `data/catalog.jsonl` | Required input for demo and evaluator captures. | Verify with `python scripts/setup_data.py` before recording. | Present locally; final preflight Pending |

## Production items

| Item | Acceptance condition | Status |
|---|---|---|
| Final recording commit ID | Visible in every capability capture with a clean tracked worktree. | Pending |
| Formal architecture graphic | Shows only the active state/FTS5-BM25/lexical-rerank/clarification/Top-10 path. The isolated experiment is not a runtime node. | Pending |
| Experiment-decision card | Clearly says the merged dual-route lexical experiment is not enabled in the formal Agent and reports its trade-offs without claiming deployment. | Pending |
| Raw demo terminal take | One continuous S03-S06 run with command, turns 1-5, Top 10, Rank 8, and successful exit. | Pending |
| Raw full-evaluator terminal take | Real S07 run from the same final commit with that commit's test count and gate result. | Pending |
| Historical runtime evidence capture | Real CLI display of the committed JSON with original measurement commit and environment visible. | Pending |
| English voice-over | Follows `storyboard-3min.md`, sounds natural, and stays within 180 seconds. | Script Ready, recording Pending |
| English subtitles | Match spoken wording and every displayed number, then export as a timed subtitle file. | Text Ready, timing Pending |
| Highlight and caption overlays | Identify Active Intent, override replacement, Top 10, metric provenance, formal/experiment boundary, and shortened waiting time. | Pending |
| Limitation card | Uses only evidence-bounded formal limitations and experiment trade-offs. | Pending |
| Team-contribution card | Uses the four names and responsibilities in S10; PR, review, and SHA detail stays in the ledger. | Pending |
| Final 180-second video | Legible, synchronized, free of unsupported claims, secrets, or private data. | Pending |
| Export manifest | Records final commit, commands, capture date, checksum, duration, resolution, and subtitle checksum. | Pending |

## Final preflight commands

Run from the repository root using the final production interpreter:

```text
git rev-parse HEAD
git status --short
python scripts/setup_data.py
python demo/run_demo.py
python scripts/team_gate.py --full-eval
python -m json.tool reports/metrics/first-version-runtime.json
git status --short
```

If a command fails, status is dirty without explanation, or generated metrics
differ from the prepared subtitles, stop and update the evidence ledger before
recording. The test count in the video must come from the final recording
commit. Displaying the runtime JSON does not remeasure latency; it preserves the
historical environment and commit recorded in that file.
