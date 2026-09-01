# TASK-306 capability-complete candidate handoff

This candidate starts from immutable RC3 source commit
`d15dcc0fec037ff005c115d62ea7689ed92b152f`. RC3 remains the rollback. The
official evaluator, catalog, Public set, scoring formula and stopping rules were
not edited. Generated evidence is intentionally ignored by Git and must be
transferred with the candidate evidence bundle.

## Candidate configuration

The normal `Agent` default is `integrated / capability / local`. It keeps one
in-memory SQLite FTS5 catalog and, when the verified assets are present, one
in-memory 50,000 x 384 float32 dense matrix. Expensive semantic inference is
demand-driven for exploratory Browsing or lexical-miss recovery. Missing or
invalid optional assets fail closed to the lexical pipeline; no runtime download
occurs. The RC3 `release_check.py` deliberately activates the frozen RC3 preset
and therefore is rollback evidence, not TASK-306 acceptance evidence.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-semantic.txt
.\.venv\Scripts\python.exe scripts\setup_data.py
.\.venv\Scripts\python.exe scripts\build_semantic_index.py --download
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe scripts\task306_evaluate.py --split public --semantic local --output reports\generated\task306\public.json
```

Use `python3` and `.venv/bin/python` on macOS/Linux. The catalog-derived vector
build measured 1783.905 seconds once on the development host; reuse only an
artifact whose manifest hashes match the catalog and pinned models.

## Capability matrix

| Track 4.2 capability | Production entry and actual effect | Proof | Default/limits |
|---|---|---|---|
| Buying/Browsing routing | `WorkflowState.plan` selects a route; `CapabilityRetriever.search` executes exact-constraint routes for Buying and expansion/dense routes for Browsing. | Public: 632 Buying and 115 Browsing responses; direct route test. | On. Route is based only on visible dialogue state. |
| Buying conditions | `_constraint_state` distinguishes satisfied, conflict and unknown. Known upper-budget or explicit negative conflicts are filtered when enough results exist; otherwise relaxation is explicit in trace. | Budget, missing metadata and route tests. | On. Parent-level absent attributes remain unknown; they are never invented as satisfied. |
| Browsing dense and diversity | `DenseIndex` runs real ONNX text embedding and in-memory cosine retrieval. Exploratory fusion uses bounded category diversity. | `test_task306_real_models` executes the actual embedding model, dense matrix and candidate evidence. | On demand. Missing assets use lexical fallback. |
| Multi-route recall | Keyword/category/exact/expanded/dense are independently queried, deduplicated and scored. Dense exploratory fusion may add candidates; ordinary routes fill unused result capacity without displacing the proven lexical head. | Direct tests plus route candidate counts in evaluation reports. | On. Independent-route candidates never evict the ordinary compatibility head. |
| Semantic ranking | Local MS MARCO MiniLM cross-encoder can reorder the real candidate window. Existing budgeted Qwen/DeepSeek adapters are in the same decision chain and strictly validate ID permutations. | Actual local inference test; `live-llm-proof.json` completed Qwen `qwen3.8-max`, 3726/54 tokens, 10 valid IDs. | Local on demand by default with assets. External LLM is opt-in because credentials/network cannot be shipped; it is not required by official rules. |
| Information accumulation/override | Existing session slots replace corrections, clear no-preference values and isolate reset sessions. | Existing state/adaptive/final tests. | On; no raw transcript persistence. |
| Over-general cutoff/recovery | `_broad` returns before any FTS/model call, records skipped expensive work and asks for clarification; a concrete reply resumes normal retrieval. | Mock call-count plus end-to-end tests. | On for narrowly enumerated genuinely empty/generic requests. |
| Explicit profile handoff | `export_profile` exports bounded preference tags with a consent marker; only a caller-supplied next reset consumes them. | Cross-session influence and isolation test. | Optional. Never joins users by `session_id`. |
| Dynamic workflow | Rejection/override/overload changes pool size, query state, questions and guarded terminal recovery; it is not a label-only branch. | Recovery test asserts workflow, pool >= 80 and retained constraints; existing terminal tests. | On and session-local. |
| Metrics/resources | Candidate evaluator uses original scoring and target-blind source; reports latency, memory, trace events and all scenarios. | Four paired aggregate/scenario JSON reports. | No GPU, training, UI, multimodal processing or external vector database. |

## Quality results

All values below equal RC3 on the same already-used sets; none are claimed as
fresh holdouts. The allowed deltas were HR/MRR -0.005 and MTTC +0.10.

| Set | N | HR@10 | MRR | MTTC | Delta vs RC3 |
|---|---:|---:|---:|---:|---|
| Public | 200 | .980000 | .696861 | 3.755000 | 0 / 0 / 0 |
| Synthetic Shadow | 200 | .965000 | .703615 | 3.545000 | 0 / 0 / 0 |
| Existing TASK-014 A | 800 | .956250 | .695408 | 3.453750 | 0 / 0 / 0 |
| Existing TASK-014 B | 800 | .956250 | .698810 | 3.515000 | 0 / 0 / 0 |

Candidate single-process p95 was 119.51 ms Public, 127.52 ms Shadow, 131.58
ms A and 124.20 ms B on Windows; initialization was about 3.8 seconds with
assets. These are machine-specific and not an official score. Public/Shadow/A/B
reports preserve all scenario metrics; dense/semantic did not needlessly fire
on the scripted benchmark wording, so functional model proof is separate.

## Model, data, API and fallback disclosure

- Embedding: `sentence-transformers/all-MiniLM-L6-v2`, revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0.
- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L6-v2`, revision
  `233902d25c440f23af6f7d6e94d2946bac0bee0a`, Apache-2.0.
- CPU dependencies are pinned in `requirements-semantic.txt`; models are ONNX,
  text-only, and not trained or fine-tuned here.
- Dense vectors derive only from the supplied catalog. The index manifest binds
  catalog SHA256 `da979b05a68af864cb0dcf9ee6a81c010c7e66a57978ad286c7a2e005fc69a67`.
- The successful Qwen proof increased the conservative local ledger by
  RMB 0.058274. It proves integration, not metric improvement. Keys and ledger
  are excluded. Network/model failure keeps the offline order and opens a
  circuit breaker; unknown billed usage is never reported as zero.

## Honest limitations

The official scripted sets do not contain every trigger, so direct target-blind
tests prove dense, diversity, cutoff, profile handoff and LLM/local ranking.
Catalog metadata is parent-level; ordinary missing variant attributes stay
unknown. The candidate preserves RC3's validated Top-10 on ordinary traffic,
so richer fusion is intentionally concentrated on exploratory or recovery
requests. No claim of hidden-set, business-conversion or global optimality is
made.
