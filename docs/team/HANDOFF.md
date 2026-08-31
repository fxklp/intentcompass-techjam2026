# Branch and handoff protocol

## Do not pass loose project files

Code handoff means a Git commit or pull request. Do not send ZIP archives,
overwrite `agent.py` in chat, copy folders through messaging apps, or use
"accept both changes" during conflicts.

Large generated artifacts are transferred separately with a manifest and
SHA-256 checksum. The repository stores only the manifest, build command, and
download location.

## Branch format

```text
core/TASK-001-state-policy
qa/TASK-101-contract-regression
analysis/TASK-201-baseline-failures
retrieval/TASK-301-field-aware-bm25
```

One branch has one owner, one task card, and one primary outcome. Branches should
live less than six hours and avoid more than roughly 400 effective changed lines.

## Before work

1. Pull/rebase the current integration branch.
2. Read `AGENTS.md`, the architecture contract, and the task card.
3. Post exactly:

```text
[OWN] TASK-___ short outcome
[PATHS] exact allowed paths
[PROOF] exact commands
[BLOCK] none / decision needed by HH:MM
```

4. Confirm no other active task owns the same file.

## Required handoff manifest

Every branch or PR description must contain:

```text
Task:
Base commit:
Head commit:
Changed paths:
Contract changed: no / ADR link
Commands run:
Results and metric delta:
Generated artifacts + SHA-256:
Known risks:
Unfinished work:
Reviewer:
```

The receiver verifies the commit hash and reruns the commands. A screenshot,
Agent message saying "done", or copied terminal text is not sufficient.

## Merge order

```text
contract -> core adapter -> retrieval -> QA evidence -> submission/docs
```

Before merge:

1. Rebase onto the latest integration branch.
2. Run `python scripts/team_gate.py`.
3. Reviewer checks path ownership and the complete diff.
4. Reviewer reproduces at least one proof command.
5. Integration owner merges and reruns the gate on the integrated branch.

## Interface conflicts

When two branches need the same file, stop one branch immediately. The shared
contract owner lands the smallest contract/adapter change first; the other owner
rebases and adapts. Never ask a third coding Agent to blindly merge two generated
implementations.

## Artifact manifest example

```json
{
  "name": "catalog-field-index-v1",
  "source_catalog_sha256": "...",
  "artifact_sha256": "...",
  "build_command": "python scripts/build_index.py ...",
  "created_from_commit": "...",
  "python": "3.11.x",
  "notes": "No public labels or private data used."
}
```
