# V2 claim and evidence ledger

> **Historical TASK-203 ledger.** It predates TASK-306. Use the final report and
> TASK-306 handoff for current claims.

Status: reviewer-requested revision for PR #7, prepared locally. `Verified`
claims may be used exactly as bounded below. `Partial` and `Pending` claims must
not be narrated as complete.

Source classes in this ledger are `Official rule`, `Current implementation`,
`Measured result`, and `Team policy`. They are intentionally kept distinct.

## Official rules and measured claims

| Claim | Source class | Safe wording | Evidence | Commit anchor | Status |
|---|---|---|---|---|---|
| C01 | Official rule | “The challenge scores exact catalog `parent_asin` matches in the first 10 valid unique recommendations, over at most 10 turns.” | `docs/competition_specification.md`; `docs/evaluation_config.json` | `34078351e1c3615e5505a2e829600b56a542e462`; `2a6cc8e776da66ce69b1cbd237838fbc43f32587` | Verified |
| C02 | Current implementation | “IntentCompass is a deterministic, CPU-only Python Agent whose primary scoring path requires no network or model API.” | `docs/submission/first-version-report.md`; `reports/metrics/first-version-runtime.json` | snapshot `94e25c633751ad37fbe0499dc1a684959a148358`; evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified for the cited implementation |
| C03 | Current implementation | “The Agent maintains structured active preferences and replaces superseded values instead of appending contradictions.” | `docs/contracts/architecture.md`; `solution/state.py`; `tests/core/test_state.py` | base `a81b042d3010fb254519ab56573d03beba111396` | Verified |
| C04 | Official rule and current implementation | “Every turn returns a customer message, a structured clarification field, and an ordered Top 10.” | `docs/agent_api_contract.json`; `demo/run_demo.py`; `tests/core/test_agent.py` | `2a6cc8e776da66ce69b1cbd237838fbc43f32587`; `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`; base `a81b042d3010fb254519ab56573d03beba111396` | Verified |
| C05 | Measured demo result | “In public Intent Override session `public_0183`, replacement arrives on turn 4 and the first eligible hit is turn 5 at rank 8.” | `demo/run_demo.py`; `docs/submission/first-demo-evidence.md` | `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`; `5bd84367c0103163eda681b5dc64727b147e9210`; merged PR #5 `a81b042d3010fb254519ab56573d03beba111396` | Verified |
| C06 | Measured result | “On the 200-session public evaluator, HitRate@10 is 0.91, MRR is 0.624024, MTTC is 4.255, Efficiency is 0.6745, and the recommended TechnicalScore is 0.777107.” | `reports/metrics/first-version-runtime.json` | measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified reference result |
| C07 | Measured result | “Public scenario HitRate@10 is 0.925 Buying, 0.95 Browsing, 0.766667 Intent Override, and 0.9 Boundary.” | `reports/metrics/first-version-runtime.json` | measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified reference result |
| C08 | Measured result | “The committed reference run reports 0 prompt tokens, 0 completion tokens, no scoring-time network requirement, and estimated API cost USD 0.” | `reports/metrics/first-version-runtime.json`; `docs/submission/first-version-report.md` | `9c59d4874db29dee1d9d839c8339ad870f2a3e46`; snapshot `94e25c633751ad37fbe0499dc1a684959a148358` | Verified reference result |
| C09 | Measured result | “On the committed Windows/Python 3.13 reference run, 833 responses averaged 37.736 ms with p95 76.583 ms, and initialization took 2.933 seconds.” | `reports/metrics/first-version-runtime.json` | measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified and machine-specific |
| C10 | Measured result | “A 200-target deterministic shadow evaluation with zero public-target overlap reached HitRate@10 0.895 and TechnicalScore 0.780546.” | `reports/metrics/first-version-shadow.json` | measured code `4ea2cff794318baa5e05ab77e089f2997edbc3cc`; evidence commit `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad` | Verified robustness result, not an official score |
| C11 | Current limitation | “Lexical retrieval can miss semantic matches, index construction has startup cost, personalization is limited, and public and shadow results do not guarantee private-set performance.” | `docs/submission/first-version-report.md`; `reports/analysis/TASK-201-failure-taxonomy.md` | `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad`; `cac52211e4d0eea13c27512689a4e59d13acc86b` | Verified limitations |
| C12 | Pending result | “Final-submit metrics and latency at the eventual video commit are unchanged.” | No immutable result exists for the future recording commit. | None | Pending, do not claim |
| C13 | Pending result | “Performance on the organizer's 800 private sessions is known.” | Private results are unavailable. | None | Pending, do not claim |
| C14 | Pending capability | “Recommendations include product-specific explanations.” | The accepted report lists this as unfinished. | snapshot `94e25c633751ad37fbe0499dc1a684959a148358` | Pending, do not claim |
| C15 | Official rule | “TechnicalScore is the recommended objective composite used as an input to Technical Execution; it is not the competition's final overall score.” | `docs/competition_specification.md`, section `Metrics` | `34078351e1c3615e5505a2e829600b56a542e462` | Verified |

