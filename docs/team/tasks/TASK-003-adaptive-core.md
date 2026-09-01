# TASK-003: executable adaptive core

Owner: team-lead integration Agent. Reviewer: Liu Chunyi.
Base: `5bd5d6fac91aad718862baded99eaf8b21cdd2bf`.
User direction: implement missing core behavior; pause submission material work.

## Allowed paths

- `solution/**` EXCEPT `solution/retrieval/**`
- `tests/core/**`
- `docs/decisions/ADR-0010-adaptive-core.md`
- `docs/decisions/ADR-0011-optional-semantic-rerank.md`
- `docs/team/tasks/TASK-003-adaptive-core.md`

No edits to existing shared contracts, starter signature, evaluator, data,
retrieval-owned code, other tests, dependencies, CI, or submission documents.
New core-private components consume the existing rich retrieval contract.

## Acceptance and promotion

- Preserve runnable baseline and its existing tests without weakened assertions.
- Opt-in adaptive mode must execute through the official adapter/harness.
- Route and workflow decisions must change execution, not just trace labels.
- Candidate evidence must drive clarification under overload, with a bounded
  pool and deterministic fallback for sparse evidence.
- Explicit preferences and no-preference dominate aggregate profile priors;
  distilled memory updates on correction without leaking across sessions.
- Never infer identity or persist cross-session history from anonymous profiles.
- The default and fallback paths work offline. Optional API ranking requires
  explicit network opt-in, selected model, credentials, and a request cap.
- Do not represent lexical ranking as learned semantic/LLM reranking.
- Promotion requires overall AND scenario non-regression on public and shadow
  HR/MRR/MTTC, plus independent review. Team gate alone is insufficient.
- Run public once per declared implementation; shadow is an aggregate final
  robustness check, not a target-level tuning source. Record negative results.

## Proof commands

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python -m tests.core.check_adaptive --output reports/generated/task003
```

`check_adaptive` runs baseline and adaptive modes against unchanged official
evaluation functions in separate processes, writes UTF-8/LF JSON and source
checksums, and reports a promotion verdict without changing configuration.

## Remaining separate lane

Real dense retrieval belongs to Wang. API reranking plumbing is tested with
mocked transport, but live model quality/cost validation awaits explicit
approval. Do not claim a successful real-model experiment from mocks.
Existing DualRoute remains opt-in.

## First measured decision

Offline core run `reports/generated/task003-run2` (source checksums in manifest):

| Split | Mode | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | ---: | ---: | ---: | ---: |
| Public | baseline | 0.910 | 0.624024 | 4.255 | 0.777107 |
| Public | adaptive | 0.925 | 0.637887 | 4.555 | 0.782766 |
| Shadow | baseline | 0.895 | 0.630488 | 3.805 | 0.780546 |
| Shadow | adaptive | 0.900 | 0.608901 | 4.280 | 0.767070 |

Decision: retain baseline. The alternate core is implemented but NOT approved
for default promotion. In particular, asking high-split conventional attributes
does not establish higher conversational information value; the observed
Browsing/Buying time and ranking regressions remain unresolved. No retuning
from shadow labels was performed. No model API was called.

Run1 stopped on a wrapper field-name error after baseline-public only; it is
not a complete experiment. Run2 completed all four groups. Final code adds
the independently disabled API boundary, with no offline-policy retuning.

## Local operation and review

PowerShell (offline candidate):

```powershell
$env:INTENTCOMPASS_AGENT_MODE = "adaptive"
$env:INTENTCOMPASS_RETRIEVAL = "baseline"
$env:INTENTCOMPASS_SEMANTIC = "off"
$env:INTENTCOMPASS_LLM_ALLOW_NETWORK = "0"
python -m evaluator.local_evaluator --output reports/generated/adaptive-public.json
```

macOS/Linux (offline candidate):

```sh
INTENTCOMPASS_AGENT_MODE=adaptive INTENTCOMPASS_RETRIEVAL=baseline INTENTCOMPASS_SEMANTIC=off INTENTCOMPASS_LLM_ALLOW_NETWORK=0 python -m evaluator.local_evaluator --output reports/generated/adaptive-public.json
```

Create `reports/generated` first if absent. `check_adaptive` does this itself.
Use `INTENTCOMPASS_AGENT_MODE=baseline` and `INTENTCOMPASS_RETRIEVAL=baseline`
for the existing demo and full gate. Existing demo expectations intentionally
describe the frozen baseline, not the opt-in candidate. Independent review
must not weaken those assertions to promote this candidate.
