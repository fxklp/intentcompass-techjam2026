# Method, measurements and limitations

## Actual submitted default

IntentCompass is a deterministic non-LLM shopping Agent. A thin official adapter
delegates to a modular implementation. `reset` creates independent state;
`respond` updates preference slots, retrieves up to 50 candidates from one
in-memory SQLite FTS5/BM25 index, reranks by visible preferences and asks a
non-repeating clarification using a fixed priority order. Invalid IDs and
duplicate recommendations are not generated intentionally; acceptance checks
validate every Public response before the unchanged evaluator scores it.

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

The local Public evaluator produces HR@10 .91, MRR .624024, MTTC 4.255,
Efficiency .6745 and TechnicalScore .777107 over 200 sessions. The release checker
regenerates aggregate and all per-session results from the packaged source.
The example demo hits on the first eligible turn 5 at rank 8. It is a selected
Public demonstration, not a random unseen success rate.

Earlier aggregate-only checks produced Shadow HR .895 / MRR .630488 / MTTC 3.805.
A predeclared new synthetic seed produced .93 / .666312 / 3.645. Both are team
synthetic robustness sets, not official final results; different-set absolute
scores are not algorithm gains. No retuning followed those confirmation checks.

At the pre-packaging runtime freeze dbf78d429686337273d05f92795e6c88d0e0bf8b,
three independent Windows/Python 3.13.9 measurements gave p95 response latency
71.4605 / 71.5195 / 72.4481ms (median 71.5195ms), maximum process peak memory
450809856 bytes, and median Agent initialization 3.199749s. Timing is machine-
specific; peak memory includes the evaluator's catalog as well as Agent state.
Packaging changes do not claim another performance gain. The compact release
checker reports correctness, not a standardized organizer speed score.

Default scoring uses zero model tokens and has estimated API cost RMB0. This is
not a claim that development was free: the last recorded API experiment ledger
conservatively reserved/charged RMB9.110809, including uncertain requests. That
is a development estimate, not a provider invoice. No API calls occur in this stage.

## Why freeze here, and what remains

Field reranking improved overall MRR in some experiments but slightly reduced
Buying MRR. Dense/cross-encoder and paid candidates also failed one or more
quality gates. They remain disabled, rather than being sold as reliable gains.

Remaining weaknesses: semantic lexical-recall gap, fixed clarification order,
limited personalization and workflow adaptation, soft rather than guaranteed
constraints, non-zero index startup and no real-user/business validation. Public
results are not a prediction of hidden performance or commercial conversion.
More time should go to target-blind semantic retrieval and independently validated
question selection, not answer-specific rules or post-deadline tuning.

The final evaluation package, cross-machine signoff, public video, final Devpost
description and submitted public repository commit remain separate acceptance
items. A passing local checker does not complete them.
