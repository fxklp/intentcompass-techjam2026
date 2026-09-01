# Three-minute demo script

> **Superseded baseline script.** Metrics and architecture below predate
> TASK-306. Do not use this file for the final video.

## 0:00-0:25 — Problem and claim

“IntentCompass is a deterministic conversational product-search agent. It
keeps an explicit active-intent state, asks one useful clarification at a time,
and removes superseded preferences instead of letting stale intent contaminate
retrieval.”

## 0:25-0:40 — Start the real system

Run from the repository root:

```bash
python demo/run_demo.py
```

Explain that this uses the real `starter.Agent` and official customer
simulator. The harness knows the labeled public target only to show rank; the
Agent receives no ground truth.

## 0:40-1:30 — Turns 1-3 (before override)

Point to the customer message, active state, search query, chosen clarification,
and ordered Top 10. Note that `Target rank` displays “Not scored until intent
override” — the harness does not reveal the final target's position before the
override, matching the official evaluator's scoring gate.

## 1:30-2:15 — Intent override and hit

On turn 4, the customer overrides their earlier preference from `Hand Wash Only`
+ `100% Polyester` to just `polyester`. Show that active state drops the stale
slots and retains only `polyester`. The target does not appear in Top 10 on
turn 4. On turn 5, after the customer adds `Button closure` + `Hand Wash Only`,
the target enters Top 10 at rank 8. `First hit turn: 5` matches exactly — no
contradiction between per-turn display and the final summary.

## 2:15-2:45 — Evaluation evidence

State the reproducible public result: HitRate@10 0.91 and recommended
TechnicalScore 0.777107 over all 200 public sessions, with no network calls or
model tokens.

## 2:45-3:00 — Close

“The demo proves the core mechanism, not a hard-coded happy path: the same
Agent passes the full evaluator, and an independent 200-target non-public-catalog
shadow set reached HitRate@10 0.895 with zero overlap with public targets.”
