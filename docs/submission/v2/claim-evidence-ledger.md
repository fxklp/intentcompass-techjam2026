# V2 claim and evidence ledger

Status: synchronized to accepted main
`5bd5d6fac91aad718862baded99eaf8b21cdd2bf` under TASK-204. `Verified`
claims may be used only within the boundaries below. `Partial`, `Isolated`, and
`Pending` claims must not be narrated as completed formal-Agent capability.

Source classes are `Official rule`, `Formal Agent`, `Current reproduction`,
`Historical measurement`, `Isolated experiment`, and `Team policy`.

## Official, formal-Agent, and measured claims

| Claim | Source class | Safe wording | Evidence | Commit anchor | Status |
|---|---|---|---|---|---|
| C01 | Official rule | “The challenge scores exact catalog `parent_asin` matches in the first 10 valid unique recommendations over at most 10 turns.” | `docs/competition_specification.md`; `docs/evaluation_config.json` | `34078351e1c3615e5505a2e829600b56a542e462`; `2a6cc8e776da66ce69b1cbd237838fbc43f32587` | Verified |
| C02 | Formal Agent | “The submitted path is a deterministic, CPU-only Python Agent whose scoring path requires no model API or runtime network.” | `starter/agent.py`; `solution/agent_impl.py`; historical feasibility evidence | Main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`; `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified; formal path only |
| C03 | Formal Agent | “The Agent maintains structured active preferences and replaces superseded values instead of appending contradictions.” | `solution/state.py`; state tests | Main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf` | Verified |
| C04 | Official rule and Formal Agent | “Every turn returns a customer message, a structured clarification field, and an ordered Top 10.” | `docs/agent_api_contract.json`; `demo/run_demo.py`; Agent tests | `2a6cc8e776da66ce69b1cbd237838fbc43f32587`; main `5bd5d6f...` | Verified |
| C05 | Current reproduction | “In `public_0183`, replacement arrives on turn 4 and the first eligible hit is turn 5 at rank 8.” | `demo/run_demo.py`; TASK-204 verification record | Original truthful-demo commit `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`; reproduced at main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf` | Verified on Windows/Python 3.12.13 |
| C06 | Historical measurement | “The frozen 200-session public run reports HitRate@10 0.91, MRR 0.624024, MTTC 4.255, Efficiency 0.6745, and TechnicalScore 0.777107.” | `reports/metrics/first-version-runtime.json` | Measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; evidence `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified historical reference |
| C07 | Historical measurement | “Public scenario HitRate@10 is 0.925 Buying, 0.95 Browsing, 0.766667 Intent Override, and 0.9 Boundary.” | `reports/metrics/first-version-runtime.json` | `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified historical reference |
| C08 | Historical measurement | “The frozen run reports zero model tokens, no scoring-time network requirement, and estimated API cost USD 0.” | `reports/metrics/first-version-runtime.json`; `docs/submission/first-version-report.md` | `9c59d4874db29dee1d9d839c8339ad870f2a3e46`; `94e25c633751ad37fbe0499dc1a684959a148358` | Verified historical reference |
| C09 | Historical measurement | “On the recorded Windows 11/Python 3.13.9 run, 833 responses averaged 37.736 ms with p95 76.583 ms and initialization took 2.933 seconds.” | `reports/metrics/first-version-runtime.json` | Measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; evidence `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified, machine-specific; not remeasured by TASK-204 |
| C10 | Historical measurement | “A deterministic 200-target shadow run with zero public-target overlap reached HitRate@10 0.895 and TechnicalScore 0.780546.” | `reports/metrics/first-version-shadow.json` | Measured code `4ea2cff794318baa5e05ab77e089f2997edbc3cc`; evidence `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad` | Verified robustness result; not official private score |
| C11 | Formal limitation | “The formal lexical retriever can miss semantic matches; personalization is limited; public and shadow results do not guarantee private-set performance.” | Formal source; `docs/submission/first-version-report.md`; failure taxonomy | Main `5bd5d6f...`; `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad`; `cac52211e4d0eea13c27512689a4e59d13acc86b` | Verified limitations |
| C12 | Pending result | “Final recording-commit metrics and latency are unchanged.” | The future recording commit does not yet exist. | None | Pending, do not claim |
| C13 | Pending result | “Performance on the organizer's 800 private sessions is known.” | Private results are unavailable. | None | Pending, do not claim |
| C14 | Pending capability | “Recommendations include product-specific explanations.” | Accepted report lists this as unfinished. | `94e25c633751ad37fbe0499dc1a684959a148358` | Pending, do not claim |
| C15 | Official rule | “TechnicalScore is an objective input to Technical Execution; it is not the competition's final overall score.” | `docs/competition_specification.md`, `Metrics` | `34078351e1c3615e5505a2e829600b56a542e462` | Verified |
| C16 | Current reproduction | “At accepted main, 49 tests pass and the full gate reproduces HR@10 0.91 and TechnicalScore 0.777107.” | `python scripts/team_gate.py --full-eval`; TASK-204 verification record | Main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf` | Verified on Windows/Python 3.12.13; not a replacement for the historical latency JSON |

