# V2 requirement, policy, implementation, evidence, and shot matrix

> **Historical TASK-203 matrix.** It predates TASK-306 and is not the final
> capability or submission status.

Status: reviewer-requested revision for PR #7, prepared locally. No media has
been recorded or uploaded.

This matrix keeps three sources separate:

- `Official requirement` comes from the competition specification, submission
  rules, API contract, or evaluation configuration.
- `Team policy` is an internal evidence or production rule. It must not be
  presented as an organizer requirement.
- `Current implementation` describes only behavior present at the TASK-203
  base. `Partial` and `Not implemented` items must not be narrated as complete.

## Official requirements

| ID | Requirement | Repository evidence and immutable anchor | Planned shot | Status |
|---|---|---|---|---|
| O01 | Find a hidden target product as early and as highly ranked as possible in a multi-turn session. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`, sections `Objective` and `Session Protocol`. | S01 states the exact-match Top-10 objective. | Covered |
| O02 | Expose `Agent.reset(session_id, user_profile)` and `Agent.respond(session_id, user_message, turn, top_k)`. | `docs/agent_api_contract.json` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`. | S03 launches the real Agent through the headless harness. | Covered |
| O03 | Return natural `message`, structured `ask_attribute`, and ordered recommendations. Only the first 10 valid unique `parent_asin` values are scored. | `docs/submission_rules.md`, `docs/agent_api_contract.json`, and `docs/evaluation_config.json` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`. | S04-S06 keep the response fields and Top 10 legible. | Covered |
| O04 | Handle Buying, Browsing, Intent Override, and Boundary sessions. An override cannot score before the replacement intent arrives. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`. | S04-S06 follow `public_0183` through replacement and the eligible hit. | Covered |
| O05 | Formal scoring uses the automated Agent contract and headless evaluator pipeline. | Scope and protocol in `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`, plus `evaluator/local_evaluator.py` at base `a81b042d3010fb254519ab56573d03beba111396`. | S03-S08 use real repository commands and generated output. | Covered |
| O06 | Provide reproducible setup and a scoring path that does not depend on undeclared services or credentials. | `docs/submission_rules.md` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`; accepted demo evidence at `5bd84367c0103163eda681b5dc64727b147e9210`. | S03 launches the demo; S07 runs the full evaluator. | Covered |
| O07 | Report HitRate@10, MRR, MTTC, Efficiency, and the recommended TechnicalScore. TechnicalScore is an objective input to Technical Execution, not the competition's final overall score. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`; measured result in `reports/metrics/first-version-runtime.json` at `9c59d4874db29dee1d9d839c8339ad870f2a3e46`. | S07 shows the evaluator result and states the score boundary. | Covered evidence, capture Pending |
| O08 | Disclose architecture, model choice, latency, token use, estimated cost, limitations, and team contributions. | Final deliverables and model policy in `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`; disclosure evidence at `94e25c633751ad37fbe0499dc1a684959a148358`. | S02 and S08-S10 cover these topics without exceeding the evidence. | Covered evidence, production Pending |

## Team policies

| ID | Policy | Repository evidence and immutable anchor | Planned shot | Status |
|---|---|---|---|---|
| P01 | Do not present mock output, retyped terminal text, prepared screens, or unsupported claims as executed behavior. | Evidence boundary in `docs/contracts/architecture.md` at `8e88d75cbd8f3a1a6c3f6fcfebdd3bc22b9d85bb`; TASK-203 task card. | S03-S08 begin with visible commands and retain output from the recorded process. | Recording Pending |
| P02 | Distinguish the accepted founding baseline, current team responsibilities, and later completed contributions. The founding baseline must use immutable accepted-mainline evidence; later teammate work counts only after its supporting PR is merged. | `docs/submission/first-version-report.md` at `94e25c633751ad37fbe0499dc1a684959a148358`; `docs/team/OWNERSHIP.md`; role, open-PR, merged-PR, and SHA evidence is centralized in `claim-evidence-ledger.md`. | S10 credits Fang Tianchen's accepted initial Agent/demo baseline and names all four responsibilities; the ledger prevents PR #6 or PR #8 from being narrated as completed while open. | Covered through remote status check on 2026-08-30 |
| P03 | Record capability footage from one identified clean commit and disclose shortened waiting time. | TASK-203 task card and `shot-list.md`. | S03, S07, and S08 show commit and clean status; edited waits are labeled. | Production Pending |

## Current implementation and capability gaps

| ID | Capability at base `a81b042d...` | Repository evidence | Planned shot | Status |
|---|---|---|---|---|
| I01 | Thin official adapter delegates to the core Agent. | `starter/agent.py`, `solution/agent_impl.py` | S02-S03 | Implemented |
| I02 | Structured session state replaces superseded preferences and clears no-preference slots. | `solution/state.py`, `tests/core/test_state.py` | S04-S06 | Implemented |
| I03 | Retrieval query is rebuilt from the current category and active preference values. | `SessionState.retrieval_query` in `solution/state.py` | S04-S06 | Implemented |
| I04 | Candidate retrieval uses one in-memory SQLite FTS5/BM25 lexical index with deterministic popularity fallback. | `_BaselineBM25Index` in `solution/agent_impl.py` | S02, S08 | Implemented |
| I05 | Candidate reranking uses lexical preference overlap, exact value matches, budget distance when available, and retrieval rank. | `solution/ranker.py` | S02 | Implemented |
| I06 | Clarification uses a fixed attribute priority while skipping already asked, unconstrained, or populated attributes. | `solution/question_policy.py`, `tests/core/test_state.py` | S04-S06 | Implemented deterministic policy |
| I07 | Learned uncertainty or question-value based dynamic clarification. | No such scoring exists in `solution/question_policy.py`; limitation recorded in `docs/submission/first-version-report.md`. | S09 limitation | Partially implemented: state-aware skipping only |
| I08 | Buying-versus-Browsing routing. | `solution/agent_impl.py` uses the same pipeline for every session. | Not shown as a capability | Not implemented |
| I09 | Dual-route or multi-route retrieval. | The required base has one `_BaselineBM25Index.search` path. PR #8 head `23814dbb2bba9de9f338b26aeffbf23ceb0efb82` is an open, unmerged experiment and is not part of the current submission implementation. | Not shown as a capability | Not implemented at base; open work exists |
| I10 | Dense retrieval. | No embedding model, dense index, or dense search path is present under `solution/`. | Not shown as a capability | Not implemented |
| I11 | Hybrid lexical-plus-dense retrieval. | Only the lexical FTS5/BM25 path is present. | Not shown as a capability | Not implemented |
| I12 | Semantic reranking. | `solution/ranker.py` uses lexical overlap and numeric budget distance, not embeddings or a semantic model. | Not shown as a capability | Not implemented |
| I13 | Deep aggregate-profile personalization. | `SessionState` stores a copied profile, but the current retrieval and ranker do not consume it. | S09 limitation | Partially implemented: safe storage only |
| I14 | Offline primary path with zero reported model tokens and no scoring-time network requirement. | `reports/metrics/first-version-runtime.json` at `9c59d4874db29dee1d9d839c8339ad870f2a3e46`. | S08 | Implemented and measured |

## Coverage decision

The three-minute story may claim I01-I06 and I14 within their evidence bounds.
I07 and I13 must be described as partial. I08-I12 must remain absent from the
architecture and capability narration, except when named explicitly as gaps or
limitations. Recording, graphics, audio, subtitle timing, and final media remain
Pending.
