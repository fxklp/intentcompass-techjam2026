# V2 claim and evidence ledger

Status: approved wording candidates for a future recording. `Verified` claims
may be used exactly as bounded below. `Pending` claims require new evidence and
must not enter narration or subtitles yet.

## Product and execution claims

| Claim | Safe wording | Evidence | Commit anchor | Status |
|---|---|---|---|---|
| C01 | “The challenge ranks exact catalog `parent_asin` matches in the first 10 valid unique recommendations, over at most 10 turns.” | `docs/competition_specification.md` and `docs/evaluation_config.json` | `34078351e1c3615e5505a2e829600b56a542e462` and `2a6cc8e776da66ce69b1cbd237838fbc43f32587` | Verified |
| C02 | “IntentCompass is a deterministic, CPU-only Python Agent whose primary scoring path requires no network or model API.” | `docs/submission/first-version-report.md` and `reports/metrics/first-version-runtime.json` | `94e25c633751ad37fbe0499dc1a684959a148358`, evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified for the cited implementation |
| C03 | “The Agent maintains structured active preferences and replaces superseded values instead of appending contradictions.” | `docs/contracts/architecture.md`, `solution/state.py`, and `tests/core/test_state.py` | `8e88d75cbd8f3a1a6c3f6fcfebdd3bc22b9d85bb`, `6a3937445c1f2cf011d28f346ac33dbb9c7c0753`, and TASK-203 base `a81b042d3010fb254519ab56573d03beba111396` | Verified |
| C04 | “Every turn returns a customer message, a structured clarification field, and an ordered Top 10.” | `demo/run_demo.py` and `tests/core/test_agent.py` | `923c31c916fbbdc965b3abb5d9c44bbb296c1b43` and `21ccdee352786cbf4e08114b5e9e7a4402edbb40` | Verified |
| C05 | “In public Intent Override session `public_0183`, the replacement arrives on turn 4 and the first eligible hit is turn 5 at rank 8.” | `demo/run_demo.py` and `docs/submission/first-demo-evidence.md` | `923c31c916fbbdc965b3abb5d9c44bbb296c1b43`, `5bd84367c0103163eda681b5dc64727b147e9210`, and merged PR #5 `a81b042d3010fb254519ab56573d03beba111396` | Verified |

## Metric, feasibility, and limitation claims

| Claim | Safe wording | Evidence | Commit anchor | Status |
|---|---|---|---|---|
| C06 | “On the 200-session public evaluator, HitRate@10 is 0.91, MRR is 0.624024, MTTC is 4.255, Efficiency is 0.6745, and the recommended TechnicalScore is 0.777107.” | `reports/metrics/first-version-runtime.json` | measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified reference result |
| C07 | “Public scenario HitRate@10 is 0.925 Buying, 0.95 Browsing, 0.766667 Intent Override, and 0.9 Boundary.” | `reports/metrics/first-version-runtime.json` | measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified reference result |
| C08 | “The committed reference run reports 0 prompt tokens, 0 completion tokens, no scoring-time network requirement, and estimated API cost USD 0.” | `reports/metrics/first-version-runtime.json` and `docs/submission/first-version-report.md` | `9c59d4874db29dee1d9d839c8339ad870f2a3e46` and `94e25c633751ad37fbe0499dc1a684959a148358` | Verified reference result |
| C09 | “On the committed Windows/Python 3.13 reference run, 833 responses averaged 37.736 ms with p95 76.583 ms, and initialization took 2.933 seconds.” | `reports/metrics/first-version-runtime.json` | measured code `424781522f52e9c1ef1c814ca8dc64eaf24cfead`, evidence commit `9c59d4874db29dee1d9d839c8339ad870f2a3e46` | Verified and must be labeled machine-specific |
| C10 | “A 200-target deterministic shadow evaluation with zero public-target overlap reached HitRate@10 0.895 and TechnicalScore 0.780546.” | `reports/metrics/first-version-shadow.json` | measured code `4ea2cff794318baa5e05ab77e089f2997edbc3cc`, evidence commit `f3722bbebbc81c6d31e1cd914f8ce0d7499adaad` | Verified robustness result, not an official score |
| C11 | “Lexical retrieval can miss semantic matches, index construction has startup cost, personalization is limited, and public and shadow results do not guarantee private-set performance.” | `docs/submission/first-version-report.md` and `reports/analysis/TASK-201-failure-taxonomy.md` | `94e25c633751ad37fbe0499dc1a684959a148358` and `cac52211e4d0eea13c27512689a4e59d13acc86b` | Verified limitations |
| C12 | “Final-submit metrics and latency at the eventual video commit are unchanged.” | No immutable result exists for the future recording commit. | None | Pending, do not claim |
| C13 | “Performance on the organizer’s 800 private sessions is known.” | Private results are unavailable. | None | Pending, do not claim |
| C14 | “Recommendations include product-specific explanations.” | The accepted report lists this as unfinished. | `94e25c633751ad37fbe0499dc1a684959a148358` | Pending, do not claim |

## Team-contribution claims

Contribution wording is derived only from merge commits reachable from the
TASK-203 base. A task assignment or unmerged branch is not contribution
evidence.

| Contributor label | Safe wording | Merged evidence | Status |
|---|---|---|---|
| Integration lane | “PR #1 hardened the repository gate against untracked whitespace.” | Merge `4e4a240a0a6060eaa0b16864fd447785b90b141d` | Verified |
| Liu Chunyi | “PR #2 added file-level whitespace-gate coverage and related task metadata updates.” | Merge `ccd58846a286ae1f102c28388ffe8364787df764` | Verified |
| Cheng Xianyun | “PR #4 added the evidence-validated public failure taxonomy. PR #5 corrected the Intent Override demo and its test-count evidence.” | Merges `184ef33a9cf686b5ef55bc60d6d0b223d762d666` and `a81b042d3010fb254519ab56573d03beba111396` | Verified |
| Wang Siwen | No merged PR attributable to this contributor is present at the TASK-203 base. | None | Pending, no contribution claim |
| TASK-203 authoring | This local storyboard work is not a merged contribution yet. | Future PR, if approved and merged | Pending, no contribution claim |

## Claim update rule

Before recording, rerun the demo, full evaluator, and runtime benchmark at the
final commit. If a value changes, revise the storyboard, subtitles, compact
cards, and this ledger in the same local change. Do not round a changed value
back to an older subtitle and do not infer private performance from public or
shadow results.
