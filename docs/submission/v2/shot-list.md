# V2 headless demonstration shot list

Status: TASK-204 capture plan only. Every capture remains `Pending` until it is
recorded from the final clean commit and checked against the evidence ledger.

| Shot | Planned time | Capture action | Required visible evidence | Editing boundary | Status |
|---|---:|---|---|---|---|
| S01 | 0:00-0:15 | Create a simple title and 10-turn scoring timeline. | `exact parent_asin`, `Top 10`, and `earlier is better`. | Explanatory opening only; it does not prove runtime behavior. | Pending |
| S02 | 0:15-0:35 | Draw only the formal path reached from `starter.agent.Agent`: `reset`, `SessionState`, state replacement, lexical query, SQLite FTS5/BM25 retrieval, lexical constraint rerank, deterministic clarification, and Top 10 response. | Every node maps to `starter/agent.py` or the formal core files under `solution/`. | Label it `Formal Agent at recording commit`. Do not add Buying/Browsing routing, dual-route fusion, dense, hybrid, semantic-reranking, or learned-clarification nodes. The merged experiment may be referenced only as an isolated decision in S09. | Pending |
| S03 | 0:35-0:45 | Start one terminal recording at repository root. Run `git rev-parse HEAD`, `git status --short`, and `python demo/run_demo.py`. | Final commit SHA, empty status output, typed command, and process output beginning. | No pasted transcript or prepared terminal output. | Pending |
| S04 | 0:45-1:10 | Continue the same recording through turns 1-3. Use a crop or highlight to keep each field readable. | Customer message, `Active state`, search query, `Ask attribute`, Agent message, ordered Top 10, and pre-override scoring label. | Cropping and zoom are allowed; values must remain from the recorded process. | Pending |
| S05 | 1:10-1:25 | Continue to turn 4 and highlight state replacement. | Replacement message, active material `polyester`, stale feature and duplicate material values absent, and target not in Top 10. | Do not reconstruct the state in a fake terminal. | Pending |
| S06 | 1:25-1:45 | Continue to turn 5 and the final result. | Added constraints, all ten identifiers, target rank 8, and first hit turn 5. | Keep the full result line visible long enough to read. | Pending |
| S07 | 1:45-2:15 | At the same final SHA, run `python scripts/team_gate.py --full-eval`. | Typed command, the test count produced by that commit, evaluator JSON, `TEAM GATE PASSED`, and successful exit. The TASK-204 baseline reproduced 49 tests, HR@10 0.91, and TechnicalScore 0.777107. | Silent compute time may be shortened only with `waiting time shortened, one uninterrupted run`. State that TechnicalScore is not the final overall score. | Pending |
| S08 | 2:15-2:35 | Display the committed historical runtime evidence with a real CLI command such as `python -m json.tool reports/metrics/first-version-runtime.json`. | Measurement commit `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, Windows/Python 3.13.9 environment, workload, latency, tokens, and network requirement. | Label values `Historical reference measurement`. Do not imply TASK-204 reran the benchmark or measured latest main. | Pending |
| S09 | 2:35-2:45 | Build an experiment-decision and limitation card from the committed TASK-303 summary and manifest. | Dual-route lexical experiment merged, formal Agent not enabled, Public HR unchanged, MRR/latency trade-off, dense retrieval absent, private set unknown. | This is repository evidence, not a formal capability shot. Do not add experiment nodes to S02 or claim candidate gains for the submitted Agent. | Pending |
| S10 | 2:45-3:00 | Build a contribution card from the verified ledger. | `Fang Tianchen — initial Agent/integration`; `Liu Chunyi — cross-platform QA/independent review`; `Wang Siwen — isolated retrieval experiment/negative evidence repair`; `Cheng Xianyun — analysis/truthful demo/V2 materials`. | Show names and responsibilities only. Keep PR numbers, review links, and SHAs in `claim-evidence-ledger.md`. | Pending |

## Recording continuity

S03-S06 must originate from one invocation of `demo/run_demo.py`. S07 may be a
separate terminal segment at the same final SHA. S08 displays frozen evidence
and is not a fresh benchmark. Record complete raw takes before editing and
retain them until the submission is accepted.

## Capture rejection conditions

Reject and re-record a capability shot if the command is hidden, the commit is
wrong, tracked files are dirty without explanation, output was copied into a
prepared terminal, an exit failure is concealed, a metric differs from its
subtitle, or an isolated experiment is presented as behavior of the formal
Agent.
