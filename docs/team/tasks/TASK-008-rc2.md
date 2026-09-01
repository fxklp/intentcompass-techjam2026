# TASK-008 RC2 integration: qualified category ordering only

Owner: team lead / integration Agent, under the lead's local completion authority.
Base: accepted RC1 44ae159659e76b21ca63dbb9fcd1306b9d342d32, reproduced before
research. This checkout starts from exactly that source. RC1 and the research
branch are preserved. No push, merge, video upload or submission is authorized.

## Allowed paths

- This card; docs/team/TASK-008-RESULTS.md
- solution/category_order.py; solution/adaptive.py; solution/field_evidence.py
- tests/core/test_category_order.py; tests/core/test_release.py; tests/core/check_rc2.py
- scripts/release_check.py
- README.md; docs/release/METHOD.md; docs/release/VIDEO-HANDOFF.md;
  docs/release/REQUIREMENTS.md
- Ignored artifacts/** and reports/generated/**; unchanged copy of catalog.

The official evaluator, data, interface, dependencies, question policy, ranking
weights, retrieval queries and candidate counts remain unchanged. No network,
keys, training, new model/data, disk index, UI, or target-dependent logic.

## Scope

Prepare only the category_head policy frozen in research commit
799e590fd10eda9fd401544473c5e34cf6163ec2. It changes ordering within the same
Top10, not membership, clarification or stopping. Keep its bounded 512-entry
catalog-query cache and exact deterministic no-match behavior. Default on only
for integrated/baseline/offline constraints; explicit off remains a control.
Do not copy the rejected research policies or experimental SQL path into RC2.
Also apply the independently reproduced field-reader eviction correctness fix.

Preparation is not acceptance: do not freeze/package RC2 until the research
candidate passes the predeclared 800-target confirmation. Then require RC2
Public per-session and aggregate equality with the frozen candidate, plus the
same Shadow/800 aggregate results. No retuning on validation outputs.
Update release-specific assertions and current documentation to measured RC2
values, while keeping strict checks and the official scoring untouched.

## Proof and handoff

python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python -m tests.core.check_rc2 --split public --output reports/generated/rc2-public.json
python -m tests.core.check_rc2 --split shadow --output reports/generated/rc2-shadow.json
python -m tests.core.check_rc2 --split confirmation --output reports/generated/rc2-confirmation.json
git diff --check
git status --short

Commit a clean, allowlisted local revision, build a NEW intentcompass-rc2.zip,
extract into a NEW smoke directory, and run its strict release checker without
network or credentials. Record ZIP/results SHA256 and source commit. Existing
RC1 archives/directories must not be overwritten. Cross-machine signoff and
public publication remain separate actions through the team lead.

## Completed qualification before packaging

The research candidate passed its 800-target confirmation without any overall
or scenario regression. Extracted runtime 8c61d545070507f25966e6e2d8ad82683464768c
then matched frozen Public per-session results and all three sets' metrics.
158 tests and the full team gate passed. Final-source speed/memory gates passed:
median p95 +3.56% (within the predeclared 5%), maximum RSS decreased. This is not
claimed as a speed improvement. Only documentation was changed afterward.