## Isolated retrieval experiment claims

| Claim | Safe wording | Evidence and immutable anchor | Status and boundary |
|---|---|---|---|
| E01 | “A merged isolated experiment implements field-specific Buying/Browsing lexical routes and deterministic fusion.” | `solution/retrieval/**`; `experiments/retrieval/**`; code `0be74958a9833e1c6e2e0bd5a8db9abdc9c6ebcd`; PR #8 merge `970f0b754bba06f93b889e1b87f4ee9174e43ecb` | Verified repository experiment; not enabled in formal Agent |
| E02 | “The retained candidate preserved Public HR@10 0.91, changed Public TechnicalScore from 0.777107 to 0.777516, reduced Public MRR from 0.624024 to 0.619054, and increased retrieval latency.” | `reports/experiments/TASK-303-results.json`; `reports/experiments/TASK-303-benchmark.json`; `reports/experiments/TASK-303-summary.md`; hashes in manifest at main `5bd5d6f...` | Verified historical experiment result; never use as formal-Agent performance |
| E03 | “The initial unconstrained fusion was rejected after Public HR@10 fell to 0.89 and Shadow HR@10 fell to 0.87.” | `reports/experiments/TASK-303-summary.md`, `Decision`; PR #8 history | Verified negative result |
| E04 | “Dense retrieval was not implemented; the experiment uses lexical routes and must not be called dense, hybrid, or semantic retrieval.” | `artifacts/manifests/TASK-303-dual-route-inmemory.json`; TASK-303 task card | Verified boundary |
| E05 | “PR #9 made the evidence hashes and generators LF-stable without changing the algorithm or frozen metrics.” | Reviewed head `ae5589ef66024dbe562de456783f1d159e8ec64f`; TASK-304 tests and task card; PR #9 merge `5bd5d6fac91aad718862baded99eaf8b21cdd2bf` | Verified evidence repair |

## Formal Agent capability status at main `5bd5d6f...`

| Capability | Evidence | Status | Claim boundary |
|---|---|---|---|
| Structured state and override replacement | `solution/state.py`; state tests | Implemented | May be demonstrated through `public_0183`. |
| State-derived lexical retrieval query | `SessionState.retrieval_query` | Implemented | Do not call it model-based query rewriting. |
| SQLite FTS5/BM25 retrieval | `_BaselineBM25Index` in `solution/agent_impl.py` | Implemented | One formal retrieval path. |
| Constraint-aware reranking | `solution/ranker.py` | Implemented | Lexical overlap, exact match, budget distance, and retrieval rank. |
| Deterministic non-repeating clarification | `solution/question_policy.py`; state tests | Implemented | Fixed priority with state-aware skipping. |
| Dynamic or adaptive clarification | No uncertainty or question-value score | Partial | State-aware skipping exists; learned/value-based selection does not. |
| Buying/Browsing routing in formal Agent | One `respond` pipeline; no `solution.retrieval` import | Not enabled | Keep route node out of formal architecture. |
| Dual-route retrieval in formal Agent | `_BaselineBM25Index` is instantiated directly | Not enabled | Merged isolated code is not deployed behavior. |
| Dense or hybrid retrieval | No embedding model or dense index; manifest says false | Not implemented | Do not claim dense, hybrid, or semantic retrieval. |
| Semantic reranking | Formal ranker has no embedding or semantic model | Not implemented | Call it lexical constraint-aware reranking. |
| Aggregate-profile personalization | Profile copied but not consumed by formal retrieval/ranking | Partial: storage only | Describe personalization as limited. |

