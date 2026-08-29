# TASK-201 public-set failure taxonomy

## Evidence ledger

- Baseline commit: `ccd58846a286ae1f102c28388ffe8364787df764` (`ccd5884`).
- Evaluator result: `reports/analysis/evidence/team-gate-results.json`.
- Evaluator result SHA-256: `992666033582306a9c759b2d0702c76a59809983fadac7a3a66dc4ac19946824`.
- Public metadata: `data/public_set.jsonl`.
- Public metadata SHA-256: `571359a8a69014c43fc30d39c996c4a28e875dccc249dffc707358757beb16c0`.
- Evaluated sessions: 200.
- The report aggregates metadata only; it emits no sample identifiers or target products.

Regeneration command:

```bash
python analysis/failure_taxonomy.py --result reports/analysis/evidence/team-gate-results.json --public-set data/public_set.jsonl --baseline-commit ccd58846a286ae1f102c28388ffe8364787df764 --output reports/analysis/TASK-201-failure-taxonomy.md
```

The script validates unique session identifiers, a complete one-to-one join with the public set, scenario consistency, supported difficulty buckets, the expected 18-failure breakdown, and that the baseline commit exists in the local repository. A mismatch exits non-zero instead of generating a report.

## Failure classification

### By scenario

| Scenario | Public sessions | Failures | Failure rate | Expected failures | Check |
| --- | ---: | ---: | ---: | ---: | --- |
| Buying | 80 | 6 | 7.50% | 6 | Pass |
| Browsing | 80 | 4 | 5.00% | 4 | Pass |
| Intent Override | 30 | 7 | 23.33% | 7 | Pass |
| Boundary | 10 | 1 | 10.00% | 1 | Pass |
| **Total** | **200** | **18** | **9.00%** | **18** | **Pass** |

### By difficulty

| Difficulty | Public sessions | Failures | Failure rate | Share of failures |
| --- | ---: | ---: | ---: | ---: |
| Easy | 80 | 6 | 7.50% | 33.33% |
| Medium | 90 | 5 | 5.56% | 27.78% |
| Hard | 30 | 7 | 23.33% | 38.89% |

### Scenario by difficulty

| Scenario | Easy | Medium | Hard | Total |
| --- | ---: | ---: | ---: | ---: |
| Buying | 6 | 0 | 0 | 6 |
| Browsing | 0 | 4 | 0 | 4 |
| Intent Override | 0 | 0 | 7 | 7 |
| Boundary | 0 | 1 | 0 | 1 |
| **Total** | **6** | **5** | **7** | **18** |

## Observable evidence from failed sessions

The evaluator records four session-level signals per sample: `hit`, `best_rank`, `first_hit_turn`, and `reciprocal_rank`. Aggregating across the 18 failures:

| Signal | Observation | Count |
| --- | --- | ---: |
| `best_rank` | `null` (target never appeared in any recommendation list) | 18/18 |
| `first_hit_turn` | `null` (target never surfaced at any turn) | 18/18 |
| `reciprocal_rank` | `0.0` (complete recall miss) | 18/18 |
| `category_bucket` | clothing (18) | 18/18 |

All 18 failures are **complete recall misses**: the target product was never retrieved into any recommendation list at any conversational turn. The evaluator data contains no partial-hit or near-miss signals that could differentiate failure mechanisms across scenarios. Consequently, the failure classes below are hypotheses derived from scenario metadata and difficulty concentration, not from fine-grained behavioral traces.

## Top three failure-class hypotheses

Because all 18 failures are complete recall misses with no differentiating session-level signals (see above), these classes are **hypotheses** informed by scenario metadata and difficulty concentration. They identify where failures cluster and propose plausible mechanisms, but proving the actual internal defect requires conversation-level traces and candidate-recall logs that the evaluator result does not contain.

### 1. Post-override recovery (7/18; 38.89%)

Evidence slice: Intent Override.

Hypothesis: Failures concentrate after the active intent changes, indicating that state replacement, query reconstruction, or post-change candidate recovery remains the highest-risk path.

General improvement direction: Test slot replacement and query rebuilding as one invariant; after a material change, retrieve a fresh and sufficiently broad candidate pool before reranking.

### 2. Constrained-buying recall or ranking (6/18; 33.33%)

Evidence slice: Buying.

Hypothesis: Failures remain even when a hard constraint is disclosed early. Outcome-only evidence cannot separate candidate-recall loss from incorrect final ordering.

General improvement direction: Measure candidate recall before reranking, normalize equivalent constraint wording, and combine field-aware lexical retrieval with a general semantic fallback.

### 3. Ambiguity and no-preference handling (5/18; 27.78%)

Evidence slice: Browsing, Boundary.

Hypothesis: Vague requests and absent preferences form a shared clarification problem: the agent must ask useful questions without narrowing too early or repeating a cleared slot.

General improvement direction: Choose clarifications by expected information gain, preserve diverse recommendations while evidence is sparse, and mark no-preference attributes as non-blocking.

## Limitations and next steps

The evaluator result records only final outcomes (`hit`, `best_rank`, `reciprocal_rank`). All 18 failures share identical signals (target never retrieved), so scenario-level aggregation is the finest granularity available. To upgrade these hypotheses into confirmed root causes, the following additional evidence is needed:

1. **Conversation traces**: full dialogue turns to observe where slot-filling or clarification diverged from the user profile.
2. **Candidate-recall logs**: the retrieval stage's candidate set at each turn, to separate recall failure from reranking failure.
3. **Query reconstruction diffs**: for Intent Override sessions, the before/after query state to verify whether slot replacement occurred correctly.

## Interpretation boundary

The taxonomy is suitable for prioritizing scenario-level experiments. It must not be used to add rules keyed by public sample identifiers, ground-truth identifiers, or particular products. Any proposed retrieval or policy change should be evaluated on the full public set and an independent shadow or locked split before adoption.
