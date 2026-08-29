# First repeatable demo

From the repository root, run:

```bash
python demo/run_demo.py
```

The default scenario is the labeled public Intent Override session
`public_0072`. It is selected because the accepted core commit finds the target
immediately after the official simulator sends the correction.

The demo prints:

- customer messages;
- structured active preferences;
- the current retrieval query;
- `ask_attribute` and Agent reply;
- ordered Top 10 identifiers;
- target rank and first-hit turn.

The harness reads the public target only to reproduce the official simulator and
display the rank. `starter.Agent` receives only `user_profile` in `reset` and the
customer message/turn/Top K in `respond`. No target or ground truth is passed to
the Agent.

This is an evidence/demo harness, not an alternative evaluator. Final reported
scores must still come from the unmodified official evaluator.
