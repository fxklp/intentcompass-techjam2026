# V2 production asset checklist

Status: local checklist. It inventories what exists and what must be produced
after the storyboard is approved. No media has been recorded or uploaded.

## Repository evidence available now

| Asset or source | Purpose | Evidence anchor | Status |
|---|---|---|---|
| `docs/competition_specification.md` and `docs/submission_rules.md` | Official objective, protocol, deliverables, and execution constraints. | `34078351e1c3615e5505a2e829600b56a542e462` and `2a6cc8e776da66ce69b1cbd237838fbc43f32587` | Ready |
| `docs/contracts/architecture.md` | Source for the explanatory architecture diagram. | `8e88d75cbd8f3a1a6c3f6fcfebdd3bc22b9d85bb` | Ready as source |
| `demo/run_demo.py` | Real multi-turn Intent Override run with per-turn state and Top 10. | `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`, merged in PR #5 at `a81b042d3010fb254519ab56573d03beba111396` | Ready to record |
| `reports/metrics/first-version-runtime.json` | Accepted public metrics, latency, token, network, workload, and environment evidence. | measured commit `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Ready |
| `reports/metrics/first-version-shadow.json` | Robustness evidence with zero public-target overlap. It is not an official score and is not required in the core 180-second cut. | measured commit `4ea2cff794318baa5e05ab77e089f2997edbc3cc`, evidence commit `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad` | Reserve only |
| `reports/analysis/TASK-201-failure-taxonomy.md` | Evidence-based failure categories and interpretation limits. | `cac52211e4d0eea13c27512689a4e59d13acc86b`, merged in PR #4 at `184ef33a9cf686b5ef55bc60d6d0b223d762d666` | Ready |
| Merge history through `a81b042d3010fb254519ab56573d03beba111396` | Team-contribution evidence. | PR merge commits #1, #2, #4, and #5 | Ready |
| Local verified catalog at `data/catalog.jsonl` | Required input for demo, evaluator, and benchmark captures. | Verify with `python scripts/setup_data.py` before recording. | Present locally, final preflight Pending |

## Production items

| Item | Acceptance condition | Status |
|---|---|---|
| Final submission commit ID | Visible in every capability capture, with a clean repository before recording. | Pending |
| Architecture graphic | Matches the frozen contract, uses no unsupported component, and is labeled explanatory. | Pending |
| Raw demo terminal take | One continuous S03-S06 run with command, turns 1-5, Top 10, and success exit. | Pending |
| Raw full-evaluator terminal take | Real S07 run from the same final commit, including test and gate result. | Pending |
| Raw benchmark terminal take | Real S08 run with environment and machine-specific latency visible. | Pending |
| English voice-over | Follows `storyboard-3min.md`, sounds natural, and stays within 180 seconds. | Script Ready, recording Pending |
| English subtitles | Match spoken wording and every displayed number, then export as a timed subtitle file. | Text Ready, timing Pending |
| Highlight and caption overlays | Identify Active Intent, override replacement, Top 10, metric provenance, and shortened waiting time. | Pending |
| Limitation card | Uses only the four limitations in the approved script. | Pending |
| Contribution card | Contains only PR #1, #2, #4, and #5 unless additional PRs merge before recording. | Pending |
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
and update the evidence ledger before recording again.
