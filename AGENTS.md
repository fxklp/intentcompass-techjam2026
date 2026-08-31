# Track 4 repository rules

## Mission

Build the smallest reproducible Python shopping Agent that improves the official
Track 4 metrics without modifying the benchmark. Optimise for private-set
generalisation, deterministic evidence, offline operation, and a clear
three-minute demonstration.

## Required reading

Before editing code, read:

1. `docs/competition_specification.md`
2. `docs/submission_rules.md`
3. `docs/contracts/architecture.md`
4. `docs/team/OWNERSHIP.md`
5. the assigned file under `docs/team/tasks/`

## Non-negotiable competition rules

- Never edit `evaluator/**`, `data/public_set.jsonl`, public labels, metric
  formulas, stopping rules, or official API-contract files.
- Never hard-code public targets, session identifiers, expected answers, or
  rules learned by manually inspecting locked holdout labels.
- Final recommendations must be valid frozen-catalog `parent_asin` values.
- Preserve the required `Agent.reset(...)` and `Agent.respond(...)` interface.
- The critical path must run without API credentials or network access. An LLM
  may improve the system, but an offline fallback is mandatory.
- Never commit keys, tokens, private data, absolute local paths, raw model logs,
  large generated indexes, or undocumented binary assets.

## Scope and ownership rules

- Modify only the paths listed in the active task card under `Allowed paths`.
- Do not edit another owner's files to make your code work. Propose a contract
  change in `docs/decisions/` and stop until the integration owner approves it.
- Only the integration owner may edit `starter/agent.py`, shared contracts,
  root dependency files, CI, or common configuration.
- Keep `starter/agent.py` a thin adapter. Business logic belongs in `solution/`.
- Do not add a dependency, model, API, index, or new data source without a
  written rationale, license/source note, cost, fallback, and reproduction step.

## Implementation rules

- Reproduce the baseline or failing case before coding.
- Prefer small pure functions and explicit typed data over hidden globals,
  prompt-only state, copied logic, or large all-purpose classes.
- One module has one purpose. Do not duplicate state parsing, scoring, retrieval,
  or validation logic across modules.
- New behavior requires tests for the normal case and at least one boundary,
  override, invalid-output, or failure case.
- Do not weaken assertions or change fixtures merely to make a test pass.
- Generated outputs belong under ignored `artifacts/` or `reports/generated/`
  and must have a command and checksum/manifest when handed off.

## Definition of done

Before claiming completion:

1. Run `python scripts/team_gate.py`.
2. Run every proof command in the task card.
3. Inspect `git diff --check` and `git status --short`.
4. Report changed files, commands and results, metric deltas, known risks, and
   unfinished work.
5. Confirm the diff touches only the task card's `Allowed paths`.

If any rule cannot be followed, stop and describe the blocker. Do not invent a
workaround that changes the evaluator, interface, data, or another owner's code.
