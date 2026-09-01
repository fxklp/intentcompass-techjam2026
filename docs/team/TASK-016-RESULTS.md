# TASK-016: RC3 release packaging and local independent-directory acceptance

## Frozen identities

- Algorithm commit: `4968804054bc1159007d34fe40e976bca508fb4f` (accepted TASK-015).
- Packaging source commit: `dec27a1512da32d7192433fb3f0d895c96663462`.
- Branch: `release/TASK-016-rc3`.
- ZIP: `artifacts/release/intentcompass-rc3.zip`, 88,132 bytes, 53 members.
- ZIP SHA256: `ccd8f4f54e99ee3eda0bfc4dcde6cb4862a54e746d4566b87632fcc260790d98`.
- Second build: `intentcompass-rc3-rebuild.zip`, byte-identical checksum.

This handoff report is a later documentation-only commit, not the ZIP's source
commit. Rebuilding the original archive requires a clean checkout of the
packaging commit above, not a later documentation HEAD (manifest embeds HEAD).
The original ZIP is retained and never overwritten.

## What changed and what did not

The stale RC2 release assertion was first reproduced against frozen TASK-015
Public results; it failed with `frozen Public metric mismatch: hit_rate_at_10`.
The release checker was then updated to exact RC3 aggregate/scenario results,
scenario counts, efficiency and zero reported tokens. NaN/non-numeric values
are rejected, not allowed through tolerance comparisons. Demo hit, override,
turn 5 and rank 8 are explicitly asserted.

The preset now explicitly pins lastchance recovery, separate-field precision
and final policy on, alongside existing baseline/offline settings. Effective
runtime components are checked, not inferred from environment variable names.
Manifest schema 2 identifies RC3, the final algorithm and the packaging source.
Verification records Python executable/version, platform, effective components,
manifest/result hashes and protected source/data hashes.

README and bundled method/requirements/video facts were updated. Portable team
instructions are bundled; a separate Chinese relay file and ZIP checksum file
are beside the ZIP. No algorithm, adapter, evaluator, official data, setup-data
checksums, dependency list, or scoring/stopping rule changed. The two previously
accepted synthetic-scenario MRR decreases remain disclosed; packaging is not a
new optimization experiment or all-scenario non-regression claim.

## Executed verification

- 18 release-specific tests passed (8 existing, updated where version-specific,
  and 10 new RC3 tests). Old RC2/TASK-013 metrics, scenario/count regressions,
  invalid numbers, model tokens, inactive final components, altered Demo,
  mixed manifest versions and inherited experimental settings are rejected.
- Full suite: 200 tests, 199 passed, 1 existing optional semantic-assets test
  skipped. Full team gate passed, including the unchanged Public evaluator.
- Clean committed source built twice; archive hashes are equal. ZIP allowlist
  excludes credentials, models, indexes, Git metadata, historical results and
  private data. Released official Public labels are included; catalog is external.
- Two fresh extraction directories: isolated Python (`-I -B`), no Git in PATH,
  no inherited PYTHONPATH or API keys. Only the byte-identical frozen catalog
  was copied in. Setup's existing-file hash path was tested; this stage did NOT
  retest the internet download route.
- Both packaged checks passed and all 200 Public per-session records AND
  aggregate/scenario metrics exactly match the frozen TASK-015 reference.
- Both entire result files have the SAME SHA256:
  `9fbb1bd0cf549715cb9bd4c331285c8dcecfca9841c3fcde8152c2c674ed23dd`.
- Zero network attempts and zero model tokens; Demo first hit turn 5, rank 8.
  Manifest, packaged files and catalog bytes remained unchanged after execution.

| Local extraction | Python | Result |
|---|---|---|
| `artifacts/rc3-py313-bebifzh0` | Anaconda Python 3.13.9 | RELEASE CHECK PASSED |
| `artifacts/rc3-py312-vju0er64` | Codex-bundled Python 3.12.13 | RELEASE CHECK PASSED |

These are two Python environments on the SAME Windows host. They are not
independent teammate reproduction, a macOS test or a fresh latency benchmark.
Final-algorithm timing remains the separately measured TASK-015 result.

Public N=200, HR@10=.98, MRR=.696861, MTTC=3.755, Efficiency=.7245,
recommended TechnicalScore=.843958. This is not an official hidden-set score.

## Evidence and reproduction

Under ignored `reports/generated/`:

- `task016-unit.json`, `task016-gate.json`: exact commands/output and clean source.
- `TASK-016-BUILD.json`: both build records and archive hash.
- `TASK-016-SMOKE-py312.json`, `TASK-016-SMOKE-py313.json`: commands, folders,
  comparison/reference hashes and isolated environment assertions.
- Each extraction's `reports/generated/acceptance/` contains its actual
  `results.json` and `verification.json`.
- `manage_task016.py`: bounded build, QA, safe extraction and audit driver.

After committing this handoff, run `python -B reports/generated/manage_task016.py audit`.
Require `TASK-016-FINAL-AUDIT.json` to contain `audit_passed: true`. It checks
allowed paths, runtime/official source identity versus the algorithm freeze,
all ZIP members against the packaging Git commit, immutable smoke evidence,
exact rebuild identity and preservation of the older RC2 ZIP. Source worktree
must remain clean. Standard proof commands were:

```text
python -B -m unittest discover -s tests -p "test_*.py"
python -B scripts/team_gate.py --full-eval
python -B scripts/build_release.py --output artifacts/release/intentcompass-rc3.zip
python -B scripts/build_release.py --output artifacts/release/intentcompass-rc3-rebuild.zip
```

In each NEW extraction after providing the verified catalog:

```text
python -I -B scripts/setup_data.py
python -I -B scripts/release_check.py --output reports/generated/acceptance
```

Use fresh output directories when repeating; never overwrite original evidence.
The old RC2 ZIP remains untouched at SHA256
`5c404574c2cff1b0549a078e2b7e0484cb38c4aa1f8841370a1603a6cd246379`.

## Relay and remaining boundary

Send the ZIP and `artifacts/release/RC3-队员测试指令.md` to Liu and Cheng through
the lead. Liu uses macOS; Cheng uses Windows. Each verifies the external ZIP
hash, extracts into a fresh directory, and returns their OS/Python, pass/Demo
result, plus the same run's two original JSON files. No code editing or mutual
task assignment. Wang has no task. Recording waits for the lead's signoff.

No remote push, PR, merge, video upload or submission occurred. Independent
teammate/macOS acceptance, publication and final submission materials remain
separate pending work. A verified RC3 package is not contest completion.
