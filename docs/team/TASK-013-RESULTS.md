# TASK-013 results: accept pure field-aware precision ordering locally

Date: 2026-08-31. Windows 11, Python 3.13.9. Local integration only; no push,
PR, merge, API request, teammate assignment, release ZIP replacement or claim
of official hidden-set performance.

## Decision and immutable source

- Prior accepted baseline: TASK-011 `d33c1d39ce036cb8a747779702700a56d38a1ac3`.
- Two-candidate freeze: `6bff218c8aee180a267be1e95417a44b9ddb0e5f`.
- Verified default runtime: `2bdb6ae0b3ce9907ac3284b58d9e483c7fbc25aa`.
- Select `separate`, enable it only in this worktree; `off` retains the exact
  previous behavior. `joined` remains a small diagnostic/reference option,
  not a separately confirmed production recommendation.

The default commit changes only the default constant after both independent
confirmations pass. Default Public, original Shadow, confirmation A and B then
exactly reproduce the selected frozen candidate's metrics; Public session
records match too. No policy tuning followed either confirmation.

## What research changed

See [dataset-specific research](TASK-013-RESEARCH.md) for papers, author code and
technical blogs, with direct-dataset versus adjacent-task distinctions.
We extracted TASK-012's previously unconfirmed **pure** safe phrase ordering,
without its rejected question policy, and added primary-field boundary safety.
It stable-partitions the existing same-category Top10 using all explicit
positive phrases, and skips budget/exclusion/fallback cases. It adds no model,
dependency, learned parameter, index, data source, retrieval route or question.

Both `joined` and `separate` had identical Public and Shadow metrics. Therefore
the field-boundary guard has **no separately measured score gain** on those
sets; it won the predeclared tie-break for safety. The measured improvement is
primarily validation of the extracted full-phrase precision policy. This is an
original lexical adaptation, not reproduction of neural paper result tables.

## Quality results

Tables reproduced by `python -B -m reports.generated.tables_task013` from the
immutable `task013-off-*.json` and `task013-default-*.json` reports below.

| Set | HR old/new | MRR old/new | MTTC old/new | Technical score old/new |
|---|---|---|---|---|
| Public, 200 reused | 0.975000 / 0.975000 | 0.674004 / 0.693046 | 4.190000 / 4.190000 | 0.825901 / 0.831614 |
| Shadow, 200 reused | 0.960000 / 0.960000 | 0.684288 / 0.698732 | 3.740000 / 3.740000 | 0.830486 / 0.834820 |
| Confirmation A, 800 fresh | 0.937500 / 0.937500 | 0.680755 / 0.690276 | 3.806250 / 3.806250 | 0.816851 / 0.819708 |
| Confirmation B, 800 fresh | 0.937500 / 0.937500 | 0.668590 / 0.680633 | 3.627500 / 3.627500 | 0.816777 / 0.820390 |

This is an MRR/score gain with HR and MTTC unchanged, not improvement in every
individual metric. HR/MRR nondecrease and MTTC nonincrease were checked overall
and in every scenario, tolerance 1e-6. No failures in any of the four sets.

| Set | Boundary MRR delta | Browsing MRR delta | Buying MRR delta | Override MRR delta |
|---|---|---|---|---|
| Public | +0.000000 | +0.016250 | +0.031354 | +0.000000 |
| Shadow | +0.000000 | +0.000417 | +0.035695 | +0.000000 |
| Confirmation A | +0.016667 | +0.010248 | +0.010272 | +0.003194 |
| Confirmation B | +0.004167 | +0.013318 | +0.014630 | +0.004365 |

Every scenario HR and MTTC delta is exactly zero in the reported metrics.
Public-only session audit: eight improved ranks, zero worsened ranks; first-place
hits 112 -> 117; every hit flag and first-hit turn unchanged. Fresh confirmation
target/session rows were not inspected by the algorithm work; only aggregate
outputs were exposed. No per-session non-regression claim for the fresh sets.

Both new 800-session sets exclude Public, original Shadow and TASK-008/010/011/012
confirmation targets, and exclude each other. Seeds and exclusion order were
frozen in the task card and test wrapper before generation. These are synthetic
dialogs using the same official simulator family, not unseen real-user tests.

## Controlled speed and memory

Three alternating fresh-process pairs, sequential, first allowed CPU only
(affinity mask 1); same Public200 and 833 responses per run. Each timing run
also checks exact quality equivalence. Values below are medians across three
runs, except peak memory, which is the maximum of three whole-process peaks.
The process contains evaluator/catalog bookkeeping as well as Agent memory.

