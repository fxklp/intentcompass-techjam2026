# IntentCompass — Track 4 Shopping Copilot

A CPU-only conversational shopping Agent for TikTok TechJam 2026. It maintains
replaceable preferences, searches a frozen catalog, asks structured clarification
questions and returns ranked product identifiers. No UI or transaction service.
The customer conversations are simulated, not real-user conversations.

## Start here: the frozen default

Use **Python 3.12 or 3.13 with SQLite FTS5**. No third-party Python package, GPU,
downloaded model, API key, paid service or external database is required.
On macOS use `python3` if `python` is unavailable. Run from this folder.

```text
python scripts/setup_data.py
python scripts/release_check.py
```

The first command downloads and checksum-verifies the official catalog (network
needed once). The second uses a fixed offline preset, ignores inherited experiment
settings in its own process, checks the Agent contract/reset, evaluates all 200
Public sessions with the unchanged evaluator, and runs the real demo.
It checks that no network connections are attempted during this verification.
Success ends with `RELEASE CHECK PASSED`. Full per-session `results.json` and
provenance go to a new `reports/generated/release-.../` directory.

In a released ZIP, `RELEASE-MANIFEST.json` records source commit and file hashes.
The checker rejects altered/missing payloads. The ZIP needs no Git executable;
catalog, credentials, model assets, caches and API ledger are excluded.
Verify its checksum against the team lead's handoff before extraction.

The preset is `integrated / baseline FTS / constraints / semantic off / network off`.
The checker does not modify the parent shell's environment or the algorithm.
Optional experiments in the source tree are **not active default capabilities**.

## Interface and direct recording

The official entry is `starter/agent.py:Agent`, delegating to `solution/`:

```python
from starter.agent import Agent

agent = Agent("data/catalog.jsonl")
try:
    agent.reset("example", {})
    result = agent.respond("example", "I'm looking for shoes.", 1, 10)
finally:
    agent.close()
```

Responses contain natural `message`, one `ask_attribute`, up to ten valid unique
`parent_asin` values, and zero prompt/completion tokens. The ten-turn bound and
session reset contract are preserved.

For direct recording in a fresh shell with no `INTENTCOMPASS_*` overrides:

```text
python demo/run_demo.py
python scripts/run_offline.py --output results.json
```

The real Public demo first hits after intent override on turn 5 at rank 8.
Only the harness knows the target; the Agent does not receive it.
Use a new results filename on subsequent runs to preserve previous evidence.
`run_offline.py` selects the frozen preset and forwards all arguments to the
unchanged `evaluator.local_evaluator`; it does not impose Public reference
scores. The underlying equivalent command is
`python -m evaluator.local_evaluator --output results.json` with that preset.
For the future final package, follow its released instructions and use its
unmodified evaluator with the frozen solution; do not substitute the Public
acceptance check for final evaluation or tune after seeing final labels.

## Reproduced Public results

| Metric | Frozen offline default |
| --- | ---: |
| Sessions | 200 |
| HitRate@10 | 0.910000 |
| MRR | 0.624024 |
| MTTC | 4.255000 |
| Efficiency | 0.674500 |
| TechnicalScore | 0.777107 |
| Default model tokens / API cost | 0 |

TechnicalScore is an input to Technical Execution, **not the contest total**.
The official weak starter's published HR/MRR/MTTC are .125/.068034/9.81.
Later experiments were compared with our strong .91 baseline, not that starter.
Recent field/dense/API experiments failed our all-scenario non-regression rule
and were not promoted. See [method and limitations](docs/release/METHOD.md).

## Current rules and capability boundary

The [current official submission rules](https://github.com/TechJam2026/techjam-conversational-search/blob/main/docs/submission_rules.md),
checked 2026-08-31, explicitly allow non-LLM methods. After the deadline, evaluate
the released final package with the unmodified official evaluator and the commit
frozen at the Devpost deadline. Retain results and environment details. Do not
change the Agent, prompts, indexes or configuration after that freeze.

The checked-in original `docs/submission_rules.md` in the full repository is
historical; its network-policy wording does not describe the current rules.
Offline operation is our choice, not an organizer mandate.

The broader [Track 4 statement](https://bytedance.larkoffice.com/wiki/GdYFwzWNLiREsSkuIjZcDznInWc)
also describes richer dense/multi-route retrieval, LLM ranking and orchestration.
Those are not all active in this default. See the [requirements audit](docs/release/REQUIREMENTS.md).
We do not claim full four-pillar coverage, guaranteed eligibility, private-set
accuracy, or a globally optimal Agent.

## Team contributions

- Fang Tianchen: initial end-to-end Agent, algorithm/architecture direction and
  final integration with AI coding assistance.
- Liu Chunyi: QA, cross-platform contract/CI work and independent reviews.
- Cheng Xianyun: reproduction analysis, evidence organization and demo storyboard;
  final video production remains a separate deliverable.
- Wang Siwen: isolated retrieval experiments, benchmarks and evidence-integrity
  fixes. Rejected candidates are not described as deployed improvements.

AI coding assistance supported implementation, tests and documentation; the team
remains responsible for correctness and explaining the work.

## Developer checks and packaging

These require the full Git checkout, not the compact released ZIP:

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python scripts/build_release.py --output artifacts/release/intentcompass.zip
```

The builder requires a clean committed tree and a new output path. One optional
ONNX smoke test can skip without model dependencies. Do not run old experiment
summary scripts for release acceptance: they pin historical source hashes.

## Data and remaining submission materials

The official kit supplies 50,000 Clothing/Shoes/Jewelry products and 200 Public
sessions derived from Amazon Reviews 2023. Only released Public labels are
packaged. Catalog files stay external and checksum-verified.
Preserve [data attribution](DATA_ATTRIBUTION.md) and respect upstream terms.

Devpost requires an English description, public repository with README and a
**public three-minute YouTube demo**. Passing technical checks does not complete
video production or submission. See [recording guidance](docs/release/VIDEO-HANDOFF.md).
These tools never upload a video or submit a project.
