# ADR TASK-305: capability-completion candidate lane

Status: experimental; accepted authority, not accepted outcome.
Date: 2026-09-01.

## Context and temporary authority

RC3 is the immutable comparison bundle.  Its default path intentionally leaves
parts of Track 4.2 inactive.  TASK-305 temporarily authorizes Wang Siwen to edit
the core, retrieval, integration, tests, candidate scripts and documentation in
the task card's allowlist.  This does not authorize changes to the evaluator,
frozen data, scoring/stopping rules, official contracts, main, or RC3.

The verified source snapshot was imported as commit `4ac56f446b948ec730f3a52f98841a4714dfa0a8`.
It corresponds to handoff source commit
`d15dcc0fec037ff005c115d62ea7689ed92b152f`; the hashes are not represented as
the same Git history.

## Decision

The TASK-305 runner selects one observable candidate preset:

- integrated orchestration with real Buying/Browsing route decisions;
- independent keyword, category and pinned MiniLM dense recall followed by
  deterministic de-duplication, route-weighted fusion and bounded diversity;
- three-valued Buying constraint evidence (`satisfied`, `conflict`, `unknown`),
  excluding known conflicts and retaining unknowns only as an explicit
  relaxation;
- a cheap over-generality gate that skips retrieval and semantic ranking before
  asking for missing information, and resumes after a substantive reply;
- explicit profile import through `reset`, session-local updates and explicit
  export for a caller-controlled next-session handoff;
- candidate-derived question choice after observable rejection and
  rejection-driven changes to pool size, query and recovery;
- semantic ranking whose model output must be a validated full permutation and
  must actually replace candidate order.  A local cross-encoder is disclosed as
  non-LLM.  Qwen/DeepSeek/OpenAI paths are disclosed as LLM paths and require a
  real credential, network opt-in and bounded budget.  Missing credentials are
  a failed capability precondition, never a mocked success.

RC3 remains available only through its existing frozen preset.  The new
candidate runner records the effective preset and module traces and refuses to
label an unavailable dense or LLM path as enabled evidence.

## Dependencies, models, data, cost and fallback

The existing optional lock file supplies NumPy 2.2.6, ONNX Runtime 1.29.0 and
Tokenizers 0.23.1.  `scripts/build_semantic_index.py` downloads pinned revisions
of `sentence-transformers/all-MiniLM-L6-v2` and
`cross-encoder/ms-marco-MiniLM-L6-v2`, both recorded as Apache-2.0, and writes
per-file SHA256 manifests under ignored `artifacts/semantic/`.  The dense index
is derived only from the checksum-verified frozen catalog.  Runtime inference
is local CPU and has no per-request fee.  Generated model/index assets are not
committed.

The existing chat LLM integrations use only explicitly configured providers,
models, credentials, regions and a shared RMB micro-unit budget ledger.  No key
is stored and no request is made without explicit network opt-in.  Transport,
schema, usage, budget or model failure falls back to deterministic local order
and opens a circuit.  A candidate run that never obtains valid LLM output is
reported as incomplete for the team-specific LLM goal.

For the credential-free proof, two and only two pinned local choices were
tested as allowed by the task card: Qwen2.5-0.5B-Instruct-GGUF and
Qwen2.5-1.5B-Instruct-GGUF through llama.cpp b10516.  Both produced valid but
semantically incorrect permutations on the fixed semantic probe.  No output
was relabelled as success and no third model or prompt search was attempted.
The 1.5B setup remains reproducible in
`scripts/task305_setup_local_llm.py` (Apache-2.0 model, MIT runtime, local CPU,
no request fee), but LLM semantic ranking is an explicit unfinished capability.

## Compatibility, tests and rollback

`Agent.reset(...)` and `Agent.respond(...)` retain their official signatures and
payload schema.  `export_profile(session_id)` is an optional host method; it
does not infer identity or connect sessions.  Tests cover route differences,
three-valued constraints, dense fusion/diversity and failure, pre-retrieval
cutoff/resume, profile handoff/isolation, model-output participation and dynamic
recovery.  Candidate metrics use the unchanged evaluator.

Rollback is selection of the immutable RC3 bundle or its frozen environment
preset, not disabling TASK-305 features while claiming this candidate complete.
The two permitted general optimization revisions did not bring Public metrics
within the task-card tolerance, so further tuning stopped and the candidate is
not proposed for acceptance.
