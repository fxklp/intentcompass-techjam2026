# V2 requirement, evidence, and shot matrix

Status: local production plan. No video has been recorded or uploaded.

The V2 submission story covers only the automated Python Agent and the headless
evaluation path. A row is `Verified` only when the cited repository file and
commit already support the wording. `Pending` means that the recording or
final-commit evidence must still be produced and may not be described as done.

| ID | Official requirement or scope rule | Repository evidence and immutable anchor | Planned video shot | Status |
|---|---|---|---|---|
| R01 | Find a hidden target product as early and as highly ranked as possible in a multi-turn session. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`, sections `Objective` and `Session Protocol`. | S01 states the problem and the exact-match Top-10 objective. | Verified |
| R02 | Expose `Agent.reset(session_id, user_profile)` and `Agent.respond(session_id, user_message, turn, top_k)`. | `docs/agent_api_contract.json` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`, and the adapter in `starter/agent.py` at `21ccdee352786cbf4e08114b5e9e7a4402edbb40`. | S03 shows the real launch command. S04-S06 show the resulting turn records. | Verified |
| R03 | Return natural `message`, structured `ask_attribute`, and ordered recommendations. Only the first 10 valid unique `parent_asin` values are scored. | `docs/submission_rules.md`, `docs/agent_api_contract.json`, and `docs/evaluation_config.json` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`. | S04-S06 keep `Ask attribute`, `Agent message`, and `Top 10` legible in the terminal capture. | Verified |
| R04 | Handle Buying, Browsing, Intent Override, and Boundary sessions. An override cannot score before the replacement intent arrives. | `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`, and truthful gating in `demo/run_demo.py` at `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`. | S04-S06 follow `public_0183` through pre-override turns, replacement, and the eligible hit. | Verified |
| R05 | Formal evaluation uses the automated backend contract and headless pipeline. | Scope and protocol in `docs/competition_specification.md` at `34078351e1c3615e5505a2e829600b56a542e462`, and the scoring entry point in `evaluator/local_evaluator.py` at the TASK-203 base `a81b042d3010fb254519ab56573d03beba111396`. | S03-S08 use terminal commands and generated output from the real repository. | Verified |
| R06 | Provide one reproducible command and remain usable without credentials or network access during scoring. | `docs/submission_rules.md` at `2a6cc8e776da66ce69b1cbd237838fbc43f32587`, `demo/README.md` at `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`, and `docs/submission/first-demo-evidence.md` at `5bd84367c0103163eda681b5dc64727b147e9210`. | S03 launches `python demo/run_demo.py`. S07 launches `python scripts/team_gate.py --full-eval`. | Verified |
| R07 | Report HitRate@10, MRR, MTTC, Efficiency, and the recommended TechnicalScore from the unchanged evaluator. | `reports/metrics/first-version-runtime.json`, measured code commit `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, committed by `9c59d4874db29dee1d9d839c8339ad870f2a3e46`. | S07 records a real full-evaluator run and presents the accepted reference values with their evidence path. | Verified evidence, capture Pending |
| R08 | Disclose latency, token use, model choice, network need, and estimated cost. | `reports/metrics/first-version-runtime.json` at `9c59d4874db29dee1d9d839c8339ad870f2a3e46`, and disclosure text in `docs/submission/first-version-report.md` at `94e25c633751ad37fbe0499dc1a684959a148358`. | S08 records `python scripts/benchmark_runtime.py`. The narration labels latency as reference-machine evidence. | Verified evidence, capture Pending |
| R09 | Explain the architecture and the replaceable active-intent state. | `docs/contracts/architecture.md` at `8e88d75cbd8f3a1a6c3f6fcfebdd3bc22b9d85bb`, and the state implementation in `solution/state.py` at `6a3937445c1f2cf011d28f346ac33dbb9c7c0753`. | S02 uses an explanatory architecture diagram. S04-S06 prove the state transition in a real run. | Diagram Pending, behavior Verified |
| R10 | Disclose limitations without implying private-set guarantees. | `docs/submission/first-version-report.md` and `docs/submission/P0_P1_ACCEPTANCE_AUDIT.md` at `94e25c633751ad37fbe0499dc1a684959a148358`. | S09 states lexical-retrieval, startup, personalization, and private-set limits. | Verified |
| R11 | Describe team contributions using merged pull requests only. | Merge commits: PR #1 `4e4a240a0a6060eaa0b16864fd447785b90b141d`, PR #2 `ccd58846a286ae1f102c28388ffe8364787df764`, PR #4 `184ef33a9cf686b5ef55bc60d6d0b223d762d666`, PR #5 `a81b042d3010fb254519ab56573d03beba111396`. | S10 shows only these merged records. No planned or unmerged work is credited. | Verified through base commit |
| R12 | Do not present mock output, prepared screens, or unsupported claims as executed behavior. | Evidence policy in `docs/contracts/architecture.md` at `8e88d75cbd8f3a1a6c3f6fcfebdd3bc22b9d85bb`, and task controls in `docs/team/tasks/TASK-203-v2-storyboard.md`. | S03-S08 begin with visible commands and use output from the same recorded run. Explanatory cards are labeled as such. | Recording Pending |

## Coverage decision

All official deliverable topics needed for the three-minute story have a source,
repository anchor, and planned shot. The remaining work is production work:
recording the final clean commit, generating the architecture graphic from the
frozen contract, timing the narration, exporting subtitles, and verifying the
final media. None of those items is claimed as complete in this task.
