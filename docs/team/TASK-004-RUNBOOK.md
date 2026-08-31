# TASK-004 local integration runbook

Status: implementation and experiments in progress; not a submission approval.
Main stays at its reviewed baseline. Wang receives no work. No PR self-approval.

## Fixed boundaries

Official source re-read on 2026-08-31:
https://bytedance.larkoffice.com/wiki/GdYFwzWNLiREsSkuIjZcDznInWc

The interface, catalog, public data, evaluator, metric formula and stopping
policy remain unchanged. Public is a labeled development set; Shadow is a
local synthetic robustness set, NOT the organizer's 800-session private set.
No target-specific rule, hidden-label access, training, UI, multimodal input,
external vector database, purchase transaction or upstream data reconstruction.

## Setup (optional semantics)

Python 3.12+ recommended; this machine runs 3.13.9. The baseline uses stdlib.
Create a project-local virtual environment and install `requirements-semantic.txt`.
Activate it using the usual command for your shell, then:

```text
python scripts/build_semantic_index.py --download
```

The explicit setup downloads two pinned approximately 23 MB ONNX models,
tokenizers and their model cards (Apache-2.0 license declaration). No separate
LICENSE file exists in those model repositories. The script creates the
catalog-derived 384-dimensional float32 cache under ignored `artifacts/semantic`.
It preserves the source catalog and writes file/model/catalog checksums.
Nothing downloads at Agent runtime. Missing dependencies/assets use lexical
fallback, and must not be reported as successful dense-model execution.

This machine completed the 50,000-product build in 1783.905 seconds (about
29.7 minutes, partly sharing CPU with the cross-encoder experiment). Raw
vectors occupy 76,800,000 bytes; the NPY file is 76,800,128 bytes. Vector file
SHA256: `93b97407d50e87c670445008fc367eced7c5fc9d0ff0f85b77d085fe2a6f7420`.
This is one-time setup cost, not per-session inference latency.

The models are pretrained encoders. They provide true vector retrieval and
cross-encoder ranking, but are NOT a generative LLM. Qwen/DeepSeek are separate
optional LLM-ranking routes. Do not conflate their evidence.

## Reproducible offline experiments

These commands isolate each model configuration in a separate process:

```text
python -m tests.core.check_final --mode baseline --output reports/generated/baseline-public.json
python -m tests.core.check_final --mode integrated --output reports/generated/integrated-public.json
python -m tests.core.check_final --mode integrated --retrieval hybrid --output reports/generated/hybrid-public.json
python -m tests.core.check_final --mode integrated --semantic local --output reports/generated/local-ranker-public.json
```

Output names must be new. The runner rejects source/data changes during a run.
Only frozen public non-regressing finalists get `--split shadow`. Final latency
comparisons run sequentially without model building or another CPU workload.
First-run construction cost is reported separately from per-turn latency.

## Shared API budget

