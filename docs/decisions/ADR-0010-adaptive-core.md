# ADR-0010: private adaptive orchestration without contract migration

Decision: preserve default baseline until measured non-regression and review.
Implement a runnable alternate core selected by `INTENTCOMPASS_AGENT_MODE=adaptive`.
The official constructor/reset/respond signatures and shared dataclasses stay
unchanged. No affected-owner contract migration is required.

The alternate core consumes Wang's existing rich RetrievalRequest/Result via a
private adapter. Default retrieval is BaselineFTS5Retriever. Explicit
`INTENTCOMPASS_RETRIEVAL=dual_route` enables the previously isolated candidate
only for controlled tests, never as an unconditional baseline replacement.
Only one catalog index is built per Agent.

State parsing and lexical scoring are reused, not copied. New pure functions
distill active context, estimate candidate attribute splits, select a bounded
workflow, and apply low-weight profile preferences behind explicit constraints.
Short-term corrections replace memory; long-term aggregate tags are caller-
provided priors, not an identity store or raw conversation archive. A reset
destroys learned session preferences. Unknown profile fields are ignored.

The offline lane introduces no packages, model assets, data sources or API
costs. It remains standard-library CPU and in-memory FTS5, not dense retrieval
or model-based semantic reranking. The separate optional API boundary and its
not-yet-approved live verification are documented in ADR-0011.

Rollback: unset both environment variables. Baseline state parsing, ranking,
question policy, retrieval and all pre-existing tests remain unchanged.
Verification: TASK-003 acceptance commands and independent Liu review. Promotion
must not be inferred from an internal floor score or from passing unit tests.
