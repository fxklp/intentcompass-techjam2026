# RC3 method, measurements and limitations

> **Historical rollback document.** This describes RC3, not the accepted
> TASK-306 submission. Use `docs/submission/FINAL_REPORT.md` for final claims.

## Actual frozen algorithm

IntentCompass is a deterministic non-LLM shopping Agent. Its thin official
adapter delegates to modular session state, retrieval and policy code. RC3
packages TASK-015 algorithm commit `4968804054bc1159007d34fe40e976bca508fb4f`
without changing runtime source. RELEASE-MANIFEST records a separate packaging
commit because release checks and documentation have changed.

The active pipeline is:

1. Replace or clear structured preferences from current dialogue. Explicit
   overrides discard obsolete values; no-preference replies mark slots free.
2. Retrieve normally up to 50 candidates from one in-memory SQLite FTS5/BM25
   index. Guarded terminal recovery can request a larger pool, so 50 is not
   the unconditional maximum and there are not two active retrieval engines.
3. Rank with visible constraints, then category and complete requirement
   phrases within individual title/features/details fields. Category and
   full-phrase ordering preserve their input Top10 membership.
4. Within contiguous same-category/full-phrase groups, a strict title-evidence
   superset can pass a neighboring item at retrieval-rank distance <= 3.
   Incomparable evidence/ties retain input order; this step preserves
   Top10 membership and tail.
5. Guarded terminal recovery can change shown membership after explicit
   rejection or repeated late-turn results. It is not unconditional diversity.
6. Ask an available unasked attribute. After three consecutive explicit
   no-preference replies, advance the eligible `other` question once.
   Override/substantive replies reset this streak. Turn 10 asks no new question.

Deterministic no-match popularity fallback is preserved. Budget and recognized
negative preferences bypass the new evidence-ordering steps. Constraints are
soft signals, not guaranteed filtering; missing metadata remains unknown.
Title ordering shares PrecisionOrder's bounded field cache. Indexes remain
in-memory, without industrial databases or downloaded models.

Context/profile snapshots are session-local, not persistent cross-session user
models. Default ranking does not let profile priors outweigh explicit needs.
Workflow labels do not constitute active dense retrieval, learned question
optimization or autonomous online self-improvement.

## Model, cost and data disclosure

Default model/API: none. Runtime API cost and prompt/completion tokens: zero.
Python standard library with SQLite FTS5 is sufficient; no GPU, foundational
training, multimodal processing, real transactions or UI dependency.

The catalog and Public sessions are organizer-frozen Amazon Reviews 2023-derived
artifacts. Conversations are simulated, not real-user transcripts. Production
policy reads visible catalog/dialogue only, never hidden targets or sample IDs.
Preserve DATA_ATTRIBUTION.md and upstream terms. No private data, credentials,
API budget ledger, model assets or generated indexes are packaged.

Source contains inactive API/dense/multi-route support. These are NOT active
default features or prerequisites. No tested API variant was accepted as
superior to this final offline release under the full protocol. No API calls
occurred during TASK-015 adoption or RC3 packaging. Prior development was not
necessarily free: the historical ledger estimate was RMB9.110809 including
uncertain requests, not a provider invoice or current account balance.

## Quality and explicitly accepted tradeoff

Each cell is preceding TASK-013 -> accepted TASK-015/RC3 algorithm.

| Set | N | HitRate@10 | MRR | MTTC (lower better) | Local technical composite |
|---|---:|---|---|---|---|
| Public | 200 | .975 -> .980 | .693046 -> .696861 | 4.190 -> 3.755 | .831614 -> .843958 |
| Synthetic Shadow | 200 | .960 -> .965 | .698732 -> .703615 | 3.740 -> 3.545 | .834820 -> .842684 |
| Existing TASK-014 A | 800 | .94875 -> .95625 | .694759 -> .695408 | 3.73125 -> 3.45375 | .828178 -> .837672 |
| Existing TASK-014 B | 800 | .95125 -> .95625 | .698647 -> .698810 | 3.81875 -> 3.515 | .828844 -> .837468 |

Overall HR/MRR/MTTC improve on all four sets, but NOT all scenario MRR values:
A/buying decreases .692729 -> .690502; B/intent override decreases
.633509 -> .629838. The lead explicitly accepted those two decreases.
Historical strict non-regression rejection was preserved, not rewritten as
a pass. Every scenario HR is non-decreasing and MTTC non-increasing.

The selected TASK-014 candidate was frozen before A/B confirmation. TASK-015
then extracted accepted logic and reproduced these SAME sets; repetitions are
not new independent validation. Public/Shadow were repeatedly used during
development. Synthetic sets use the same simulator/catalog; they are not the
organizer-hidden set or evidence from real users.

The bundle checker regenerates all 200 Public results with the unchanged
evaluator and checks aggregate/scenario metrics, active policy, output schema,
reset, catalog/source integrity, zero network/tokens and the real Demo.
The selected Public Demo hits after override on turn 5 at rank 8, not a random
unseen success rate. TechnicalScore is an input to technical assessment,
not the contest total or a judging guarantee.

## Runtime measurements

TASK-015 used three alternating sequential fresh-process pairs on Windows,
Python 3.13.9, pinned to the same first allowed CPU. These measure the exact
algorithm shipped here; packaging itself does not justify a speed claim.

| Metric | TASK-013 | Accepted final algorithm |
|---|---:|---:|
| Median initialization | 3.467128 s | 3.242453 s |
| Median response p50 | 18.6652 ms | 25.6621 ms |
| Median response p95 | 96.9776 ms | 102.4571 ms |
| Median response p99 | 135.3821 ms | 141.0839 ms |
| Responses over the same 200 sessions | 833 | 747 |
| Maximum whole-process peak memory | 463351808 bytes | 462934016 bytes |

P95 increases approximately 5.48 ms; do not call RC3 faster. Earlier conversion
yields fewer responses, so per-response distributions do not contain identical
turns. Memory includes evaluator/catalog overhead. Startup/memory differences
are small observations, not architectural guarantees. Host/platform affect
measurements; release-check wall time is not a standardized speed benchmark.
Mac timing has not been independently measured.

## Limitations and release boundary

Lexical matching misses paraphrases and implicit intent. Clarification is
bounded/rule-based, not learned. Personalization, workflow adaptation and strict
constraint satisfaction remain limited. No global optimum or real transaction/
business conversion validation is claimed. Full four-pillar coverage is not
claimed; consult REQUIREMENTS.md.

Research informed category/phrase/title evidence and dialogue recovery.
Unselected lookahead/rare-term/other2 code was not copied into the final policy.
No new algorithm research or tuning occurs during packaging.

The ZIP is source-only; acquire the catalog separately and verify its checksum.
Independent Windows/macOS signoff, public repository, video and submission
remain separate actions through the lead. A local `RELEASE CHECK PASSED`
does not complete those deliverables.
