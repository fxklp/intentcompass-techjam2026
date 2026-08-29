# First runnable demo evidence

Status: accepted locally on 2026-08-29.

## One-command demo

```bash
python demo/run_demo.py
```

Expected deterministic result for `public_0183`:

- scenario: Intent Override;
- turns 1-3: target rank displays "Not scored until intent override";
- override arrives on turn 4: old values `Hand Wash Only` + `100% Polyester`
  are removed from active state, new value `polyester` is present;
- turn 4: target not in Top 10 (override just applied);
- turn 5: target enters Top 10 at rank 8;
- first hit turn: 5 — consistent with per-turn display (no contradiction).

## Reproduction gates

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
```

Accepted local results:

- tests: 28/28 passed with no `ResourceWarning`;
- public sessions: 200;
- HitRate@10: 0.91;
- MRR: 0.624024;
- recommended TechnicalScore: 0.777107;
- every scenario HitRate@10: at least 0.766667;
- reported token use: 0.

The score above comes from the unchanged official local evaluator. Generated
JSON remains ignored; reviewers must reproduce it from the commands above.

## Fresh-checkout proof

Historical baseline (`6175dfe`): an independent detached worktree ran
`setup_data.py`, `run_demo.py`, all tests, and the quick team gate. That
commit used the previous sample (`public_0072`) which had a display
contradiction fixed in TASK-202.

Current proof: at the TASK-202 commit, the same sequence was re-run with
`public_0183`. The demo displays "Not scored until intent override" before the
override and reports `First hit turn: 5 | Rank: 8` after — consistent with
per-turn output.

The subsequent lifecycle gate adds deterministic, idempotent cleanup of the
in-memory SQLite index. A full 200-session re-evaluation after that change kept
all metrics identical.

The current full gate also fails automatically if overall HitRate@10 falls
below 0.75, TechnicalScore below 0.60, or any scenario HitRate@10 below 0.60.

`python scripts/shadow_evaluator.py` separately evaluates 200 deterministic
catalog targets with zero public-target overlap and the official scenario mix.
The accepted reproducible result is HitRate@10 0.895 and TechnicalScore
0.780546; the shadow command fails below HitRate@10 0.70.
