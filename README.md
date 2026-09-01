# IntentCompass — Track 4 Conversational Product Search

IntentCompass is a local-first, CPU-based Python shopping Agent for TikTok
TechJam 2026 Track 4. It maintains replaceable multi-turn intent, routes Buying
and Browsing requests, searches a frozen 50,000-product catalog, asks structured
clarifying questions and returns an ordered Top 10 of valid `parent_asin` values.

The accepted implementation is commit
`1513020a35fb54700e2a63f2265e4d80ca10af48`, merged through PR #12. It does
not modify the official evaluator, catalog, labels, scoring or stopping rules.

## What it implements

- structured preference accumulation, `no preference` handling and intent override;
- Buying/Browsing workflow routing and recovery after rejection or lexical miss;
- one in-memory SQLite FTS5 index serving keyword, category, exact-constraint
  and query-expansion routes;
- three-valued constraint semantics: satisfied, conflict and unknown;
- on-demand in-memory MiniLM dense retrieval and bounded category diversity;
- guarded lexical ordering plus an on-demand local MS MARCO MiniLM cross-encoder;
- early over-generality cutoff, dynamic clarification and deterministic fallback;
- optional, explicit, consent-marked profile handoff between caller-managed sessions;
- optional Qwen/DeepSeek adapters with strict output validation, cost limits,
  circuit breaking and offline fallback.

Semantic work is demand-driven. Missing or invalid model assets fail closed to
the lexical pipeline, and no model is downloaded at runtime.

## Required interface

The official entry is `starter.agent.Agent`:

```python
from starter.agent import Agent

agent = Agent("data/catalog.jsonl")
try:
    agent.reset("example", {})
    response = agent.respond("example", "I'm looking for shoes.", 1, 10)
finally:
    agent.close()
```

`response` contains a natural `message`, one allowed `ask_attribute`, up to ten
ordered unique catalog IDs, and model `usage` when applicable.

## Setup

Use Python 3.12 or 3.13 with SQLite FTS5.

### Base local path

```text
python scripts/setup_data.py
python demo/run_demo.py
python -m evaluator.local_evaluator --output results.json
```

The base path uses only the Python standard library and runs without credentials,
GPU, external database or scoring-time network access.

### Full local semantic path

```text
python -m venv .venv
# Windows: .venv\Scripts\python.exe
# macOS/Linux: .venv/bin/python
python -m pip install -r requirements-semantic.txt
python scripts/setup_data.py
python scripts/build_semantic_index.py --download
python scripts/task306_evaluate.py --split public --semantic local --output results.json
```

The one-time semantic build downloads pinned ONNX models, verifies their source
revisions and builds a catalog-derived dense matrix. Generated assets are kept
outside Git. Set `INTENTCOMPASS_SEMANTIC_ASSETS` only when assets are stored
outside the default `artifacts/semantic` directory.

## Reproduced Public results

These are development-set results over the released 200-session Public set, not
the organizer's private score:

| Metric | IntentCompass |
|---|---:|
| HitRate@10 | 0.980000 |
| MRR | 0.696861 |
| MTTC | 3.755000 |
| Efficiency | 0.724500 |
| TechnicalScore | 0.843958 |

TechnicalScore is an objective input to Technical Execution, not the final
competition score. Public, a deterministic Shadow set, and two existing
800-session synthetic confirmation sets matched the frozen RC3 metrics exactly.
Repeated runs of those sets are reproduction evidence, not fresh holdouts.

The demonstrated Intent Override case `public_0183` first becomes score-eligible
after replacement intent, then hits at turn 5, rank 8. The demo harness knows the
public target only for display; the Agent never receives it.

## Models, APIs, cost and resources

- Dense encoder: `sentence-transformers/all-MiniLM-L6-v2`, pinned revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (Apache-2.0).
- Local reranker: `cross-encoder/ms-marco-MiniLM-L6-v2`, pinned revision
  `233902d25c440f23af6f7d6e94d2946bac0bee0a` (Apache-2.0).
- CPU dependencies: NumPy, ONNX Runtime and Hugging Face Tokenizers, pinned in
  `requirements-semantic.txt`.
- Optional APIs: Qwen and DeepSeek compatible chat endpoints. They are not
  required for Public reproduction or final local operation.
- Successful Qwen integration proof: model `qwen3.8-max`, 3,726 prompt and 54
  completion tokens, conservative cost delta RMB 0.058274. This proves the
  adapter works; it is not claimed as a metric improvement.
- Public run: zero model tokens and zero network attempts because no scripted
  Public turn required semantic execution.
- Independent Win11/Python 3.12 validation with verified local assets measured
  about 143 ms p95. Latency is machine-specific and is not an official limit.

API keys must be supplied by environment variables (`DASHSCOPE_API_KEY` or
`DEEPSEEK_API_KEY`) and must never be committed. The default local path needs
neither variable.

## Verification

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python demo/run_demo.py
```

The final candidate passed 209 repository tests; independent Win11 acceptance
also exercised the real dense and local cross-encoder path. See
[`docs/release/task306/HANDOFF.md`](docs/release/task306/HANDOFF.md) for the
evidence boundaries and exact asset procedure.

## Limitations

- Demand-driven semantic branches are proven separately because the scripted
  Public conversations did not require them.
- Parent-level catalog metadata may omit variant attributes; missing data stays
  unknown rather than being treated as a match.
- Local model assets add one-time build time, memory and platform-dependent latency.
- Public and synthetic results do not predict the private set or real business conversion.
- No UI, real transaction service, foundational-model training, multimodal
  processing or industrial external vector database is included.

## Team contributions

- **Fang Tianchen:** team lead, algorithm and architecture direction, original
  end-to-end Agent, optimization and final integration.
- **Liu Chunyi:** QA, cross-platform CI/contracts, release reproduction and
  independent code reviews.
- **Cheng Xianyun:** failure analysis, evidence organization, Windows testing,
  demo storyboard and final video production.
- **Wang Siwen:** retrieval experiments, benchmark isolation, evidence-integrity
  fixes and independent semantic acceptance testing.

AI coding assistance supported implementation, tests and documentation; the
team remains responsible for the design, verification and submitted claims.

## Data and third-party notices

The competition catalog derives from Amazon Reviews 2023. See
[`DATA_ATTRIBUTION.md`](DATA_ATTRIBUTION.md) and
[`docs/submission/THIRD_PARTY_NOTICES.md`](docs/submission/THIRD_PARTY_NOTICES.md).
The catalog, model binaries, generated dense index, credentials and private
evaluation data are not committed.

For judges, use the copy-ready
[`testing instructions`](docs/submission/TESTING_INSTRUCTIONS.md) and
[`final report`](docs/submission/FINAL_REPORT.md).