Real API calls are blocked until credentials and (for Qwen) Beijing region are
confirmed. Never paste a key in chat or commit it. Environment variable names:
`DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `INTENTCOMPASS_QWEN_REGION=beijing`.
This implementation deliberately does not guess international pricing.

Initialize ONE ledger once for the whole experiment stage:

```text
python scripts/model_probe.py --ledger artifacts/api-budget/task004.sqlite3 --initialize-budget
```

It refuses to overwrite an existing ledger. All subsequent models must use
that same path. Moving/deleting/reinitializing the ledger does not restore the
user's budget authorization. The initialized ceiling is RMB100 in total.
Unknown charges retain their reservation. No automatic top-up or retries.
An eight-second parent deadline terminates a stuck request subprocess.

Readiness/budget status (no model request):

```text
python scripts/model_probe.py --ledger artifacts/api-budget/task004.sqlite3 --model qwen3.8-flash
python scripts/model_probe.py --ledger artifacts/api-budget/task004.sqlite3 --model deepseek-v4-flash
```

After account free credits are checked, a small live screen is explicit:

```text
python scripts/model_probe.py --ledger artifacts/api-budget/task004.sqlite3 --model qwen3.8-flash --live --per-scenario 3 --output reports/generated/qwen-free-screen.json
```

The screen uses the first three public sessions in each scenario, selected
before model calls. It aborts on a provider failure. A fallback-only screen is
not a successful model test. Estimated peak uncached cost is conservative;
provider invoices and credit deductions determine actual paid cost.

## Official review checklist (do not replace with a score threshold)

| Official item | Acceptance evidence / known boundary |
| --- | --- |
| 4.2 I Buying/Browsing | Runtime route changes candidate retrieval; lexical-only fallback clearly labeled |
| 4.2 I Multi-route -> LLM ranking | Keyword/category/vector implementation plus separately tested Qwen/DeepSeek API route; real API validation still required |
| 4.2 II Accumulation/override | Structured current slots, replacement tests, no obsolete constraints in context |
| 4.2 II Over-generality | Bounded pool, explicit clarification, expensive-stage cutoff; never claim entropy alone proves useful questions |
| 4.2 III Context distillation | Safe aggregate profile only, current short-term state; no identity inference or cross-user persistence |
| 4.2 III Runtime adaptation | Executed control flow and failure/cutoff traces, not only labels |
| 4.2 IV Metrics | Official HR/MRR/MTTC and scenario breakdown; no manual score substitution |
| 4.3 Scope | Text only, in-memory inference, no training/UI/heavy vector service |
| 4.3 Limits | 10-turn evaluator, valid frozen ASINs, immutable catalog |
| 4.4 Models | Offline operation mandatory here; disclose optional network and costs |
| 4.5 Submission | Public repo, setup/repro, report and YouTube video still require actual completion; software checks do not establish these |

Official rubric: Technical Execution 35%, Innovation & Problem Insight 20%,
Impact & Relevance 20%, Feasibility & Practicality 15%, Presentation &
Communication 10% (FINAL EVENT ONLY). TechnicalScore is only an input to
Technical Execution, not the total contest score. Final-event communication
is unassessed, not automatically awarded. No official passing score is given.

## Experiment ledger

- Baseline reproduced: 81 tests, full gate; Public HR .910, MRR .624024,
  MTTC 4.255, TechnicalScore .777107.
- C1 conservative integration, lexical/offline: exact same overall AND scenario
  metrics on Public. Evidence: `task004-c1-public.json`, SHA256
  `b6417f74bc5b5976c9a3ad858941569248a0218d564c61bcf2df8ba764b9f859`.
  This run overlaps CPU index building, so its latency is NOT a speed verdict.
- C3 cross-encoder quality test can execute before C2 dense recall completes
  its initial index build; neither decision uses Shadow labels.
- C3 completed: Public HR .910, MRR .623373, MTTC 4.170, TechnicalScore
  .778612. Reject despite the aggregate score increase: Browsing HR/MRR and
  Buying MRR regress. File `task004-c3-public.json`, SHA256
  `5662642cb1fd4b1b76891c1dd324e92ac10cab1a3e174431296213c8ccd33cda`.
  Evaluation took 644.94 seconds overlapping index building; precise isolated
  latency comparison was not performed because it already fails quality gates.
  It completed naturally before a contemplated resource-screen termination.
  Do not report it as aborted or as a successful promotion. Shadow not run.
- API spend at initialization: zero; no Qwen/DeepSeek key present in this
  process. Budget and provider-failure tests use mocked transport, not live APIs.
- Current test run: 105/105 including actual optional model smoke tests passed
  in the semantic virtual environment. Public C1 needs final recheck after the
  small turn-boundary, plain numeric-budget and safe profile-export additions.
- C2 true hybrid retrieval completed with dense assets ready: Public HR .910,
  MRR .619347, MTTC 4.210, TechnicalScore .776604. Reject: overall, Boundary,
  Browsing and Buying MRR regress; Browsing MTTC also increases. No Shadow
  evaluation or further tuning of this variant. Evidence `task004-c2-public.json`,
  SHA256 `8bcc754d22a7e8a3c78a84c43a0b7116e2a7bf2b319e7fa63bfe0434dbd2c6c0`.
  The immutable result's effective backend must say dense `ready`.

The release configuration remains lexical/offline; `integrated` is the
conservative final candidate. Hybrid and cross-encoder remain opt-in experiments,
not advertised as improvements. Existing `adaptive` behavior remains available
for reproducing TASK-003; it is not promoted. The legacy OpenAI adapter is not
used in this authorized Qwen/DeepSeek experiment stage.

Final freeze decision, judge simulation and simple Liu/Cheng reproduction
commands will be added only after the corresponding checks actually finish.
