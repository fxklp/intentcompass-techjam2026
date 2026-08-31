# ADR-0011: opt-in semantic reranking boundary

Owner: integration Agent; no shared contract migration or retrieval edits.

Rationale: a real model may resolve semantic intent that lexical boosts miss.
Keep a small, testable Responses API client using Python's standard library,
with a fixed HTTPS OpenAI endpoint. No SDK, downloaded asset, new data source,
model training, or license-bearing binary dependency is added. Service/model
use remains subject to the provider's terms and the selected model's access.

Sources checked 2026-08-31:
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/reference/cli/resources/responses/methods/create

Cost: zero with the default disabled configuration. Paid tests are NOT approved
by this ADR. Model ID, approved monetary budget, current per-token pricing and
the actual smoke result must be supplied before live testing. A request cap is
an extra guard, not a monetary budget guarantee. No automatic retries.

Activation requires all of these (only after approval):
- `INTENTCOMPASS_AGENT_MODE=adaptive`
- `INTENTCOMPASS_SEMANTIC=openai`
- `INTENTCOMPASS_LLM_ALLOW_NETWORK=1`
- `INTENTCOMPASS_LLM_MODEL` explicitly selected (no guessed default)
- `INTENTCOMPASS_LLM_MAX_CALLS` positive, capped at 100 for this experiment
- `OPENAI_API_KEY` supplied by the owner in their environment, never in Git

Data: only bounded current category/explicit preferences, unsuppressed safe
profile tags and up to 20 candidate IDs/text snippets. No raw transcript,
session ID, caller profile summary or hidden evaluation field. `store=false`
disables response storage for retrieval; it is NOT a claim of zero retention.
All strings in the request are treated as untrusted ranking data, not commands.

Response: strict JSON schema plus independent exact-permutation validation.
Unknown/duplicate/missing IDs, refusal, incomplete output, malformed response,
missing credentials, HTTP errors and timeout retain the lexical ordering.
Known token usage is reported even on invalid ranking/refusal. Missing usage
after an attempted request is marked unknown, not reported as zero cost.

Reproduce offline protections: `python -m unittest tests.core.test_semantic`.
Live reproduction is intentionally deferred pending approval. Never claim mock
tests prove model quality, endpoint access, latency, or final metric gains.
Rollback: unset the semantic/network variables; the standard offline route
remains available without keys or network.
