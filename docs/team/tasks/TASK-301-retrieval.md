# TASK-301: candidate retrieval boundary and baseline wrapper

Owner: Wang Siwen  
Reviewer: Team-lead automation Agent

## Allowed paths

- `solution/retrieval/**`
- `scripts/build_index.py`
- `artifacts/manifests/**`
- `tests/retrieval/**` after coordination with Liu Chunyi

## Outcome

Implement the shared `CandidateRetriever` protocol, first reproducing the
official field-aware BM25 behavior and then evaluating one isolated candidate
recall improvement. Document build/load/latency/memory and artifact checksums.

## Proof

- Fixed-query smoke results are deterministic.
- Returned IDs are unique and catalog-valid.
- No public labels or evaluator state are read.
- Generated indexes are not committed.
