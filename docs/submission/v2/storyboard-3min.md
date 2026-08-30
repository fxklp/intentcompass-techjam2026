# IntentCompass V2 three-minute storyboard

Status: narration and subtitle draft. Total planned runtime is exactly 180
seconds. Recording and upload are out of this local documentation step.

## Production rules

The capability footage must come from one clean checkout of the final commit.
Show each command before its output. Idle waiting may be shortened in editing,
but the edit must say so and must preserve the command, result, and exit status
from the same run. Explanatory diagrams and text cards may clarify the system.
They are not execution evidence.

## Timed script

| Time | Story beat and recorded picture | Voice-over | On-screen subtitle | Evidence |
|---|---|---|---|---|
| 0:00-0:15 | S01. Title, exact-match Top-10 objective, and a compact 10-turn timeline. | “Shopping intent changes during a conversation. The challenge is to place the hidden catalog item in the first ten valid recommendations, as early and as highly as possible, using only the Agent contract.” | `Goal: early, high-ranked exact parent_asin match` | R01, R03 |
| 0:15-0:35 | S02. Explanatory architecture diagram: `reset -> SessionState`, then `respond -> state replacement -> route -> FTS5/BM25 retrieval -> rerank -> clarification -> response`. | “IntentCompass is a deterministic, CPU-only Python Agent. It stores structured, replaceable preferences, builds a retrieval query, reranks catalog candidates, asks one clarification, and returns its best current Top 10 on every turn.” | `Structured active intent | retrieval | rerank | clarification | Top 10` | R02, R09 |
| 0:35-0:45 | S03. In a terminal, show `git rev-parse HEAD`, a clean `git status --short`, then type `python demo/run_demo.py`. | “This is the real repository at a visible commit. The command calls the submitted Agent through the deterministic headless harness.” | `Real Agent + deterministic simulator. No target passed to Agent` | R05, R06, R12 |
| 0:45-1:00 | S04. Keep turns 1 and 2 legible. Highlight customer text, `Active state`, `Ask attribute`, and the ordered Top 10. | “The first message creates a feature constraint. The second adds material preferences. The Agent exposes the current active intent, its search query, the clarification field, and ten ordered identifiers.” | `Active Intent grows from disclosed preferences` | R03, R04 |
| 1:00-1:10 | Continue the same terminal recording at turn 3. | “A no-preference answer for color does not invent a color constraint. The current material and feature state remains explicit.” | `Turn 3: no color preference, no fabricated constraint` | R04 |
| 1:10-1:25 | S05. Show turn 4 in full and highlight the before/after state. | “On turn four, the customer replaces the earlier requirement with polyester. The stale feature and duplicate material values disappear. The active intent and retrieval query now contain only the replacement.” | `Intent Override: stale values removed, new value retained` | R04, R09 |
| 1:25-1:45 | S06. Show turn 5, the ten identifiers, target rank 8, and the final result. | “The next message adds button closure and hand-wash constraints. The updated Top 10 contains the target at rank eight. This is the first score-eligible hit, on turn five.” | `public_0183 | first hit: turn 5 | rank: 8` | C05 in `claim-evidence-ledger.md` |
| 1:45-2:15 | S07. Record `python scripts/team_gate.py --full-eval`. Shorten only silent computation and show the final JSON plus `TEAM GATE PASSED`. | “Across all 200 public sessions, the unchanged evaluator reports HitRate at 10 of 0.91, MRR 0.624024, MTTC 4.255, and a recommended TechnicalScore of 0.777107. Intent Override remains the weakest scenario at 0.766667 HitRate at 10.” | `200 public sessions | HR@10 0.91 | MRR 0.624024 | MTTC 4.255 | TechnicalScore 0.777107` | C06-C07 in `claim-evidence-ledger.md` |
| 2:15-2:35 | S08. Record `python scripts/benchmark_runtime.py`, then show a compact evidence card with the committed reference environment. | “The primary path uses no model API, needs no scoring-time network, reports zero model tokens, and has estimated API cost of zero dollars. On the committed Windows reference run, 833 responses averaged 37.736 milliseconds with p95 76.583 milliseconds. Latency is machine-specific.” | `Offline primary path | tokens 0 | API cost USD 0 | reference mean 37.736 ms, p95 76.583 ms` | C08-C09 in `claim-evidence-ledger.md` |
| 2:35-2:50 | S09. Limitation card, with failure categories tied to the repository analysis. | “The current lexical retriever can miss semantic matches. Index construction adds startup cost, personalization is limited, and public results do not predict the organizer’s 800 private sessions.” | `Limits: lexical recall | startup cost | limited personalization | private set unknown` | `docs/submission/first-version-report.md` and `reports/analysis/TASK-201-failure-taxonomy.md` |
| 2:50-3:00 | S10. Show merged pull-request numbers and merge SHAs only. | “Merged evidence credits integration hardening, QA coverage, failure analysis, and demo truthfulness across PRs one, two, four, and five. Unmerged work is excluded.” | `Team evidence: merged PRs #1, #2, #4, #5 only` | R11 |

## Edit notes

Keep terminal text large enough to read at the delivery resolution. Do not
replace recorded output with retyped text. If the final evaluator or benchmark
values differ from the committed reference, update the narration, subtitles,
and claim ledger together before export. The final audio should be timed once at
normal speaking speed. If it exceeds 180 seconds, shorten wording rather than
speeding up the voice.
