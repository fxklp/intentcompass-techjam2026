# TASK-306 capability-complete integration

Owner: team lead automation Agent. Base: RC3 `d15dcc0fec037ff005c115d62ea7689ed92b152f`.

The team lead explicitly takes over TASK-305 because Wang is unavailable. This
task temporarily authorizes coordinated edits to `solution/**`, the thin
`starter/agent.py` adapter if necessary, new `tests/**`, new `scripts/task306_*`,
`requirements*.txt`, `docs/decisions/ADR-TASK306*`, and
`docs/release/task306/**`. Official evaluator, data, scoring, stopping rules and
published contract files remain immutable.

Deliver a production candidate that genuinely exercises every Track 4.2
capability through observable, target-blind conditions. Existing capabilities
should improve when cheap. Missing capabilities must be implemented rather than
papered over or globally disabled. An on-demand path counts when it is part of
the submitted default and reproducibly triggers on qualifying input; a mock or
experiment-only path does not.

Compare against RC3 on Public, Shadow and existing TASK-014 A/B. Working
tolerance per set: HR@10 decrease <= .005, MRR decrease <= .005, MTTC increase
<= .10. Report every scenario and do not hide concentrated regressions. Preserve
offline fallback, disclose model/network/cost, and retain a clean rollback to
RC3. Do not tune to sample IDs, target ASINs, or private labels.
