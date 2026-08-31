# Method, measurements and limitations

## Actual submitted default

IntentCompass is a deterministic non-LLM shopping Agent. A thin official adapter
delegates to a modular implementation. `reset` creates independent state;
`respond` updates preference slots, retrieves up to 50 candidates from one
in-memory SQLite FTS5/BM25 index, reranks by visible preferences and asks a
non-repeating clarification using a fixed priority order. Invalid IDs and
duplicate recommendations are not generated intentionally; acceptance checks
validate every Public response before the unchanged evaluator scores it.

RC2 then stably prioritizes current category evidence within the same Top10.
Ties keep their previous order. It never adds or removes a Top10 member, never
promotes the tail, and leaves deterministic no-match fallback untouched. A
bounded 512-entry cache stores only static catalog-query results. No dialogue,
target labels or final answers are cached. Category ordering is not a new route.

An explicit override replaces obsolete preferences. No-preference replies clear
the relevant slot. Context is distilled into bounded current preferences and a
safe profile snapshot. That snapshot is session-local and optionally exportable;
it is not a persistent cross-session user model. The default ranking does not
use profile priors to outweigh explicit requirements.

Workflow state labels buying/browsing, rejection and overload situations, but
the frozen integrated configuration retains the same lexical retrieval backend
and 50-candidate pool. Do not describe these labels as two active retrieval
engines. The overload path can suppress optional model work; it does not stop
all lexical retrieval. Clarification is state-aware, not learned question-value
optimization or online self-improvement.

The latest limited correctness fix distinguishes a simple negative material/color
preference from a positive keyword, and an upper budget from a target price when
already parsed into the budget slot. These are soft ranking signals, not guaranteed
hard filtering. Unknown metadata remains unknown. Compound negation and unrestricted
natural language are limitations.

## Model, data and tool disclosure

Default model: none. Default external APIs: none. Runtime dependencies: Python
standard library, including SQLite FTS5. Development tools include Git/GitHub,
Python unittest, PowerShell and AI coding assistance. There is no foundational
model training, multimodal processing, external vector database or UI dependency.

Data is the organizer-frozen Amazon Reviews 2023 catalog and released Public
sessions, not scraped purchase histories or real customer interviews. We do not
reconstruct organizer-private labels. Evaluation targets stay in the harness,
not in production Agent inputs or decision rules. Preserve DATA_ATTRIBUTION.md.

Optional Qwen/DeepSeek rerankers and CPU dense/cross-encoder experiments exist in
the full source. They are disabled in the release preset and are not prerequisites.
Some small-screen API outcomes looked promising, but no tested API candidate met
the full quality acceptance protocol. Do not claim that APIs outperform the strong
offline default on the full benchmark. No provider key or budget ledger is packaged.

## Evidence

The local Public evaluator produces HR@10 .91, MRR .648734, MTTC 4.255,
Efficiency .6745 and TechnicalScore .784520 over 200 sessions. The release checker
regenerates aggregate and all per-session results from the packaged source.
The example demo hits on the first eligible turn 5 at rank 8. It is a selected
Public demonstration, not a random unseen success rate.

| Set | Sessions | RC1 MRR | Qualified RC2 MRR | HR, unchanged | MTTC, unchanged |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public development | 200 | .624024 | .648734 | .910 | 4.255 |
| Original synthetic Shadow | 200 | .630488 | .656149 | .895 | 3.805 |
| New synthetic confirmation | 800 | .658917 | .689676 | .93375 | 3.52875 |

All four scenario groups passed HR/MRR/MTTC non-regression on every set. The
confirmation seed was fixed before results and excludes Public and original
Shadow targets. These are the same official simulator over the same catalog,
not real users or the organizer's hidden set. Public was used for development;
six candidates were selected for validation, and only one survived Shadow.
Neither repeated development nor multi-candidate selection is an unbiased test.
No quality rule was changed after validation results.

The qualified research candidate was frozen at
799e590fd10eda9fd401544473c5e34cf6163ec2. Three alternating Windows/Python 3.13.9
fresh-process comparisons pinned each child to the same first allowed CPU.
RC1 p95: 73.2701 / 76.8675 / 76.6319 ms. Candidate: 75.6954 / 75.0890 / 74.3092 ms.
Medians: 76.6319 versus 75.0890 ms; maximum peak RSS: 455663616 versus 455176192
bytes; initialization medians: 3.248207 versus 3.283451 seconds. This passes the
predeclared +5% p95 / +16MiB memory gates, not a claim of substantial speedup.
The small extracted RC2 implementation must separately reproduce the candidate;
the handoff ledger records final-source and archive checks. Memory includes the
evaluator's catalog too; the ZIP checker is not a standardized speed benchmark.

Default scoring uses zero model tokens and has estimated API cost RMB0. This is
not a claim that development was free: the last recorded API experiment ledger
conservatively reserved/charged RMB9.110809, including uncertain requests. That
is a development estimate, not a provider invoice. No API calls occur in this stage.

## Why freeze here, and what remains

This round studied product-search methods in the Amazon Reviews 2023/BLaIR
paper, Amazon ESCI/KDD Cup author solutions, retrieve/rerank guides and SQLite
documentation. The implementation is original, without copied external code or
new models/data. Category/phrase evidence, conjunction/RRF routing, IDF,
clarification, dominance and cache/SQL controls were evaluated. Only conservative
category-head ordering is promoted. A broader phrase-head candidate raised
Shadow overall MRR but reduced Override MRR by .000463; it was still rejected.
Pool policies improved HR/MTTC but harmed at least one scenario's MRR. Dense,
cross-encoder and paid candidates from earlier rounds also remain disabled.

Finite experiments cannot prove global optimality. Under the unchanged strict
non-regression rule, no tested further method improved HR/MTTC without a tradeoff.

Remaining weaknesses: semantic lexical-recall gap, fixed clarification order,
limited personalization and workflow adaptation, soft rather than guaranteed
constraints, non-zero index startup and no real-user/business validation. Public
results are not a prediction of hidden performance or commercial conversion.
More time should go to target-blind semantic retrieval and independently validated
question selection, not answer-specific rules or post-deadline tuning.

The final evaluation package, cross-machine signoff, public video, final Devpost
description and submitted public repository commit remain separate acceptance
items. A passing local checker does not complete them.
