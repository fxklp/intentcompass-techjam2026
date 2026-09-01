# TASK-007: reproducible release packaging and final audit

Owner: team lead / integration Agent. Authorized by the lead's request to
continue the packaging, clean reproduction and final-check stage on 2026-08-31.
Base: dbf78d429686337273d05f92795e6c88d0e0bf8b. No new algorithm experiments.

## Allowed paths

- This task card; README.md; requirements.txt
- scripts/build_release.py; scripts/release_check.py; scripts/run_offline.py
- tests/core/test_release.py
- docs/release/**; docs/team/TASK-007-HANDOFF.md
- Ignored artifacts/** and reports/generated/**

These packaging paths extend the previous task's scope. Do not change
solution/**, starter/**, evaluator/**, data/**, contracts, CI, or historical
evidence. Do not change another checkout. Do not push, merge, submit to Devpost,
upload a video, change repository visibility, spend API funds, or self-approve.
No task for Wang. The lead relays all eventual Liu/Cheng test instructions.

## Acceptance

1. Check the current official web statement, submission rules and Devpost.
   Separate backend contract/scope checks from incomplete feature ambitions,
   and preserve unresolved policy differences rather than claiming compliance.
2. Document one frozen default: integrated / baseline FTS / constraints /
   semantic off / network off. Do not alter default algorithm implementation.
3. Build a deterministic allowlisted ZIP from a clean committed source tree,
   recording source commit and per-file raw SHA256. Exclude catalog, credentials,
   local artifacts, caches, models, data labels other than released Public.
4. Extract it to a new directory; create a fresh standard-library-only venv;
   download/verify official data; run contract checks, unchanged official
   evaluator, and actual demo without Git, API credentials, or model assets.
   Record actual outputs and the full Public per-session results, not mock text.
5. Test altered/missing payloads, unsafe paths and experiment-env isolation;
   run all tests and full team gate, audit protected-file diff and clean state.
6. Prepare English overview/method/limitations and a current video claim sheet.
   Do not overwrite Cheng's older storyboard; identify its outdated passages.
   Leave public upload, final video, teammate OS validation and submission pending.
7. Only defects blocking reproducibility/correctness may reopen implementation.
