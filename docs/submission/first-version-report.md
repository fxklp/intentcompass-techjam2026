# IntentCompass first-version report

Status: reproducible P0/P1 baseline; update team contributions and final private
evaluation observations before submission.

## Method and architecture

IntentCompass is a deterministic, CPU-only conversational product-search
Agent. `starter/agent.py` is a thin official-interface adapter. The implementation
under `solution/` separates:

- structured per-session preference state;
- explicit replacement and clearing for intent overrides/boundaries;
- dynamic lexical retrieval queries;
- an in-memory SQLite FTS5/BM25 candidate index over the frozen catalog;
- constraint-aware reranking;
- a non-repeating clarification policy.

The evaluator passes only `user_profile`, customer messages, turn number, and
Top K to the Agent. Ground truth and simulator state never enter the Agent.

## Model, network, tokens, and cost

- model/API: none;
- dependencies: Python 3.10+ standard library and SQLite FTS5;
- network during official scoring: not required;
- offline fallback: the offline implementation is the primary path;
- reported prompt/completion tokens: 0/0;
- estimated per-run API cost: USD 0.

Network is used only by `scripts/setup_data.py` before scoring to fetch the
organizer's frozen catalog. The final runtime consumes the local verified file.

## Reproducible public evidence

Command:

```bash
python scripts/team_gate.py --full-eval
```

At the accepted first-version baseline:

- public sessions: 200;
- HitRate@10: 0.91;
- MRR: 0.624024;
- MTTC: 4.255;
- Efficiency: 0.6745;
- recommended TechnicalScore: 0.777107;
- Buying/Browsing/Intent Override/Boundary HitRate@10:
  0.925/0.95/0.766667/0.9.

A deterministic 200-target catalog shadow evaluation excludes every public
target and keeps the official 80/80/30/10 scenario mix. It reached HitRate@10
0.895 and TechnicalScore 0.780546. Run `python scripts/shadow_evaluator.py`;
this is robustness evidence, not an official score.

Runtime evidence is generated, rather than typed manually, with:

```bash
python scripts/benchmark_runtime.py
```

See `reports/metrics/first-version-runtime.json` for the accepted clean-worktree
measurement and `reports/generated/runtime-benchmark.json` for the latest local
run. At commit `4247815` on Windows/Python 3.13, 833 `respond` calls averaged
37.736 ms with p95 76.583 ms; Agent initialization took 2.933 seconds. These
numbers are machine-specific and must be regenerated on the final environment.

## Demonstrated session

`python demo/run_demo.py` reproduces public Intent Override session
`public_0072`. On turn 3 the user replaces `Department: womens` with `Faux Fur`.
The stale value disappears from active state and the query, and the target is
rank 1 after the override. The accompanying narration fits within three minutes.

## Limitations

- Lexical FTS5 retrieval can miss synonyms and semantic matches absent from the
  product text.
- Building the in-memory index has startup cost and duplicates catalog data in
  memory.
- Aggregate profile metadata is retained safely but is not yet used deeply for
  personalization.
- The clarification policy is deterministic and does not estimate uncertainty
  from a learned model.
- Public and shadow results cannot guarantee performance on the organizer's 800
  private sessions.
- Recommendation explanations are not yet product-specific.

## Team contributions as of this baseline

- Team lead + dedicated Core Agent: architecture, state/override logic, lexical
  retrieval bridge, reranking, clarification policy, integration, gates, and
  first reproducible Demo.
- Liu Chunyi: assigned QA/evaluator/regression owner; independent review and
  accepted contributions must be recorded before the final submission.
- Cheng Xianyun: assigned experiment-analysis/demo/submission owner; accepted
  contributions must be recorded before the final submission.
- Wang Siwen: assigned retrieval/runtime-engineering owner; accepted
  contributions must be recorded before the final submission.

No work is attributed to a teammate until their reviewed commit is merged.
