# Three-minute demo script

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

## 0:40-1:30 — Turns 1 and 2

Point to the customer message, active state, search query, chosen clarification,
and ordered Top 10. Explain that “no additional preference” does not invent a
constraint.

## 1:30-2:15 — Intent override

On turn 3, point to the correction from `Department: womens` to `Faux Fur`.
Show that active state contains only `Faux Fur`: the stale preference was
removed, not merely appended to the query. Then show target rank 1 after the
correction.

## 2:15-2:45 — Evaluation evidence

State the reproducible public result: HitRate@10 0.91 and recommended
TechnicalScore 0.777107 over all 200 public sessions, with no network calls or
model tokens.

## 2:45-3:00 — Close

“The demo proves the core mechanism, not a hard-coded happy path: the same
Agent passes the full evaluator, and an independent 200-target non-public-catalog
shadow set reached HitRate@10 0.895 with zero overlap with public targets.”
