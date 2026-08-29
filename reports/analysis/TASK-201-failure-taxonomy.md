# TASK-201 public-set failure taxonomy

## Evidence ledger

- Baseline commit: `ccd58846a286ae1f102c28388ffe8364787df764` (`ccd5884`).
- Evaluator result: `reports/generated/team-gate-results.json`.
- Evaluator result SHA-256: `992666033582306a9c759b2d0702c76a59809983fadac7a3a66dc4ac19946824`.
- Public metadata: `data/public_set.jsonl`.
- Public metadata SHA-256: `571359a8a69014c43fc30d39c996c4a28e875dccc249dffc707358757beb16c0`.
- Evaluated sessions: 200.
- The report aggregates metadata only; it emits no sample identifiers or target products.

Regeneration command:

```bash
python analysis/failure_taxonomy.py --result reports/generated/team-gate-results.json --public-set data/public_set.jsonl --baseline-commit ccd58846a286ae1f102c28388ffe8364787df764 --output reports/analysis/TASK-201-failure-taxonomy.md
```

The script validates unique session identifiers, a complete one-to-one join with the public set, scenario consistency, supported difficulty buckets, and the expected 18-failure breakdown. A mismatch exits non-zero instead of generating a report.

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

## Top three general failure classes

These are diagnostic classes supported by scenario and difficulty concentration, not proof of a specific internal defect. The evaluator JSON records final outcomes but not candidate-recall or reranker traces, so those mechanisms must be separated in a future experiment.

### 1. Post-override recovery (7/18; 38.89%)

Evidence slice: Intent Override.

Failures concentrate after the active intent changes, indicating that state replacement, query reconstruction, or post-change candidate recovery remains the highest-risk path.

General improvement direction: Test slot replacement and query rebuilding as one invariant; after a material change, retrieve a fresh and sufficiently broad candidate pool before reranking.

### 2. Constrained-buying recall or ranking (6/18; 33.33%)

Evidence slice: Buying.

Failures remain even when a hard constraint is disclosed early. Outcome-only evidence cannot separate candidate-recall loss from incorrect final ordering.

General improvement direction: Measure candidate recall before reranking, normalize equivalent constraint wording, and combine field-aware lexical retrieval with a general semantic fallback.

### 3. Ambiguity and no-preference handling (5/18; 27.78%)

Evidence slice: Browsing, Boundary.

Vague requests and absent preferences form a shared clarification problem: the agent must ask useful questions without narrowing too early or repeating a cleared slot.

General improvement direction: Choose clarifications by expected information gain, preserve diverse recommendations while evidence is sparse, and mark no-preference attributes as non-blocking.

## Interpretation boundary

The taxonomy is suitable for prioritizing scenario-level experiments. It must not be used to add rules keyed by public sample identifiers, ground-truth identifiers, or particular products. Any proposed retrieval or policy change should be evaluated on the full public set and an independent shadow or locked split before adoption.
