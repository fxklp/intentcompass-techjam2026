# TASK-404: remote pull-request gate

Owner: Integration owner
Reviewer: Liu Chunyi

## Allowed paths

- `.github/workflows/team-gate.yml`
- `scripts/team_gate.py`
- `docs/team/GITHUB_SETUP.md`
- `docs/team/tasks/TASK-404-ci-gate.md`

## Outcome

Every pull request automatically downloads and verifies the official catalog,
runs local policy and contract checks, executes all tests and 200 public
sessions, enforces the P0 public score thresholds, benchmarks runtime, and
retains both evidence JSON files. Official protected files are compared to
the immutable organizer base commit rather than the mutable team `origin/main`.

## Proof

```text
python scripts/team_gate.py --full-eval
```

After the remote is connected, GitHub Actions must show a successful job named
`full-evaluator` before the first teammate branch is merged.
