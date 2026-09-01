# TASK-016: Package the accepted final algorithm as RC3

Owner: team lead / integration Agent. User authorized the next packaging step.
Base: TASK-015 `4968804054bc1159007d34fe40e976bca508fb4f`.
No new algorithm optimization. Retain the accepted TASK-014 scenario tradeoffs;
do not present adoption as strict all-scenario non-regression.

## Allowed paths

- This card and `docs/team/TASK-016-RESULTS.md`
- `scripts/release_check.py`, `scripts/build_release.py`
- `tests/core/test_release.py`, `tests/core/test_release_rc3.py`
- `README.md`, `docs/release/METHOD.md`, `docs/release/REQUIREMENTS.md`,
  `docs/release/VIDEO-HANDOFF.md`, `docs/release/TEAM-TEST.md`
- Ignored `artifacts/**`, `reports/generated/**` for builds/proofs/fresh extraction
- Byte-identical ignored catalog copies for offline extraction testing

No changes to `solution/**`, `starter/**`, `evaluator/**`, official public data,
setup data checksums, interfaces, requirements or CI. Release-specific test
expectations may be upgraded to the frozen final results, never relaxed to a
minimum/approximation to conceal packaging bugs. No keys, paid APIs, model
downloads, remote push/PR/merge, video upload or contest submission.

## Work

1. Reproduce the known stale RC2 release expectation failure before editing.
2. Update release-only expected overall/scenario metrics and effective policy
   checks to TASK-015. Pin final preset explicitly; maintain environment cleanup,
   zero-network checks, protected-file hashes and manifest verification.
3. Version the bundle/manifest RC3. Update bundled runtime/method/video facts;
   include portable Windows PowerShell and macOS test instructions.
4. Add exact new metrics, old-version rejection, scenario regression and final
   policy validation tests. Preserve secret, integrity and offline safeguards.
5. Freeze a clean local commit; build TWO allowlisted deterministic ZIPs and
   require equal SHA256. Preserve all existing archives.
6. Safely extract to new independent directories, with no Git/parent-repository
   dependency. Copy only the unchanged frozen catalog; separately validate the
   setup script's existing-file checksum path (no new network download needed).
7. Run packaged release checks using Python 3.13 and, if available, bundled 3.12.
   Require exact Public aggregate/scenario AND per-session equality to TASK-015,
   working demo, zero network/model tokens, and unchanged bundle files.
8. Full unit suite, full team gate, allowed-path and source/data diff audits;
   confirm runtime bytes identical to TASK-015. Produce checksums and handoff.

## Acceptance boundary

This establishes a locally verified release candidate, not independent macOS
acceptance, an official hidden score, complete contest deliverables, or public
publication. Liu/macOS and Cheng/Windows receive short read-only tests through
the lead, report only to the lead, and do not assign each other tasks. Wang is
not assigned work. Existing RC2 stays recoverable. Only after signoff should
the lead authorize recording/publication/submission separately.