## Current capability status

| Capability | Evidence at base `a81b042d...` | Status | Claim boundary |
|---|---|---|---|
| Structured state and override replacement | `solution/state.py`; state tests | Implemented | May be demonstrated through `public_0183`. |
| State-derived lexical retrieval query | `SessionState.retrieval_query` | Implemented | Do not call it model-based query rewriting. |
| SQLite FTS5/BM25 retrieval | `_BaselineBM25Index` in `solution/agent_impl.py` | Implemented | One lexical retrieval path only. |
| Constraint-aware reranking | `solution/ranker.py` | Implemented | Lexical overlap, exact match, budget distance, and retrieval rank. |
| Deterministic non-repeating clarification | `solution/question_policy.py`; state tests | Implemented | Fixed attribute priority with state-aware skipping. |
| Dynamic or adaptive clarification | No uncertainty or question-value score is present. | Partial | State-aware skipping exists; learned or value-based selection does not. |
| Buying-versus-Browsing routing | One `respond` pipeline is used for all sessions. | Not implemented | Do not show a route node. |
| Dual-route or multi-route retrieval | One `_BaselineBM25Index.search` path is present at the required base. PR #8 has an unmerged experiment at head `23814dbb2bba9de9f338b26aeffbf23ceb0efb82`, so it is not part of the current submission implementation. | Not implemented at base; open work exists | Do not claim dual-route retrieval unless it is merged and the final submission commit is re-audited. |
| Dense retrieval | No embedding or dense index exists under `solution/`. | Not implemented | Do not claim dense retrieval. |
| Hybrid retrieval | No lexical-plus-dense fusion exists. | Not implemented | Do not claim hybrid retrieval. |
| Semantic reranking | The ranker has no embedding or semantic model. | Not implemented | Call the current step lexical constraint-aware reranking. |
| Aggregate-profile personalization | The profile is copied into state but is not consumed by retrieval or ranking. | Partial: storage only | Describe personalization as limited. |

## Team roles and contribution evidence

The voice-over names all four members and describes the current,
submission-relevant responsibilities confirmed by the team. The founding
baseline is supported by accepted mainline commits and the repository's
first-version report; later teammate deliverables require merged-PR evidence.
PR numbers and SHAs remain here and are not read aloud. A task assignment or
open PR is not completed-contribution evidence. Remote status below was checked
on 2026-08-30; `origin/main` remained at
`a81b042d3010fb254519ab56573d03beba111396`.

| Team member | Current submission-relevant responsibility | Completed contribution supported by a merged PR | Open-work boundary | Status for narration |
|---|---|---|---|---|
| Fang Tianchen | Team lead; initial end-to-end Agent, demo baseline, and integration. | Core Agent `6a3937445c1f2cf011d28f346ac33dbb9c7c0753`; first repeatable demo `0f58b337ac03356c094c0fe3643bc3eb4b67b3a8`; score/runtime gate `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; frozen HR@10 `0.91` evidence `9c59d4874db29dee1d9d839c8339ad870f2a3e46`; accepted baseline report `94e25c633751ad37fbe0499dc1a684959a148358`. The report explicitly attributes the baseline architecture, state/override logic, lexical retrieval bridge, reranking, clarification policy, integration, gates, and first reproducible demo to the team lead and dedicated Core Agent. | Later integration-lane gate hardening is merged in PR #1 at `4e4a240a0a6060eaa0b16864fd447785b90b141d`. | May narrate the accepted initial Agent/demo baseline and public HR@10 `0.91`; do not call `0.91` TechnicalScore. |
| Wang Siwen | Backend and candidate-retrieval engineering. | None at the TASK-203 base. | Dual-route retrieval experiment: PR #8, head `23814dbb2bba9de9f338b26aeffbf23ceb0efb82`, open and unmerged at the status check. | Name the role, but do not narrate the PR #8 implementation as completed. |
| Liu Chunyi | Testing, QA, and demo-production support. | File-level whitespace-gate QA coverage: PR #2, merge `ccd58846a286ae1f102c28388ffe8364787df764`. | Cross-platform release checks: PR #6, head `09aaa1cbba3e1cd4bae6222064304da0d54035af`, open and unmerged at the status check. | Name the role and merged QA contribution; do not count PR #6 yet. |
| Cheng Xianyun | Testing, evidence analysis, and demo production. | Public failure taxonomy: PR #4, merge `184ef33a9cf686b5ef55bc60d6d0b223d762d666`; truthful Intent Override demo: PR #5, merge `a81b042d3010fb254519ab56573d03beba111396`. | TASK-203 PR #7 is open and is not counted as completed contribution. | Name the role and the PR #4/#5 merged contribution. |

## Claim update rule

Before recording, rerun the demo, full evaluator, tests, and runtime benchmark
at the final commit. Use the test count produced by that commit. If a value
changes, revise the storyboard, subtitles, compact cards, and this ledger
together. Do not infer private performance from public or shadow results.
