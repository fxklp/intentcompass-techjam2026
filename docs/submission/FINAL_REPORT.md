# IntentCompass final report

## Problem and approach

Track 4 rewards an Agent that identifies an exact hidden catalog item early and
high in the Top 10 while the customer's needs unfold over multiple turns.
IntentCompass separates conversation state, workflow decisions, retrieval and
ranking so a correction replaces stale intent instead of contaminating later
queries.

The official `starter.agent.Agent` delegates to a target-blind local pipeline:

```text
message
  -> replaceable active intent
  -> Buying/Browsing workflow and recovery decision
  -> keyword/category/constraint/expansion recall from one in-memory FTS5 index
  -> optional on-demand in-memory MiniLM dense recall
  -> three-state constraints and guarded evidence ordering
  -> optional on-demand local cross-encoder
  -> clarification + ordered unique Top 10
```

Very broad requests can stop expensive retrieval and ask for clarification.
Rejection, override and overload change pool size and workflow. Missing or
invalid semantic assets fail closed to deterministic lexical retrieval.

## Evaluation

The evaluator, catalog, Public labels, formulas and stopping rules were not
modified. On the 200 released Public sessions the frozen candidate reproduced:

- HitRate@10: 0.980000
- MRR: 0.696861
- MTTC: 3.755000
- Efficiency: 0.724500
- TechnicalScore: 0.843958

TechnicalScore is an input to Technical Execution, not an overall competition
score. The demonstrated Intent Override session first hits on turn 5 at rank 8.
Public and repeatedly used synthetic sets are not the organizer's private set.

## Models, dependencies, latency and cost

The base path uses Python 3.12/3.13 and SQLite FTS5. Full local semantics use
NumPy 2.2.6, ONNX Runtime 1.29.0 and Tokenizers 0.23.1. The pinned Apache-2.0
models are `all-MiniLM-L6-v2` for 384-dimensional dense retrieval and
`ms-marco-MiniLM-L6-v2` for local cross-encoder ranking. No training or
fine-tuning occurs.

The Public run reported zero model tokens and no network attempts because its
scripted turns did not trigger semantic execution. A separate target-blind E2E
test executed dense retrieval, bounded diversity and the real cross-encoder.
Independent Win11/Python 3.12 Public validation measured about 143 ms p95 with
verified local assets; latency is machine-specific.

Qwen and DeepSeek adapters are optional. A real `qwen3.8-max` proof completed a
valid permutation with 3,726 prompt and 54 completion tokens at a conservative
ledger delta of RMB 0.058274. It proves integration, not accuracy improvement.
Credentials are environment-only; failure preserves the local order.

## Scope and feasibility

The project is CPU-based, text-only and uses in-memory indexes. It includes no
UI dependency, transaction system, GPU requirement, foundational-model
training, multimodal processing or external vector database. Catalog-derived
semantic assets are checksum-bound to the supplied catalog and pinned model
revisions. Setup and fallback behavior are documented in the README.

## Limitations

- The released Public conversations do not exercise every demand-driven branch.
- Parent-level metadata may omit variant attributes; missing values remain unknown.
- Semantic assets have one-time build and memory costs.
- Public/synthetic performance does not guarantee private-set or business results.
- Personalization requires explicit caller consent and profile handoff; it does
  not infer identity or maintain a global user database.

## Team contributions

- Fang Tianchen: team lead, architecture, original Agent, algorithm optimization
  and final integration.
- Liu Chunyi: QA, cross-platform contracts/CI, reproduction and reviews.
- Cheng Xianyun: failure analysis, evidence, Windows testing, storyboard and video.
- Wang Siwen: retrieval experiments, benchmark/evidence integrity and semantic QA.

AI coding assistance was used for implementation, testing and documentation;
the team owns the decisions, verification and claims.
