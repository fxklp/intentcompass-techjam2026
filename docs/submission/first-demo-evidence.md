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

- tests: 12/12 passed;
- public sessions: 200;
- HitRate@10: 0.91;
- MRR: 0.624024;
- recommended TechnicalScore: 0.777107;
- every scenario HitRate@10: at least 0.766667;
- reported token use: 0.

The score above comes from the unchanged official local evaluator. Generated
JSON remains ignored; reviewers must reproduce it from the commands above.