## PR #6-#9 merge ledger

| PR | Reviewed/head evidence | Merge commit | Material effect |
|---|---|---|---|
| #6 | `35927230574ddbf983f66aa6f54f897dec157d99` | `ce87a192964c6a10fcb9f2a3239bb48c7653789f` | Cross-platform LF/binary contract, PNG byte round-trip test, and three-system CI. |
| #7 | `89293876231e21ebeca9c112ccfd19ce00a3a939` | `ceea73f219c5082e968c2ab99e4c7465d2457690` | Reviewed V2 headless storyboard foundation. |
| #8 | `8003f8077d5357800a8d8738bde83087035c3fa0` | `970f0b754bba06f93b889e1b87f4ee9174e43ecb` | Isolated dual-route lexical experiment, negative result, and frozen evidence; no formal-Agent activation. |
| #9 | `ae5589ef66024dbe562de456783f1d159e8ec64f` | `5bd5d6fac91aad718862baded99eaf8b21cdd2bf` | Portable evidence-hash/generator repair; no algorithm or metric change. |

## Team roles and contribution evidence

The voice-over uses names and concise responsibilities. PR numbers, review
links, and SHAs remain here. Merging an isolated experiment does not make it a
formal-Agent capability.

| Team member | Verified contribution | Evidence | Narration boundary |
|---|---|---|---|
| Fang Tianchen | Initial end-to-end Agent, architecture, state/override logic, lexical retrieval bridge, ranking, clarification, gates, demo baseline, and integration. | Core `6a3937445c1f2cf011d28f346ac33dbb9c7c0753`; demo `0f58b337ac03356c094c0fe3643bc3eb4b67b3a8`; metric gate `424781522f52e9c1ef1c814ca8dc64eaf24cfead`; accepted report `94e25c633751ad37fbe0499dc1a684959a148358` | May credit initial formal Agent and integration; HR@10 0.91 is not TechnicalScore. |
| Liu Chunyi | Cross-platform release contract, exact Git-attribute/PNG regression evidence, three-system CI, and independent review of the PR #9 evidence fix. | PR #6 head/merge above; PR #9 independent Approve at `https://github.com/fxklp/intentcompass-techjam2026/pull/9#pullrequestreview-5060927627`, reviewed SHA `ae5589ef66024dbe562de456783f1d159e8ec64f` | Credit cross-platform QA and independent review. |
| Wang Siwen | Isolated dual-route lexical experiment, transparent rejected variant/trade-offs, reproducible evidence, and LF-portable evidence repair. | PR #8 and #9 rows above; TASK-303/TASK-304 reports and manifest | State clearly that the candidate is not enabled in the formal Agent and did not establish a deployed improvement. |
| Cheng Xianyun | Public failure analysis, truthful Intent Override demo, reviewed V2 storyboard, and latest-main evidence synchronization. | PR #4 merge `184ef33a9cf686b5ef55bc60d6d0b223d762d666`; PR #5 merge `a81b042d3010fb254519ab56573d03beba111396`; PR #7 merge `ceea73f219c5082e968c2ab99e4c7465d2457690`; TASK-204 branch | Credit analysis, demo, and submission materials. |

## Claim update rule

Before recording, rerun the demo, full evaluator, tests, and status checks at
the final recording commit. Use that commit's test count. If current metrics
change, revise storyboard, subtitles, and this ledger together. Keep the
historical latency and Shadow entries tied to their original commits and
environments. Never infer private performance from public, Shadow, or isolated
experiment results.
