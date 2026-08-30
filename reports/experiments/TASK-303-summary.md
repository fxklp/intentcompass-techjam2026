# TASK-303 Buying/Browsing dual-route in-memory experiment

> Remediation note: the candidate now treats an empty baseline FTS route as the
> compatibility boundary and directly returns the baseline's deterministic
> popularity fallback, even when category or expanded routes match. The direct
> candidate regression test checks fallback IDs, order, and trace. Public/shadow
> and the independent-process benchmark were rerun from code commit `0be7495`.

## Decision

The conservative candidate meets all three minimum integration thresholds, but
the gain is marginal and has a ranking/latency trade-off. Keep the exact FTS5
fallback and treat this as eligible for controlled integration testing, not an
automatic main-Agent replacement.

The initial unconstrained RRF experiment was rejected: Public HR@10 fell to
0.89 and Shadow HR@10 to 0.87 because additional route results displaced the
proven FTS5 tail. The retained-pool variant below keeps every baseline Top-50
candidate and lets the independent routes alter ordering only.

## Design

- `BaselineFTS5Retriever` reproduces the existing title/category/features/
  details/store/description FTS5 weights and popularity fallback.
- Auto routing uses only query, category, structured active constraints, and
  turn. It receives no scenario, target, label, or evaluator state.
- Buying combines exact-constraint AND retrieval, baseline broad FTS, category-
  only FTS, and a budget-aware fusion adjustment.
- Browsing combines category-only FTS, baseline broad FTS, generic use-case
  expansion, use-case-weighted FTS, and a deterministic category novelty bonus.
- Weighted reciprocal-rank fusion is deterministic and retains the complete
  baseline candidate pool as a recall guard.
- When baseline FTS has no match, candidate fusion and diversity are bypassed;
  popularity IDs come from the existing shared in-memory catalog index in
  exactly baseline order. No second index is built.
- Dense retrieval is not implemented. No token-overlap component is described
  as dense or semantic retrieval.

## Overall metrics

| Set | Variant | HR@10 | MRR | MTTC | TechnicalScore |
|---|---|---:|---:|---:|---:|
| Public | baseline | 0.910000 | 0.624024 | 4.255 | 0.777107 |
| Public | candidate | 0.910000 | 0.619054 | 4.160 | 0.777516 |
| Shadow | baseline | 0.895000 | 0.630488 | 3.805 | 0.780546 |
| Shadow | candidate | 0.900000 | 0.615097 | 3.710 | 0.780329 |

Public HR is unchanged and TechnicalScore improves by 0.000409. Shadow HR
improves by 0.005 and MTTC by 0.095, while Shadow TechnicalScore falls by
0.000217 because MRR falls by 0.015391.

## Scenario metrics

Scenario TechnicalScore below applies the official formula to each scenario's
reported HR, MRR, and MTTC.

| Set/variant | Scenario | HR@10 | MRR | MTTC | TechnicalScore |
|---|---|---:|---:|---:|---:|
| Public baseline | Buying | 0.9250 | 0.613323 | 4.2750 | 0.780997 |
| Public candidate | Buying | 0.9125 | 0.611483 | 4.2250 | 0.775195 |
| Public baseline | Browsing | 0.9500 | 0.677808 | 3.0625 | 0.837092 |
| Public candidate | Browsing | 0.9625 | 0.672951 | 2.8750 | 0.845635 |
| Public baseline | Intent Override | 0.766667 | 0.513254 | 6.8000 | 0.621310 |
| Public candidate | Intent Override | 0.766667 | 0.497976 | 6.8000 | 0.616726 |
| Public baseline | Boundary | 0.9000 | 0.611667 | 6.0000 | 0.733500 |
| Public candidate | Boundary | 0.9000 | 0.611667 | 6.0000 | 0.733500 |
| Shadow baseline | Buying | 0.9125 | 0.570372 | 2.9750 | 0.787862 |
| Shadow candidate | Buying | 0.9250 | 0.555526 | 2.8125 | 0.792908 |
| Shadow baseline | Browsing | 0.9000 | 0.697187 | 3.4000 | 0.811156 |
| Shadow candidate | Browsing | 0.9000 | 0.680188 | 3.4000 | 0.806056 |
| Shadow baseline | Intent Override | 0.833333 | 0.586984 | 6.733333 | 0.678095 |
| Shadow candidate | Intent Override | 0.833333 | 0.572077 | 6.566667 | 0.676956 |
| Shadow baseline | Boundary | 0.9000 | 0.708333 | 4.9000 | 0.784500 |
| Shadow candidate | Boundary | 0.9000 | 0.700000 | 4.8000 | 0.784000 |

The largest HR movement is 0.0125: Public transfers one hit from Buying to
Browsing, while Shadow adds one Buying hit. Override and Boundary HR do not
regress. MRR decreases in most candidate slices, so future integration should
validate rank quality rather than looking only at HR and MTTC.

## Candidate recall

| Set | Variant | First-turn recall@50 | Any-turn recall@50 | Turn recall@50 |
|---|---|---:|---:|---:|
| Public | baseline | 0.380 | 0.955 | 0.537815 |
| Public | candidate | 0.380 | 0.955 | 0.527027 |
| Shadow | baseline | 0.455 | 0.960 | 0.601351 |
| Shadow | candidate | 0.455 | 0.960 | 0.591413 |

The candidate retains exactly the baseline Top-50 ID set per retrieval call.
The lower turn-level value reflects earlier conversion and therefore fewer
late, highly constrained calls, not displaced candidates.

## Runtime and memory

| Set | Variant | Cold start (s) | Retrieval p50/p95 (ms) | Respond p50/p95 (ms) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|
| Public | baseline | 2.425 | 18.94 / 44.08 | 21.09 / 47.11 | 445.2 |
| Public | candidate | 2.596 | 28.41 / 81.19 | 31.17 / 86.04 | 444.4 |
| Shadow | baseline | 2.592 | 24.10 / 53.50 | 26.38 / 56.51 | 445.4 |
| Shadow | candidate | 2.530 | 34.60 / 81.15 | 36.45 / 83.00 | 445.5 |

Peak RSS includes evaluator catalog objects plus the in-memory FTS index. The
fixed-query retrieval-only benchmark measured 253.0 MiB peak RSS for both
baseline and candidate in separate processes. The candidate creates no
persisted index: generated asset size is 0 bytes; the verified input catalog is
60,546,327 bytes.

## Reproduction

After `python scripts/setup_data.py`, the critical path is fully offline:

```bash
python experiments/retrieval/evaluate.py --catalog data/catalog.jsonl --output reports/experiments/TASK-303-results.json
python scripts/benchmark_retrieval.py --catalog data/catalog.jsonl --iterations 20 --output reports/experiments/TASK-303-benchmark.json
python -m unittest discover -s tests/retrieval -p "test_*.py" -v
python scripts/team_gate.py
```

Raw evidence is in `TASK-303-results.json`; fixed-query evidence is in
`TASK-303-benchmark.json`. The manifest records hashes, catalog provenance, and
the tested code commit. Evidence hashes are SHA-256 digests of the raw bytes of
the UTF-8, LF-terminated files; they are not hashes of normalized text or parsed
JSON.

## Known limitations

- RRF improves conversion timing slightly but reduces aggregate MRR.
- Multi-route querying roughly doubles p95 retrieval latency.
- Generic query expansion is deliberately small and English-only.
- The conservative recall guard prevents new route-only products from entering
  the Top-50 pool; relaxing it failed the Public and Shadow HR gates.
- Public and deterministic shadow evidence cannot guarantee private-set gains.
