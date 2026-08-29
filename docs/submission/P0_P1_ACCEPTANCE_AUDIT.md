# P0/P1 first-version acceptance audit

Audit date: 2026-08-29  
Accepted code commit: `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad`  
Working tree during final CI-equivalent run: clean

## P0: first runnable algorithm — PASS

| Requirement | Authoritative evidence | Result |
|---|---|---|
| Official `reset/respond` contract | `python scripts/team_gate.py --full-eval`; contract smoke plus 22 tests | Pass |
| Full gate offline | Current-HEAD CI-equivalent run; no credentials/network in Agent | Pass |
| Public HitRate@10 >= 0.75 | Official 200-session evaluator: 0.91 | Pass |
| Public TechnicalScore >= 0.60 | Official evaluator: 0.777107 | Pass |
| Every scenario HitRate@10 >= 0.60 | Boundary 0.9; Browsing 0.95; Buying 0.925; Intent Override 0.766667 | Pass |
| No evaluator/data/metric changes | Gate compares protected paths with immutable official base `3407835`; current diff is empty | Pass |
| No target hard-coding/label coupling | No `ground_truth`, `public_set`, evaluator imports, or ASIN literals under `starter/` or `solution/` | Pass |
| No network-only critical path/secrets | Core scan contains no network client/URL; 0 model tokens and USD 0 API cost | Pass |
| >=200 non-public-target shadow, HitRate@10 >= 0.70 | `python scripts/shadow_evaluator.py`: 200 targets, overlap 0, official 80/80/30/10 mix, HitRate@10 0.895 | Pass |

The full gate now encodes the public P0 score floors, so a later implementation
cannot pass CI merely because the evaluator executed successfully.

## P1: repeatable demo — PASS

| Requirement | Authoritative evidence | Result |
|---|---|---|
| One credential-free command | `python demo/run_demo.py` on current accepted code | Pass |
| Show message/state/question/Top 10 every turn | Three printed turns include all required fields | Pass |
| Include override or boundary | Public Intent Override sample `public_0072` | Pass |
| Remove stale preference | Turn 3 state/query replace `Department: womens` with `Faux Fur`; automated test asserts both sides | Pass |
| Target rank/turn matches evaluator | Hit after override on turn 3, rank 1 | Pass |
| Fresh-checkout reproduction | Detached clean worktree at `6175dfe` downloaded and verified official data, ran demo/tests/gate; setup and demo files are unchanged through accepted code | Pass |
| Narrated flow <=3 minutes | `docs/submission/demo-script-3min.md`; deterministic command completes in seconds on reference machine | Pass |

## Current performance disclosure

- accepted runtime evidence: `reports/metrics/first-version-runtime.json`;
- 833 response calls; mean 37.736 ms, p95 76.583 ms on the reference machine;
- Agent initialization 2.933 seconds;
- prompt/completion tokens 0/0; estimated API cost USD 0;
- shadow evidence: `reports/metrics/first-version-shadow.json`.

## Not claimed by this audit

- The new private team GitHub repository has not yet been connected, so its
  first remote `full-evaluator` Actions job is not yet evidenced.
- P2 team integration is not complete: Liu, Cheng, and Wang have not yet landed
  reviewed task branches.
- No public or shadow result can prove the unknown 800-session private score.
- Team-contribution disclosure remains provisional until actual teammate commits
  are reviewed and merged.

These are explicit next-phase items; they do not invalidate the locally accepted
P0/P1 first runnable Demo.
