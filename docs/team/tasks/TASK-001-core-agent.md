# TASK-001: offline core Agent scaffold

Owner: Team-lead dedicated automation Agent
Reviewer: Liu Chunyi
Timebox: 4 hours

## Outcome

Replace the monolithic starter implementation with a thin adapter plus a
modular offline core that preserves valid baseline recommendations, maintains
session state, handles explicit intent overrides, and can ask a non-repeated
clarification while still recommending products.

## Allowed paths

- `starter/agent.py`
- `solution/**` except `solution/retrieval/**`
- `tests/core/**`
- `docs/contracts/**`
- `docs/decisions/**`

## Acceptance criteria

- Official `Agent.reset/respond` signature is unchanged.
- `starter/agent.py` is only an adapter.
- State is isolated by session and reset is deterministic.
- Explicit corrections replace old slot values.
- A no-preference response does not create a constraint or repeat the question.
- Every response is schema-valid and returns current recommendations.
- No API credential or network is required.
- Existing official evaluator and data are unmodified.

## Proof commands

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py
python -m evaluator.local_evaluator --output reports/generated/core-agent.json
```

## Out of scope

- Dense/hybrid retrieval or generated indexes
- UI or demo video
- Editing evaluator/data/metric rules
- LLM-only behavior
- Public-target-specific tuning
