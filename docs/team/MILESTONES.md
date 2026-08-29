# Track 4 milestone gates

These gates prevent the team from calling a generated prototype "done" without
evidence. The integration owner records the exact commit and evaluator JSON for
every accepted milestone.

## P0: first runnable algorithm

Required:

- official `Agent.reset/respond` contract passes;
- `python scripts/team_gate.py --full-eval` passes offline;
- 200-session public `HitRate@10 >= 0.75`;
- public `recommended_technical_score >= 0.60`;
- every public scenario `HitRate@10 >= 0.60`;
- no evaluator/data/metric changes, target hard-coding, secrets, or network-only
  critical path;
- one independent shadow evaluation over at least 200 non-public catalog targets
  reaches `HitRate@10 >= 0.70` with the official scenario proportions.

Passing P0 freezes the first working branch. Later experiments must demonstrate
non-regression before replacement.

## P1: repeatable demo

Required:

- one command starts a deterministic multi-turn demo without credentials;
- the demo shows the user message, active structured preferences, selected
  `ask_attribute`, and ordered Top 10 on every turn;
- the chosen scenario includes an explicit intent override or boundary answer;
- the old preference is visibly replaced/cleared and never remains in the active
  query after the correction;
- the target enters Top 10 and the shown rank/turn matches evaluator evidence;
- a teammate can reproduce the demo from a fresh checkout using the README;
- total narrated flow fits within three minutes.

## P2: team integration

Required:

- retrieval, core, QA, and submission branches are merged through reviewed PRs;
- `main` passes the full gate and P0 thresholds;
- experiment ledger attributes every claimed improvement to a commit/config;
- all large artifacts have reproducible manifests and SHA-256 checksums;
- the submission report discloses model/API choice, latency, cost, limitations,
  offline fallback, and team contributions.
