# TASK-011: validated offline recovery update

## Outcome

Accept the local default **lastchance** implementation at runtime commit
`5ce1b5ad59b21c6f0082775d89957e742395251c`. It improves overall HR, MRR and MTTC
on Public, original Shadow and a new 800-session confirmation, without any
scenario regression. This is a validated local algorithm update, **not** a claim
of theoretical optimality, an official hidden-set result or a new release ZIP.
GitHub, old RC2, its ZIP and submission/video materials have not been replaced.

| Dataset | Agent | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | ---: | ---: | ---: | ---: |
| Public 200 | RC2 | .910 | .648734 | 4.255 | .784520 |
| Public 200 | New default | .975 | .674004 | 4.190 | .825901 |
| Original Shadow 200 | RC2 | .895 | .656149 | 3.805 | .788245 |
| Original Shadow 200 | New default | .960 | .684288 | 3.740 | .830486 |
| New confirmation 800 | RC2 | .89875 | .666261 | 3.89375 | .791378 |
| New confirmation 800 | New default | .93375 | .686097 | 3.85875 | .815529 |

Public recovers 13 of RC2's 18 failures; **all 182 previously successful sessions
have exactly the same hit turn and rank**. Shadow gains 13 hits; the new
confirmation gains 28. Boundary metrics are unchanged, not improved. Full
per-scenario figures are in the generated reports. TechnicalScore is only the
official metric formula's output, not the complete judging score.

The new confirmation seed is `intentcompass-task011-final-20260831`, with no
target overlap with Public, original Shadow, TASK-008 confirmation or TASK-010
confirmation. It uses the unchanged public simulator/schema and the prescribed
scenario mix. It is synthetic; Public and original Shadow have been reused,
and none of these results guarantees an official hidden-set score.

## What changed, and why

Normal ranking and clarification stay unchanged. Two guarded recovery events
can replace repeated results with un-rejected candidates:

1. The user explicitly rejects the previous output after available questions
   are exhausted, with the same active intent.
2. At the final turn, the user has no additional preference or rejects options,
   active intent is unchanged, and the proposed output exactly matches what
   was actually shown on the previous turn.

The second condition is an independent protocol-boundary experiment, declared
in TASK-011 after TASK-010 policy selection, not silently appended to that
experiment's preregistration. The final-turn restriction avoids replacing a
later high-ranked success with an earlier low-ranked hit. Reset, explicit
override or changed active preferences clear rejection history. No-preference
alone is not generic item rejection. Empty outputs and changed Top-K output do
not satisfy the repeated-output condition. No-match popularity fallback remains
byte/order compatible. The Agent never reads a target, scenario label or
simulator state.

Recovery uses the same frozen n-gram evidence score selected in TASK-010:
category, primary-field unigram/bigram/trigram coverage, complete phrases,
minimum preference coverage, baseline rank prior, budget and exclusions.
Normal retrieval remains 50 candidates; the 200-item pool and primary-field
reader are activated only when relevant. No new dependency, model, API,
embedding index or external database is required.

TASK-010 compared 15 policies informed by
[RankNet](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/08/icml_ranking.pdf),
[ProductAgent](https://aclanthology.org/2025.emnlp-industry.25/),
[ConvPS](https://arxiv.org/abs/2411.14466) and
[BLaIR](https://github.com/hyp1231/BLaIR-Bench).
Always-on learned/phrase reranking regressed protected scenarios; its models,
training traces and experimental modes are not included in this extracted
component. These are adapted ideas, not reproductions of the full paper models.

## Response speed and memory

Three alternating fresh-process Public pairs, same first-allowed-CPU affinity,
Windows / Python 3.13.9; each run reproduced exact metrics and sessions:

| Measurement | RC2 control | New default |
| --- | ---: | ---: |
| Median p50 | 14.151 ms | 16.747 ms |
| Median p95 | 81.487 ms | 91.500 ms |
| Median p99 | 129.315 ms | 130.013 ms |
| Median Agent initialization | 3.399 s | 3.444 s |
| Largest measured process peak | 455,053,312 bytes | 457,699,328 bytes |

p95 increases about **10.0 ms / 12.3%**, while p99 is essentially unchanged.
This is a quality/latency tradeoff, not a speedup. Memory is the full evaluation
process including evaluator/catalog, not isolated Agent memory. Development
and confirmation timings were noisier and sometimes overlapped non-timing QA;
do not use them instead of these controlled pairs. No old relative +5% team
speed veto was applied. The official core formula is HR/MRR/turn-based;
latency still matters for feasibility, and results vary with host load/hardware.

## Verification and provenance

- Extracted `terminal` exactly reproduces TASK-010 late_ngram Public sessions,
  original Shadow metrics and its independent 800 confirmation metrics.
- `lastchance` was frozen at `6b3a4ee2c76c2a35fb7f66c9454fd80bc51caeca`
  before Public/Shadow evaluation. The final default at `5ce1b5a` exactly
  reproduces those results and passes the new 800 confirmation without tuning.
- 166 tests: 165 passed, one optional-model skip. `TEAM GATE PASSED`.
- Headless demo: `OFFICIAL HIT after intent override`, turn 5, rank 8.
- Zero network attempts, zero model tokens, zero API cost; no keys read.
- `TASK-011-AUDIT.json` verifies 16 metric reports against both source commits,
  protected data/evaluator hashes, all overall/scenario gates, preserved Public
  successes, six independent timing processes, and unchanged RC2 ZIP SHA256.
- RC2 ZIP remains
  `5c404574c2cff1b0549a078e2b7e0484cb38c4aa1f8841370a1603a6cd246379`.
- Changes relative to RC2: this report and task card, `solution/adaptive.py`,
  `solution/terminal_recovery.py`, and two `tests/core/*terminal*.py` files.
  No evaluator, official data, retrieval-owned file or shared contract changed.

Run from this checkout:

```text
python -B -m tests.core.check_terminal --variant default --output reports/generated/NEW-default.json
python -B -m tests.core.check_terminal --variant rc2 --output reports/generated/NEW-rc2.json
python -B scripts/team_gate.py --full-eval
python -B -m demo.run_demo
```

Use `--split shadow` or `--split confirmation` for reproducible aggregate
validation; never retune against the confirmation records. The explicit `rc2`
control disables recovery; normal direct Agent callers can set
`INTENTCOMPASS_TERMINAL_RECOVERY=off` for that behavior. The preset helper clears
inherited environment overrides, so prefer the check runner for comparisons.

## Remaining limits

This is the strongest all-gate-passing implementation from this finite search,
not a mathematical global optimum. Five Public targets and 53 targets in the
new 800 remain missed; most recovered hits occur at turn 10, so MTTC improvement
is modest. Better early information gathering, semantic generalization and
ranking remain research opportunities. No target-specific patch or relaxed
metric gate was used to eliminate those misses. Only Windows was newly tested
here; teammates' fresh macOS/Windows package acceptance and release/video
refresh are later steps, not claimed complete by this algorithm experiment.
