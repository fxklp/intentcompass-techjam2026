# First runnable demo evidence

Status: accepted locally on 2026-08-29.

## One-command demo

```bash
python demo/run_demo.py
```

Expected deterministic result for `public_0072`:

- scenario: Intent Override;
- correction arrives on turn 3;
- old value `Department: womens` is removed from active state;
- new value `Faux Fur` is present in active state;
- target is rank 1 after the correction.

## Reproduction gates

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
```

Accepted local results:

- tests: 15/15 passed with no `ResourceWarning`;
- public sessions: 200;
- HitRate@10: 0.91;
- MRR: 0.624024;
- recommended TechnicalScore: 0.777107;
- every scenario HitRate@10: at least 0.766667;
- reported token use: 0.

The score above comes from the unchanged official local evaluator. Generated
JSON remains ignored; reviewers must reproduce it from the commands above.

## Fresh-checkout proof

At commit `6175dfe`, an independent detached worktree containing no local
catalog successfully ran, in order:

1. `python scripts/setup_data.py` against the organizer release;
2. `python demo/run_demo.py`;
3. all tests present at that commit;
4. the quick team gate.

The temporary worktree was removed after verification. This proves that the
demo does not depend on the commander's existing checkout or a teammate copying
an untracked catalog by hand.

The subsequent lifecycle gate adds deterministic, idempotent cleanup of the
in-memory SQLite index. A full 200-session re-evaluation after that change kept
all metrics identical.
