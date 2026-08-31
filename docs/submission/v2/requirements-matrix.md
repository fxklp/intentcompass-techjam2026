# V2 requirement, policy, implementation, evidence, and shot matrix

Status: synchronized to accepted main
`5bd5d6fac91aad718862baded99eaf8b21cdd2bf` under TASK-204. No media has
been recorded or uploaded.

This matrix keeps four evidence classes separate:

- `Official requirement` comes from the competition specification, submission
  rules, API contract, or evaluation configuration.
- `Team policy` is an internal evidence or production rule, not an organizer
  requirement.
- `Formal Agent` means the code reached through `starter.agent.Agent` during
  official evaluation.
- `Isolated experiment` means merged repository code and evidence that the
  formal Agent does not import or execute.

## Official requirements

| ID | Requirement | Repository evidence and immutable anchor | Planned shot | Status |
|---|---|---|---|---|
| O01 | Find a hidden target product as early and as highly ranked as possible in a multi-turn session. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`, sections `Objective` and `Session Protocol`. | S01 states the exact-match Top-10 objective. | Covered |
| O02 | Expose `Agent.reset(session_id, user_profile)` and `Agent.respond(session_id, user_message, turn, top_k)`. | `docs/agent_api_contract.json` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`. | S03 launches the formal Agent through the headless harness. | Covered |
| O03 | Return natural `message`, structured `ask_attribute`, and ordered recommendations. Only the first 10 valid unique `parent_asin` values are scored. | `docs/submission_rules.md`, `docs/agent_api_contract.json`, and `docs/evaluation_config.json` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`. | S04-S06 keep the response fields and Top 10 legible. | Covered |
| O04 | Handle Buying, Browsing, Intent Override, and Boundary sessions. An override cannot score before the replacement intent arrives. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`. | S04-S06 follow `public_0183` through replacement and the eligible hit. | Covered |
| O05 | Formal scoring uses the automated Agent contract and headless evaluator pipeline. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`; `evaluator/local_evaluator.py` and formal Agent source at main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`. | S03-S08 use repository commands and generated output. | Covered |
| O06 | Provide reproducible setup and a scoring path that does not depend on undeclared services or credentials. | `docs/submission_rules.md` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`; cross-platform contract merged in PR #6 at `ce87a192964c6a10fcb9f2a3239bb48c7653789f`. | S03 launches the demo; S07 runs the full evaluator. | Covered |
| O07 | Report HitRate@10, MRR, MTTC, Efficiency, and the recommended TechnicalScore. TechnicalScore is an objective input to Technical Execution, not the competition's final overall score. | Formula at `34078351e1c3615e5505a2e829600b56a542e462`; frozen historical measurement at `9c59d4874db29dee1d9d839c8339ad870f2a3e46`; TASK-204 reproduction at main `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`. | S07 shows 49 passing tests and the reproduced evaluator result. | Evidence covered, capture Pending |
| O08 | Disclose architecture, model choice, latency, token use, estimated cost, limitations, and team contributions. | Final-deliverable policy at `34078351e1c3615e5505a2e829600b56a542e462`; formal baseline disclosure at `94e25c633751ad37fbe0499dc1a684959a148358`; merged experiment decision at `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`. | S02 and S08-S10 cover these topics within their evidence boundaries. | Evidence covered, production Pending |

## Team policies

| ID | Policy | Repository evidence and immutable anchor | Planned shot | Status |
|---|---|---|---|---|
| P01 | Do not present mock output, retyped terminal text, prepared screens, or unsupported claims as executed behavior. | Evidence boundary in `docs/contracts/architecture.md` at `8e88d75cbd8f3a1a6c3f6fcfebdd3bc22b9d85bb`; TASK-204 task card. | S03-S07 show commands and output from real runs. | Recording Pending |
| P02 | Credit completed work from accepted mainline evidence and merged PRs; keep PR/SHA detail in the ledger rather than the narration. | `docs/team/OWNERSHIP.md`; PR #6-#9 merge evidence in `claim-evidence-ledger.md`. | S10 names contributors and real responsibilities without reading SHAs aloud. | Updated through PR #9 |
| P03 | Record capability footage from one identified clean final commit and disclose shortened waiting time. | TASK-204 task card and `shot-list.md`. | S03 and S07 show the final commit and clean status; edited waits are labeled. | Production Pending |
| P04 | Preserve historical performance values with their original code commit, environment, and method; do not relabel them as measurements of latest main. | `reports/metrics/first-version-runtime.json` and `reports/metrics/first-version-shadow.json`. | S08 labels the latency card as the historical Windows/Python 3.13.9 reference run. | Covered |

## Formal Agent implementation and gaps

| ID | Capability at main `5bd5d6f...` | Repository evidence | Planned shot | Status |
|---|---|---|---|---|
| I01 | Thin official adapter delegates to `solution.agent_impl.Agent`. | `starter/agent.py`; `solution/agent_impl.py` | S02-S03 | Implemented |
| I02 | Structured session state replaces superseded preferences and clears no-preference slots. | `solution/state.py`; state tests | S04-S06 | Implemented |
| I03 | Retrieval query is rebuilt from the current category and active preference values. | `SessionState.retrieval_query` in `solution/state.py` | S04-S06 | Implemented |
| I04 | Formal candidate retrieval uses one in-memory SQLite FTS5/BM25 lexical index with deterministic popularity fallback. | `_BaselineBM25Index` instantiated directly in `solution/agent_impl.py` | S02 | Implemented |
| I05 | Formal reranking uses lexical preference overlap, exact value matches, budget distance, and retrieval rank. | `solution/ranker.py` | S02 | Implemented |
| I06 | Clarification uses fixed attribute priority with state-aware skipping of asked, unconstrained, or populated attributes. | `solution/question_policy.py`; state tests | S04-S06 | Implemented deterministic policy |
| I07 | Learned uncertainty or question-value based clarification. | No uncertainty or question-value score exists in `solution/question_policy.py`. | S09 limitation | Partial: state-aware skipping only |
| I08 | Buying-versus-Browsing routing in the formal Agent. | `solution/agent_impl.py` uses one response pipeline and does not import `solution.retrieval`. | Not drawn in S02 | Not enabled |
| I09 | Dual-route or multi-route retrieval in the formal Agent. | `starter/agent.py` delegates to `_BaselineBM25Index`; the isolated retrieval package is not imported by the formal path. | Not drawn in S02 | Not enabled |
| I10 | Dense retrieval. | The formal path has no embeddings or dense index; the experiment manifest also declares `dense_retrieval.implemented=false`. | S09 limitation | Not implemented |
| I11 | Hybrid lexical-plus-dense retrieval. | Neither the formal path nor the merged experiment contains dense fusion. | Not shown as a capability | Not implemented |
| I12 | Semantic reranking. | `solution/ranker.py` uses lexical and numeric features, not an embedding or semantic model. | Not shown as a capability | Not implemented |
| I13 | Deep aggregate-profile personalization. | `SessionState` safely copies the profile, but formal retrieval and ranking do not consume it. | S09 limitation | Partial: storage only |
| I14 | Offline formal path with zero reported model tokens and no scoring-time network requirement. | Frozen measurement `reports/metrics/first-version-runtime.json` at `9c59d4874db29dee1d9d839c8339ad870f2a3e46`; reproduced gate at main `5bd5d6f...`. | S08 | Implemented; historical feasibility measured |

## Merged isolated retrieval experiment

| ID | Repository experiment state | Evidence | Video boundary | Status |
|---|---|---|---|---|
| E01 | Buying/Browsing field-specific lexical routes and deterministic fusion are implemented in an isolated experiment. | `solution/retrieval/**`, `experiments/retrieval/**`; code commit `0be74958a9833e1c6e2e0bd5a8db9abdc9c6ebcd`; PR #8 merge `970f0b754bba06f93b889e1b87f4ee9174e43ecb`. | May be described as an experiment decision, never drawn as a formal runtime node. | Implemented and merged, isolated |
| E02 | The candidate preserved Public HR@10 0.91 but reduced Public MRR and increased retrieval latency; its TechnicalScore change was marginal. | `reports/experiments/TASK-303-summary.md`; frozen JSON hashes in the manifest. | S09 explains why it is not enabled; do not attribute its numbers to the formal Agent. | Measured experiment, not deployed |
| E03 | The initial unconstrained fusion variant was rejected after Public and Shadow HR regression. | `reports/experiments/TASK-303-summary.md`, `Decision`. | May support truthful negative-result contribution wording. | Rejected experiment recorded |
| E04 | PR #9 repaired evidence portability without changing the candidate algorithm or frozen metrics. | Reviewed head `ae5589ef66024dbe562de456783f1d159e8ec64f`; PR #9 merge `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`; TASK-303 manifest. | Evidence provenance only. | Merged and verified |

## Coverage decision

The three-minute formal architecture may claim I01-I06 and the offline boundary
in I14. I07 and I13 remain partial. I08-I12 stay outside the formal runtime
diagram. E01-E04 prove that a dual-route lexical experiment exists in the
repository, but they do not change the submitted Agent call chain. All capture,
graphics, audio, subtitle timing, and final media remain `Pending`.
