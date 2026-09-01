# ADR-TASK306: capability-complete integration lane

## Context

RC3 is reproducible and strong but does not activate every capability described
in Track 4.2. The original TASK-305 implementation is unavailable because it was
not pushed. The team lead explicitly authorized a new isolated integration lane.

## Decision

Preserve RC3 as immutable rollback. Implement target-blind, on-demand buying and
browsing paths, real in-memory lexical/dense multi-route retrieval, verified
semantic ranking with safe fallback, early over-generality cutoff, explicit
profile handoff and adaptive orchestration. Keep the official adapter thin.

New dependencies, models, APIs and data require source, license, setup, resource,
cost and fallback disclosure. Official evaluator/data/contracts are unchanged.

The default semantic assets are pinned Apache-2.0 ONNX exports of
`sentence-transformers/all-MiniLM-L6-v2` revision `1110a243...` and
`cross-encoder/ms-marco-MiniLM-L6-v2` revision `233902d...`. They run on CPU
through the pinned optional dependencies in `requirements-semantic.txt`.
Artifacts are checksum-bound to the official catalog and are not committed.
Missing/corrupt assets fall back to lexical ordering without downloading.

An external LLM is not an official requirement and cannot be the credentialless
default. Existing Qwen/DeepSeek adapters remain an opt-in, budgeted semantic
backend. One sanitized Qwen proof completed through the production candidate
chain; failure, malformed output or unknown usage keeps the offline order.

## Migration and rollback

TASK-306 starts at RC3 source commit `d15dcc0fec037ff005c115d62ea7689ed92b152f`.
The candidate is accepted only after functional proof plus paired metric and
runtime evidence. Rollback is the unchanged RC3 package and algorithm commit.

## Tests

Add direct capability tests, end-to-end trace assertions, failure fallback,
session isolation, official-output validation, paired evaluation and performance
evidence. No existing assertion may be weakened.
