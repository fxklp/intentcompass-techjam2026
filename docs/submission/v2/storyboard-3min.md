# IntentCompass V2 three-minute storyboard

Status: synchronized to accepted main
`5bd5d6fac91aad718862baded99eaf8b21cdd2bf` under TASK-204. Total planned
runtime is exactly 180 seconds. Recording remains `Pending`.

## Production rules

Capability footage must come from one clean checkout of the final recording
commit. Show each command before its output. Silent waiting may be shortened,
but the edit must disclose the cut and retain the command, result, and exit
status from the same run. Explanatory diagrams and evidence cards provide
context; they are not execution evidence.

The S02 architecture is only the formal path reached through
`starter.agent.Agent`. The merged dual-route retrieval experiment is discussed
as an isolated engineering decision in S09 and must not appear as a node in the
formal runtime diagram.

## Timed script

| Time | Story beat and recorded picture | Voice-over | On-screen subtitle | Evidence |
|---|---|---|---|---|
| 0:00-0:15 | S01. Title, exact-match Top-10 objective, and a compact 10-turn timeline. | “Shopping intent changes during a conversation. The challenge is to place the hidden catalog item in the first ten valid recommendations, as early and as highly as possible, using only the Agent contract.” | `Goal: early, high-ranked exact parent_asin match` | O01, O03 |
| 0:15-0:35 | S02. Formal architecture only: `reset -> SessionState`, then `respond -> state update and replacement -> lexical query -> SQLite FTS5/BM25 retrieval -> lexical constraint rerank -> deterministic clarification -> Top 10 response`. | “IntentCompass is a deterministic, CPU-only Python Agent. It updates structured, replaceable preferences, searches one SQLite FTS5 index scored with BM25, applies a constraint-aware lexical reranker, asks a non-repeating clarification, and returns its best current Top 10.” | `Formal Agent: structured state \| FTS5/BM25 \| lexical rerank \| clarification \| Top 10` | I01-I06 in `requirements-matrix.md` |
| 0:35-0:45 | S03. In a terminal, show `git rev-parse HEAD`, a clean `git status --short`, then type `python demo/run_demo.py`. | “This is the formal Agent at a visible, clean commit. The command calls it through the deterministic headless harness.” | `Real formal Agent + deterministic simulator` | O05, O06, P01 |
| 0:45-1:00 | S04. Keep turns 1 and 2 legible. Highlight customer text, `Active state`, `Ask attribute`, and the ordered Top 10. | “The first message creates a feature constraint. The second adds material preferences. The Agent exposes the current active intent, its search query, the clarification field, and ten ordered identifiers.” | `Active Intent grows from disclosed preferences` | O03, O04 |
| 1:00-1:10 | Continue the same terminal recording at turn 3. | “A no-preference answer for color does not invent a color constraint. The current material and feature state remains explicit.” | `Turn 3: no color preference, no fabricated constraint` | O04 |
| 1:10-1:25 | S05. Show turn 4 in full and highlight the before/after state. | “On turn four, the customer replaces the earlier requirement with polyester. The stale feature and duplicate material values disappear. The old preferences are cleared; the query keeps the category and uses the new material.” | `Intent Override: stale values removed, new value retained` | O04, I02 |
| 1:25-1:45 | S06. Show turn 5, the ten identifiers, target rank 8, and the final result. | “The next message adds button closure and hand-wash constraints. The updated Top 10 contains the target at rank eight. This is the first score-eligible hit, on turn five.” | `public_0183 \| first hit: turn 5 \| rank: 8` | C05 in `claim-evidence-ledger.md` |
| 1:45-2:15 | S07. Record `python scripts/team_gate.py --full-eval`. Shorten only silent computation and show `Ran 49 tests`, evaluator JSON, and `TEAM GATE PASSED`. | “Forty-nine tests pass. Across 200 public sessions, the formal Agent reports HitRate at 10 of 0.91, MRR 0.624024, MTTC 4.255, and TechnicalScore 0.777107. TechnicalScore supports Technical Execution; it is not the competition’s final overall score.” | `49 tests \| 200 sessions \| HR@10 0.91 \| MRR 0.624024 \| MTTC 4.255 \| TechnicalScore 0.777107 \| not final overall score` | C06, C15, and C16 in `claim-evidence-ledger.md` |
| 2:15-2:35 | S08. Use a real CLI command to display the committed historical runtime JSON, including its measurement commit and environment. | “The formal path uses no model API, needs no scoring-time network, reports zero model tokens, and has estimated API cost of zero dollars. The historical Windows and Python 3.13.9 run averaged 37.736 milliseconds with p95 76.583. These are reference values from the recorded measurement commit, not a new main benchmark.” | `Historical reference \| commit 4247815 \| Win11 / Python 3.13.9 \| tokens 0 \| API cost USD 0 \| mean 37.736 ms \| p95 76.583 ms` | C08-C09 in `claim-evidence-ledger.md` |
| 2:35-2:45 | S09. Show a limitation and experiment-decision card, not a formal architecture extension. | “The merged dual-route experiment remains isolated because MRR fell and latency rose. The formal Agent stays lexical, without dense retrieval, deep personalization, or a private-set guarantee.” | `Merged experiment != enabled Agent \| lexical formal path \| no dense retrieval \| private set unknown` | E01-E04 and C11 in `claim-evidence-ledger.md` |
| 2:45-3:00 | S10. Show four names and verified responsibilities. | “Fang Tianchen built the initial Agent and integration. Liu Chunyi delivered cross-platform validation and independent review. Wang Siwen documented the isolated retrieval experiment and its trade-offs. Cheng Xianyun produced analysis, the truthful demo, and submission materials.” | `Fang: initial Agent/integration \| Liu: cross-platform QA/review \| Wang: isolated retrieval evidence \| Cheng: analysis/demo/submission` | Team-contribution evidence in `claim-evidence-ledger.md` |

## Edit notes

Keep terminal text readable at delivery resolution. Do not replace recorded
output with retyped text. The 49-test count and current evaluator values were
reproduced at the TASK-204 main baseline; rerun them at the eventual recording
commit. If they change, update narration, subtitles, and the ledger together.
The final audio must be timed at normal speaking speed. Shorten wording rather
than accelerating the voice.