| Measure | TASK-011 behavior (`off`) | New default |
|---|---:|---:|
| Initialization seconds | 3.235555 | 3.253883 |
| Response p50 ms | 15.740 | 18.600 |
| Response p95 ms | 87.655 | 95.253 |
| Response p99 ms | 127.766 | 136.338 |
| Peak process bytes | 458477568 | 463097856 |

The p95 increase is about 7.6 ms and maximum observed peak-memory increase about
4.6 MB (decimal). This is a modest measured cost, not a speed improvement. Host
background load and platform affect timings. Development/confirmation run
timings under concurrent work are not used for this comparison. No API tokens,
network attempts or API costs occurred in the frozen proof runs.

## Tests, demo and protected boundaries

- New precision tests: 11/11, including token/field boundaries, conjunction,
  group/tie/head-membership/tail preservation, budget/exclusions, fallback,
  missing text, reset/override/session isolation, zero top_k and invalid config.
- Full suite: 177 tests, 176 passed, one optional local-model test skipped.
  Unchanged existing tests; full `TEAM GATE PASSED` with the new default.
- Separate synthetic Agent checks preserve complete budget, exclusion and
  no-match fallback payloads, with network blocked and zero-output checks.
- Demo: `DEMO RESULT: OFFICIAL HIT after intent override`, turn 5, rank 8.
- Runtime change: 58-line module plus 12 orchestration lines. State parsing,
  questions, terminal recovery, retrieval and official evaluator/data unchanged.
- Frozen catalog SHA256:
  `da979b05a68af864cb0dcf9ee6a81c010c7e66a57978ad286c7a2e005fc69a67`.
- Prior TASK-011 worktree remains clean at its original SHA. RC2 ZIP unchanged,
  SHA256 `5c404574c2cff1b0549a078e2b7e0484cb38c4aa1f8841370a1603a6cd246379`.

## Evidence and reproduction

All paths below are under ignored `reports/generated/`, never submission data.
Each experiment JSON contains exact commit/source/data hashes, split digest,
clean-worktree status, environment, metrics, network attempts, time and memory.

- `TASK-013-SELECTION.json`: SHA256
  `dcb0919710c5b44618dbc99aa1d87aec3a501350606f7be4f1875b410fdbb139`.
- `TASK-013-CONFIRMATION-GATE.json`: SHA256
  `8296977af6b7eb727cbd2e62d02eeeb8709a41c9d2be235bca1cffdea8f4158e`.
- `TASK-013-TIMING.json`: SHA256
  `931529f3250f20c28782de1b108fcd9eaa9bd8f3823de4380d1a8429276b4fb0`.
- `TASK-013-MANUAL-SAFETY.json`, `TASK-013-PUBLIC-DELTA.json`.
- `task013-start-public.json`; `task013-{off,joined,separate}-{public,shadow}.json`;
  `task013-{off,separate}-{confirm_a,confirm_b}.json`;
  `task013-default-{public,shadow,confirm_a,confirm_b}.json`;
  `task013-timing-{1,2,3}-{off,default}.json`.
- Final `TASK-013-FINAL-AUDIT.json` is emitted after this documentation commit;
  inspect `audit_passed` and its per-file checksums. It validates the 21 proof
  report inventories against their Git archives, protected inputs and allowed
  paths, including the selection/confirmation evidence chain.

Use a new output filename on reproduction; never overwrite original evidence:

```text
python -B -m tests.core.check_precision --variant default --split public --output reports/generated/recheck-public.json --expected reports/generated/task013-default-public.json
python -B -m tests.core.check_precision --variant off --split public --output reports/generated/recheck-old.json --expected reports/generated/task013-off-public.json
python -B -m unittest tests.core.test_precision_order
python -B scripts/team_gate.py --full-eval
python -B -m demo.run_demo
git diff --check
git status --short
```

## Handoff and limitations

The accepted implementation is local to branch
`experiment/TASK-013-precision-order`. It is not in `main` or the existing RC2
ZIP. The legacy `scripts/release_check.py` still encodes RC2 metrics and requires
its release manifest; it was not altered or used to certify this new snapshot.
Do not label this work as a newly packaged release or cross-platform acceptance.
Next release preparation must deliberately update release expectations/manifests,
package a new version, and request Windows/macOS reproduction through the lead.

Do not claim theoretical saturation: exact phrases miss paraphrases and implicit
needs; small synthetic sets cannot prove hidden-data or real-dialogue quality.
Semantic rerankers remain a possible future experiment but were not justified
as a default by the cited papers alone. Preserve this finite, verified gain and
avoid further unplanned parameter changes before integration and release checks.
