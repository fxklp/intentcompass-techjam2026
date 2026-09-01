# IntentCompass

## Inspiration

Conversational shopping is difficult because intent is incomplete, changes over
time and often contains “no preference” answers. A search system that simply
appends every message can keep stale constraints and miss the exact product.
IntentCompass treats active intent as explicit, replaceable state and changes
retrieval strategy as the conversation evolves.

## What it does

IntentCompass is a local-first Track 4 Python Agent that returns an ordered Top
10 from the supplied 50,000-product catalog on every turn. It supports
Buying/Browsing routing, intent override, three-valued constraints, multi-route
lexical recall, on-demand dense retrieval, bounded diversity, guarded local
cross-encoder ranking, proactive clarification, recovery after rejection and an
explicit consent-based profile handoff.

## How we built it

The official `Agent.reset`/`Agent.respond` adapter delegates to modular session,
workflow, retrieval and ranking code. One in-memory SQLite FTS5 index serves
keyword, category, exact-constraint and expansion routes. Pinned ONNX MiniLM
models provide optional in-memory dense recall and local cross-encoder ranking
only when a request qualifies. Missing model assets fail closed to the lexical
path. The evaluator, data, metrics and stopping rules are unchanged.

## Results

On all 200 released Public sessions, IntentCompass reproduced HitRate@10 0.98,
MRR 0.696861 and MTTC 3.755, for TechnicalScore 0.843958. TechnicalScore is an
input to Technical Execution, not the overall competition result. Our live demo
shows an Intent Override session in which stale intent is removed on turn 4 and
the exact target first appears on turn 5 at rank 8. The target is visible only to
the evaluator/demo harness, never to the Agent.

## Built with

- Python 3.12/3.13 and SQLite FTS5
- NumPy, ONNX Runtime and Hugging Face Tokenizers
- `all-MiniLM-L6-v2` dense encoder and `ms-marco-MiniLM-L6-v2` cross-encoder
- Optional Qwen/DashScope and DeepSeek adapters with bounded cost and fallback
- Git, GitHub Actions and AI-assisted coding tools for implementation and QA
- Organizer-provided Amazon Reviews 2023-derived text catalog and sessions

## Feasibility, cost and limitations

The main system is CPU-based, text-only and in-memory; it requires no GPU,
training, multimodal processing or industrial vector database. The Public run
attempted no network calls and used zero model tokens. Independent Win11
validation measured about 143 ms p95 with local semantic assets, which is
machine-specific. A successful optional Qwen proof cost an estimated RMB
0.058274 but is not claimed as a metric improvement. Public and synthetic tests
do not guarantee the organizer's private-set or real business performance.

## Team

Fang Tianchen led architecture, algorithms and integration. Liu Chunyi handled
cross-platform QA and reviews. Cheng Xianyun handled analysis, evidence, Windows
testing and video production. Wang Siwen contributed retrieval experiments,
benchmark/evidence integrity and semantic QA. AI coding assistance was used;
the team owns the final design and verification.

## Links to fill before submission

- Public repository: https://github.com/fxklp/intentcompass-techjam2026
- Public 3-minute YouTube demo: `PASTE_PUBLIC_YOUTUBE_URL_HERE`
