# V2 headless demonstration shot list

> **Superseded TASK-203 shot list.** Do not record the final video from this file.

Status: capture plan only. Every capture remains `Pending` until it is recorded
from the final clean commit and checked against the claim ledger.

| Shot | Planned time | Capture action | Required visible evidence | Editing boundary | Status |
|---|---:|---|---|---|---|
| S01 | 0:00-0:15 | Create a simple title and 10-turn scoring timeline. | The terms `exact parent_asin`, `Top 10`, and `earlier is better`. | Explanatory opening only. It does not prove runtime behavior. | Pending |
| S02 | 0:15-0:35 | Draw only the current implementation path verified in `solution/`: `reset`, `SessionState`, state update and replacement, lexical query, SQLite FTS5/BM25 retrieval, lexical constraint rerank, deterministic clarification, and Top 10 response. | Every node maps to current code. | Label it `Current implementation`. Do not add routing, dual-route, dense, hybrid, semantic-reranking, or learned-clarification nodes. | Pending |
| S03 | 0:35-0:45 | Start one terminal recording at repository root. Run `git rev-parse HEAD`, `git status --short`, and `python demo/run_demo.py`. | Final commit SHA, empty status output, typed launch command, process output beginning. | No pasted transcript or pre-rendered command output. | Pending |
| S04 | 0:45-1:10 | Continue the same recording through turns 1-3. Use a crop or highlight to keep each field readable. | Customer message, `Active state`, search query, `Ask attribute`, Agent message, ordered Top 10, and the pre-override scoring label. | Cropping and zoom are allowed. Field values must remain from the recorded process. | Pending |
| S05 | 1:10-1:25 | Continue to turn 4 and highlight the state replacement. | Replacement customer message, active material `polyester`, stale feature and duplicate material values absent, and target not in Top 10. | Do not reconstruct the before/after state in a separate fake terminal. | Pending |
| S06 | 1:25-1:45 | Continue to turn 5 and the final result line. | Added constraints, all ten identifiers, target rank 8, first hit turn 5. | Keep the full result line visible long enough to read. | Pending |
| S07 | 1:45-2:15 | In a new terminal segment at the same final SHA, run `python scripts/team_gate.py --full-eval`. | Typed command, the final test count and pass summary produced by that commit, evaluator JSON, `TEAM GATE PASSED`, and exit success. | Silent compute time may be accelerated or cut. Add `waiting time shortened, one uninterrupted run` during the cut. State that TechnicalScore is not the final overall competition score. | Pending |
| S08 | 2:15-2:35 | Run `python scripts/benchmark_runtime.py` from the same clean commit. | Commit, dirty flag, environment, workload, latency distribution, tokens, and network requirement. | Show freshly generated output. The compact reference card must cite `reports/metrics/first-version-runtime.json`. | Pending |
| S09 | 2:35-2:45 | Build a limitation card from committed report and analysis text. | Lexical-match risk, startup cost, limited personalization, and unknown private-set performance. | A limitation card explains evidence. It must not imply a new test was run. | Pending |
| S10 | 2:45-3:00 | Build a team-role and contribution card from the verified ledger. | `Fang Tianchen — initial Agent and demo baseline, public HR@10 0.91`; `Wang Siwen — backend/retrieval`; `Liu Chunyi and Cheng Xianyun — testing/demo production`. | Distinguish the accepted founding baseline, current responsibilities, and later merged contributions. Keep PR numbers, SHAs, and open/merged status in `claim-evidence-ledger.md`. Do not present assigned or open-PR work as completed. | Pending |

## Recording continuity

S03-S06 should originate from one invocation of `demo/run_demo.py`. S07 and S08
may be separate terminal segments because they are different commands, but each
segment must show the same final commit and a clean tracked worktree. Record the
full raw takes before editing and retain them until the submitted video is
accepted.

## Capture rejection conditions

Reject and re-record a shot if the command is not visible, the commit differs
from the intended submission commit, the worktree is dirty without explanation,
the output was copied into a prepared terminal, an exit failure is hidden, a
metric differs from its subtitle, or a capability cannot be reproduced by the
shown command.
