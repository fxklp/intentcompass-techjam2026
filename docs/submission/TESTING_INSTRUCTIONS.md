# Judge testing instructions

## Requirements

- Windows, macOS or Linux
- Python 3.12 or 3.13 with SQLite FTS5
- Network once for the official catalog; additionally once for optional pinned
  local semantic assets
- No API key, GPU or external database required

## Fast base-path test

From the repository root:

```text
python scripts/setup_data.py
python demo/run_demo.py
python -m evaluator.local_evaluator --output results.json
```

The demo should end with `First hit turn: 5 | Rank: 8`. The evaluator output
must contain 200 Public sessions and valid ordered catalog identifiers. It is a
released development evaluation, not the private score.

## Full local semantic path

```text
python -m venv .venv
# activate the environment, then:
python -m pip install -r requirements-semantic.txt
python scripts/setup_data.py
python scripts/build_semantic_index.py --download
python scripts/task306_evaluate.py --split public --semantic local --output results.json
python -m unittest tests.retrieval.test_task306_real_models
```

The build verifies pinned model revisions and binds the generated dense matrix
to the catalog checksum. Missing assets cause a safe lexical fallback; runtime
never downloads a model automatically.

## Full repository checks

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
```

Expected Public metrics for the frozen candidate are HR@10 `0.98`, MRR
`0.696861`, MTTC `3.755` and TechnicalScore `0.843958`. TechnicalScore is not
the contest total.

Do not place credentials in the repository. Optional API adapters use
`DASHSCOPE_API_KEY` or `DEEPSEEK_API_KEY`; they are not required for these tests.
