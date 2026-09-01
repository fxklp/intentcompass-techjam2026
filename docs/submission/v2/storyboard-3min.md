# IntentCompass V2 three-minute storyboard

> **Superseded TASK-203 storyboard.** It is kept as history and contains old
> metrics/capability boundaries. Do not use it for the final TASK-306 video.

Status: reviewer-requested narration and subtitle revision for PR #7. Total
planned runtime is exactly 180 seconds. Recording remains out of scope.

## Production rules

The capability footage must come from one clean checkout of the final commit.
Show each command before its output. Idle waiting may be shortened in editing,
but the edit must say so and must preserve the command, result, and exit status
from the same run. Explanatory diagrams and text cards may clarify the system.
They are not execution evidence.

## Timed script

| Time | Story beat and recorded picture | Voice-over | On-screen subtitle | Evidence |
|---|---|---|---|---|
| 0:00-0:15 | S01. Title, exact-match Top-10 objective, and a compact 10-turn timeline. | “Shopping intent changes during a conversation. The challenge is to place the hidden catalog item in the first ten valid recommendations, as early and as highly as possible, using only the Agent contract.” | `Goal: early, high-ranked exact parent_asin match` | O01, O03 |
| 0:15-0:35 | S02. Explanatory architecture diagram: `reset -> SessionState`, then `respond -> state update and replacement -> lexical query -> SQLite FTS5/BM25 retrieval -> lexical constraint rerank -> deterministic clarification -> Top 10 response`. | “IntentCompass is a deterministic, CPU-only Python Agent. It updates structured, replaceable preferences, searches one SQLite FTS5 index scored with BM25, applies a constraint-aware lexical reranker, asks a non-repeating clarification, and returns its best current Top 10.” | `Structured state | lexical retrieval | constraint rerank | clarification | Top 10` | I01-I06 in `requirements-matrix.md` |
| 0:35-0:45 | S03. In a terminal, show `git rev-parse HEAD`, a clean `git status --short`, then type `python demo/run_demo.py`. | “This is the real repository at a visible commit. The command calls the submitted Agent through the deterministic headless harness.” | `Real Agent + deterministic simulator. No target passed to Agent` | O05, O06, P01 |
| 0:45-1:00 | S04. Keep turns 1 and 2 legible. Highlight customer text, `Active state`, `Ask attribute`, and the ordered Top 10. | “The first message creates a feature constraint. The second adds material preferences. The Agent exposes the current active intent, its search query, the clarification field, and ten ordered identifiers.” | `Active Intent grows from disclosed preferences` | O03, O04 |
| 1:00-1:10 | Continue the same terminal recording at turn 3. | “A no-preference answer for color does not invent a color constraint. The current material and feature state remains explicit.” | `Turn 3: no color preference, no fabricated constraint` | O04 |
| 1:10-1:25 | S05. Show turn 4 in full and highlight the before/after state. | “On turn four, the customer replaces the earlier requirement with polyester. The stale feature and duplicate material values disappear. The active intent and retrieval query now contain only the replacement.” | `Intent Override: stale values removed, new value retained` | O04, I02 |
| 1:25-1:45 | S06. Show turn 5, the ten identifiers, target rank 8, and the final result. | “The next message adds button closure and hand-wash constraints. The updated Top 10 contains the target at rank eight. This is the first score-eligible hit, on turn five.” | `public_0183 | first hit: turn 5 | rank: 8` | C05 in `claim-evidence-ledger.md` |
| 1:45-2:15 | S07. Record `python scripts/team_gate.py --full-eval`. Shorten only silent computation and show the final test summary, evaluator JSON, and `TEAM GATE PASSED`. | “Across all 200 public sessions, the unchanged evaluator reports HitRate at 10 of 0.91, MRR 0.624024, MTTC 4.255, and a recommended TechnicalScore of 0.777107. This composite is an input to Technical Execution, not the competition's final overall score.” | `200 public sessions | HR@10 0.91 | MRR 0.624024 | MTTC 4.255 | TechnicalScore 0.777107 | not final overall score` | C06, C07, and C15 in `claim-evidence-ledger.md` |
| 2:15-2:35 | S08. Record `python scripts/benchmark_runtime.py`, then show a compact evidence card with the committed reference environment. | “The primary path uses no model API, needs no scoring-time network, reports zero model tokens, and has estimated API cost of zero dollars. On the committed Windows reference run, 833 responses averaged 37.736 milliseconds with p95 76.583 milliseconds. Latency is machine-specific.” | `Offline primary path | tokens 0 | API cost USD 0 | reference mean 37.736 ms, p95 76.583 ms` | C08-C09 in `claim-evidence-ledger.md` |
| 2:35-2:45 | S09. Limitation card, with failure categories tied to the repository analysis. | “The lexical retriever can miss semantic matches. Startup has indexing cost, personalization is limited, and public results do not predict the organizer’s private sessions.” | `Limits: lexical recall | startup cost | limited personalization | private set unknown` | `docs/submission/first-version-report.md` and `reports/analysis/TASK-201-failure-taxonomy.md` |
| 2:45-3:00 | S10. Show the four team members and their real, submission-relevant responsibilities. | “Fang Tianchen built the first end-to-end Agent and demo baseline, reaching public HitRate at 10 of 0.91. Wang Siwen owns backend retrieval. Liu Chunyi and Cheng Xianyun handle testing and demo production. Later work is credited only after merge.” | `Fang Tianchen: initial Agent + demo baseline, HR@10 0.91 | Wang Siwen: backend/retrieval | Liu Chunyi + Cheng Xianyun: testing/demo production` | Baseline and later merged-contribution evidence in `claim-evidence-ledger.md` |

## Edit notes

Keep terminal text large enough to read at the delivery resolution. Do not
replace recorded output with retyped text. If the final evaluator or benchmark
values differ from the committed reference, update the narration, subtitles,
and claim ledger together before export. The final audio should be timed once at
normal speaking speed. If it exceeds 180 seconds, shorten wording rather than
speeding up the voice. Display the test count generated by the final submission
commit rather than preserving an earlier count in the edit.
