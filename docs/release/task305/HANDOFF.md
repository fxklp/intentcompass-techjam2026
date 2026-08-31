# TASK-305 handoff

## Disposition

**Still incomplete; do not accept or submit.**  The offline LLM semantic-ranking
goal is not met, and all four candidate metric groups exceed the task-card
tolerance.  The implemented capabilities and evidence are retained; neither a
feature-disabled RC3 result nor a failed model call is reported as completion.

Candidate code commit: `8161868d3db5f3570721c44bdd1049b7f616aff0` on
`core/TASK-305-capability-completion`.  The source directory was independently
extracted from the v2 handoff; the outer workspace and immutable RC3 archive
were not edited.

The outer handoff ZIP SHA256 is
`321f4992b8b89d024df94a215e23f828344a1c22627943dbe7354d44a5463c7c`;
every `HANDOFF-MANIFEST.json` entry verified with zero failures.  The nested
immutable RC3 ZIP SHA256 remains
`ccd8f4f54e99ee3eda0bfc4dcde6cb4862a54e746d4566b87632fcc260790d98`.

## Capability evidence

| Track 4.2 item | Runtime entry | Test/evidence | Candidate status |
| --- | --- | --- | --- |
| Buying/Browsing routes | `solution/workflow.py`, `solution/retrieval/hybrid.py` | route-weight/diversity test; run counters | enabled |
| Buying exact conditions | `solution/buying_constraints.py` | three-valued normal, negative, unknown, all-conflict tests | enabled |
| Dense and diversity | `solution/retrieval/dense.py`, `solution/retrieval/hybrid.py` | real ONNX/index smoke and fused-candidate test | enabled |
| Multi-route recall/fusion | `HybridRetriever.search` | keyword/category/dense counts in every final JSON | enabled |
| Model semantic ranking | `solution/local_reranker.py` | real cross-encoder output enters eight decisions | enabled, non-LLM |
| Team LLM ranking goal | `solution/local_llm_reranker.py` | strict parser/fail-closed tests and failed local probes | **incomplete** |
| State/override/reset | `solution/state.py` | inherited and new state suites | enabled |
| Pre-retrieval cutoff | `AdaptiveController.respond` | demo turn 1: pool 0, retrieval 0; turn 2 resumes | enabled |
| Profile/handoff/isolation | `solution/agent_impl.py`, `starter/agent.py` | export/import order and isolation test; demo session 2 | enabled |
| Dynamic workflow | `solution/workflow.py`, `solution/clarification.py` | rejection changes query/pool/question; demo turn 6 | enabled |
| Candidate validation | `scripts/task305_evaluate.py` | effective config, hashes, calls, fail-if-unused checks | enabled |

The final Public run records 796 real calls to each recall channel, 681 Buying
and 115 Browsing routes, 3,533 known conflicts, 18,302 satisfied and 21,415
unknown constraint outcomes, 465 profile consumptions, and eight real
cross-encoder ranking decisions.  The eight-turn target-blind demo is
`reports/generated/task305-demo-final.json`.

## Metrics

Values are RC3 -> candidate; deltas are candidate minus RC3.  All use the same
catalog hash, unchanged evaluator and deterministic materialized samples.

| Dataset | HR@10 | MRR | MTTC |
| --- | --- | --- | --- |
| Public | .980000 -> .915000 (-.065000) | .696861 -> .617552 (-.079309) | 3.755000 -> 4.065000 (+.310000) |
| Shadow | .965000 -> .895000 (-.070000) | .703615 -> .632724 (-.070891) | 3.545000 -> 3.785000 (+.240000) |
| TASK-014 A | .956250 -> .913750 (-.042500) | .695408 -> .645986 (-.049422) | 3.453750 -> 3.760000 (+.306250) |
| TASK-014 B | .956250 -> .911250 (-.045000) | .698810 -> .651080 (-.047730) | 3.515000 -> 3.848750 (+.333750) |

Public scenario detail (all dataset scenario detail remains in the raw JSON):

| Scenario | HR@10 RC3/candidate | MRR RC3/candidate | MTTC RC3/candidate |
| --- | --- | --- | --- |
| boundary | 1.000000 / .900000 | .678333 / .661667 | 5.000000 / 6.000000 |
| browsing | .987500 / .962500 | .745273 / .676017 | 2.950000 / 2.862500 |
| buying | .987500 / .925000 | .703690 / .592684 | 3.462500 / 4.000000 |
| intent_override | .933333 / .766667 | .555728 / .513254 | 6.266667 / 6.800000 |

## Runtime and resources

Three counterbalanced pairs ran in fresh Python 3.13.15 processes on Windows,
using the 200-session Public workload.  Medians of the three runs:

| Preset | init s | response p50/p95/p99 ms | total s | peak RSS MiB |
| --- | ---: | ---: | ---: | ---: |
| RC3 | 2.126523 | 12.2146 / 49.6229 / 68.0061 | 15.080837 | 439.19 |
| candidate | 2.958797 | 21.6505 / 59.6179 / 340.5531 | 25.295019 | 970.38 |

Raw paired resource files are under
`reports/generated/task305-runtime-v2/`; the first invalid peak-RSS run under
`task305-runtime/` is superseded and must not be used.

## Models, dependencies and failure handling

- Dense: `sentence-transformers/all-MiniLM-L6-v2` revision
  `1110a243...`, Apache-2.0; 50,000 x 384 float32 vectors generated locally.
- Semantic: `cross-encoder/ms-marco-MiniLM-L6-v2` revision `233902d...`,
  Apache-2.0; local CPU, zero request cost, strict deterministic fallback.
- Runtime dependencies are the existing optional lock: NumPy 2.2.6, ONNX
  Runtime 1.29.0 and Tokenizers 0.23.1.
- LLM attempts were limited to Qwen2.5 0.5B and 1.5B GGUF, Apache-2.0, through
  llama.cpp b10516, MIT.  The pinned 1.5B artifact is 1,117,320,736 bytes and
  costs no per-call fee.  Both generated semantically wrong permutations on the
  fixed probe.  The integration rejects malformed/incomplete permutations and
  falls back; the candidate runner refuses to call that LLM capability complete.
- No credential was present, no paid request was made, and network use remains
  opt-in.  Setup/download hashes are in the ignored model manifests and pinned
  setup scripts.

## Verification and Windows reproduction

From the isolated `source` directory in PowerShell:

```powershell
py -3.13 -m pip install -r requirements-semantic.txt
py -3.13 scripts/build_semantic_index.py --download --batch-size 64
py -3.13 -m unittest discover -v
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0=(Get-Location).Path.Replace('\','/')
py -3.13 scripts/team_gate.py
py -3.13 scripts/task305_demo.py --output reports/generated/task305-demo-repro.json
py -3.13 scripts/task305_evaluate.py --dataset public --semantic local --output reports/generated/task305-public-repro.json
```

RC3 reproduction was run from the separately extracted `rc3-repro` directory:

```powershell
py -3.13 scripts/setup_data.py
py -3.13 scripts/release_check.py
```

It returned exactly HR@10 `.980000`, MRR `.696861`, MTTC `3.755000`, and
TechnicalScore `.843958`.  The complete test result is 210 tests passed with
one intentional skip: the real-local-LLM-success proof, because neither allowed
local model passed.  `TEAM GATE PASSED`, `git diff --check` passed, and no
official evaluator, public data, score/stopping rule or contract file changed.
