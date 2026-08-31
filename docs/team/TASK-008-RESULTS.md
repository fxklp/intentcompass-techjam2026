# TASK-008: research results and RC2 decision

## Decision

Promote only stable **category ordering within the original Top10**. It raises
MRR on Public, original Shadow and the predeclared 800-session confirmation,
without changing HR or MTTC in any of the four scenarios. It passed three
alternating speed/memory comparisons against the actual accepted RC1 checkout.
This is a real precision gain, NOT simultaneous improvement of all three metrics,
an official hidden-set result, a contest total, or proof of global optimality.

RC1: `44ae159659e76b21ca63dbb9fcd1306b9d342d32`.
Frozen research candidates: `799e590fd10eda9fd401544473c5e34cf6163ec2`.
Extracted RC2 runtime: `8c61d545070507f25966e6e2d8ad82683464768c`.
The research branch keeps the negative experiments; RC2 starts separately from
RC1 and adds a 27-line category module, controller wiring, and the cache fix.
No rejected research-policy module or experimental SQL was copied into RC2.

## Scope and methods

Live official rules were checked before coding: static text/metadata catalog,
in-memory lightweight execution, at most ten turns, original Agent contract and
unchanged evaluator. Current organizer rules permit a non-LLM approach. No UI,
base-model training, multimodality, external DB, new dataset/model/dependency,
API calls, keys, pushes, merges or submissions were used in this round.

Research included [Amazon Reviews 2023/BLaIR](https://arxiv.org/html/2403.03952v2),
[Amazon ESCI](https://github.com/amazon-science/esci-data),
[KDD 2022 author solution](https://amazonkddcup.github.io/papers/8408.pdf),
[TFKD](https://amazonkddcup.github.io/papers/8610.pdf),
[retrieve/rerank guidance](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html),
[BEIR](https://github.com/beir-cellar/beir),
[Vespa domain-transfer discussion](https://blog.vespa.ai/improving-zero-shot-ranking-with-vespa/),
[rank fusion](https://blog.vespa.ai/solr-vs-vespa/),
[SQLite FTS5](https://www.sqlite.org/fts5.html),
[SQLite query optimization](https://www.sqlite.org/optoverview.html), and
[mixed-initiative clarification](https://www.microsoft.com/en-us/research/publication/analysing-mixed-initiatives-and-search-strategies-during-conversational-search/).

Applicable ideas were field/category relevance, phrase evidence, separating
recall from ranking, complementary-route fusion, corpus IDF, and question utility.
Large fine-tuned ensembles and external serving clusters were not imported.
All new code is original. These papers' datasets, labels and scores are not
substitutes for this competition's exact-ASIN multi-turn benchmark.

## Public development: all 17 variants, including controls

Four structural batches were declared before their results; no ASIN/sample rules
or weight grid. Public is repeatedly used development, not a holdout. The table
shows each variant's latest recorded Public result; early routes are rejected
development probes, not accepted final implementations. All raw batches remain.

| Variant | HR | MRR | MTTC | TechnicalScore | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| RC1 control | .910 | .624024 | 4.255 | .777107 | Reference |
| category_head | .910 | .648734 | 4.255 | .784520 | Qualified |
| category_pool | .920 | .637990 | 4.090 | .789597 | Later fails Shadow |
| phrase_head | .910 | .668748 | 4.255 | .790524 | Later fails Shadow |
| idf_head | .910 | .629012 | 4.255 | .778604 | Buying MRR down |
| phrase_pool | .925 | .636476 | 3.960 | .794243 | Later fails Shadow |
| conjunction_route | .940 | .637605 | 3.835 | .804581 | Boundary turns / Buying MRR worse |
| rrf_route | .940 | .633540 | 3.735 | .805362 | Buying MRR down |
| coverage_question | .920 | .634712 | 4.630 | .777814 | Turns and scenario MRR worse |
| category_phrase | .920 | .658185 | 4.090 | .795655 | Later fails Shadow |
| rrf_category | .940 | .630288 | 3.730 | .804486 | Buying MRR down |
| conjunction_category | .940 | .633639 | 3.830 | .803492 | Boundary turns / Buying MRR worse |
| category_route | .900 | .647153 | 4.290 | .778346 | HR / turns worse |
| category_route_phrase | .900 | .667153 | 4.290 | .784346 | Same membership regression |
| fast_rank | .910 | .624024 | 4.255 | .777107 | Same answers, much slower |
| cache_only | .910 | .624024 | 4.255 | .777107 | Equality/performance control |
| dominance_pool | .915 | .617440 | 4.110 | .780532 | Overall / scenario MRR down |
| category_dominance | .925 | .635976 | 3.960 | .794093 | Later fails Shadow |

## Cache correctness and performance negatives

Batch-two phrase_pool disagreed with batch one (MTTC 3.99 versus 3.96).
Tests reproduced both an empty-field bug in the old field reader and a KeyError
in the new normalization cache: inserting a miss could evict another field still
needed in the same request. Snapshotting the full request before eviction fixes
both. Batch two is not a reliable phrase-pool quality result. Corrected runs
recover 3.96, with cold/warm evidence and eviction regression tests.
The optional old field reader's fix also goes into RC2; its inactive status in
the default means that fix itself is not credited for the MRR gain.

ORDER BY rank with identical BM25 weights exactly preserved all Public sessions,
but p95 rose to about 112.84 ms versus the early 70.97 ms control; it is rejected.
A deferred-content SQL scratch probe matched eight label-free queries and had
means 23.33 versus 23.97 ms over 24 calls. That small exploratory difference
was not established as a whole-Agent win and was not integrated. The retained
512-entry cache stores catalog-query results only, not answers or profiles.

## Frozen Shadow selection, no retuning

All six finalists were frozen before these outputs. None was changed using
Shadow records; only aggregate results were inspected. The original Shadow was
used in earlier project work, so it is not a pristine independent dataset.

| Variant | HR | MRR | MTTC | Gate failure |
| --- | ---: | ---: | ---: | --- |
| RC1 | .895 | .630488 | 3.805 | Reference |
| category_phrase | .905 | .643744 | 3.615 | Browsing / Override MRR |
| phrase_pool | .910 | .635375 | 3.520 | Boundary / Browsing / Override MRR |
| category_dominance | .905 | .634792 | 3.555 | Boundary / Browsing / Override MRR |
| phrase_head | .895 | .667913 | 3.805 | Override MRR .586984 -> .586521 |
| category_pool | .905 | .628280 | 3.615 | Overall / Browsing / Override MRR |
| category_head | .895 | .656149 | 3.805 | None |

The small .000463 phrase-head Override regression is not rounded away and the
tolerance stays 1e-6. Better overall scores do not overrule scenario failures.

## Paired final evidence

| Set | N | RC1 MRR | category_head MRR | HR, both | MTTC, both | RC1 score | New score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Public | 200 | .624024 | .648734 | .910 | 4.255 | .777107 | .784520 |
| Original Shadow | 200 | .630488 | .656149 | .895 | 3.805 | .780546 | .788245 |
| Confirmation | 800 | .658917 | .689676 | .93375 | 3.52875 | .813975 | .823203 |

Every overall AND scenario HR/MRR/MTTC gate passes. Confirmation's scenario MRR:
Boundary .613700 -> .627530; Browsing .693700 -> .713806;
Buying .648904 -> .693415; Override .607937 -> .636075. HR and turns remain equal.

Confirmation seed: `intentcompass-task008-final-20260831`; 800 unique targets,
excluding Public and original Shadow; scenario counts 320/320/120/40.
Target-list SHA256: `55133511016044afa1da26a35ef1e1fd6696df49617219c7f3e83fa09d6d0e12`.
Only aggregate confirmation metrics are exported. It is the same simulator and
catalog, not the official private set, and not guaranteed disjoint from every
older synthetic experiment. Six-candidate selection also limits inference.

Three alternating fresh-process speed pairs, Windows/Python 3.13.9, CPU mask 1:

| Measurement | Actual RC1 | Frozen category_head |
| --- | ---: | ---: |
| p95 round 1 ms | 73.2701 | 75.6954 |
| p95 round 2 ms | 76.8675 | 75.0890 |
| p95 round 3 ms | 76.6319 | 74.3092 |
| Median p95 ms | 76.6319 | 75.0890 |
| Max process peak bytes | 455663616 | 455176192 |
| Median initialization seconds | 3.248207 | 3.283451 |

The +5% p95 and +16MiB RSS gates pass. No substantial acceleration is claimed;
initialization is slightly longer. Only the benchmark children were pinned,
not the user's host. Evaluation-process RSS includes both harness and Agent.

## Integrity and reproduction

Research: 165 tests, 164 passed / one optional-model skip; full team gate passed.
All production evaluations blocked socket connections and reported zero attempts
and zero model tokens. Official catalog, Public data and evaluator hashes stayed
fixed. No API budget was consumed or keys read. RC1 stayed clean and untouched.

Raw research JSONs are under the research checkout's ignored reports/generated/;
47 TASK-008 JSON artifacts were retained through final confirmation. They record
source/data hashes, source stability, environment, commit and dirty state.
Development snapshots are explicitly dirty; frozen validations are clean.
Results are append-only/new filenames, including negative and cache-invalid runs.

Key frozen candidate evidence SHA256:

- Public, task008-b4-category_head-public.json:
  `6e1e4db874d2ca70db0c4963e8dd15d151131c89ca744922257f66b2bec17f51`
- Shadow, task008-frozen-category_head-shadow.json:
  `3af647437a6521cdacecfb0f25d0f12983bef17506b2517bfa402b9bcce0412a`
- Confirmation, task008-final-category_head-confirmation.json:
  `69ea02d3d7cf2a7ea1d999a1ec64af651f4826e2a07ba6c3d3cccccb759f4671`

Research reproduction: python -m tests.core.check_research --variant category_head
--split public --output reports/generated/NEW-proof.json. For RC2 use
tests.core.check_rc2 and its --expected-report option. The acceptance runner
checks the extracted module against frozen Public sessions and Shadow/800
aggregates; it does not alter any score or target. See the RC2 task card for
full gate, clean commit, new ZIP and extracted-package smoke commands.

## Stopping boundary and remaining work

No tested further method improved HR/MTTC without lowering another protected
metric. Stop this search without loosening the gate or tuning on confirmation.
This is a finite, evidence-based stopping decision, not proof that all possible
methods are exhausted. Unrestricted language, exact-target lexical recall,
question optimization, personalization and official private evaluation remain
limitations. Candidate membership staying unchanged also means wrong-category
items can still remain when the original Top10 contains them.

RC2 at 8c61d545070507f25966e6e2d8ad82683464768c passed exact Public per-session
and aggregate equivalence, plus identical Shadow and 800-confirmation aggregate
results. Its 158 tests passed (157 executed, one optional-model skip), and its
full team gate passed. Final-source speed and new ZIP smoke are recorded in the
handoff rather than presumed from these research results. Old RC1 remains
recoverable. Liu/Cheng cross-machine reproduction and a video using the SAME
new release are separate lead-mediated actions; no work is assigned to Wang.

## Final extracted RC2 audit

Runtime commit: 8c61d545070507f25966e6e2d8ad82683464768c. Public per-session
results and all metrics equal the frozen category_head result. Shadow and the
800-confirmation aggregates also match exactly. Each proof's source inventory
was unchanged and its worktree clean. 158 tests (157 pass / 1 optional skip),
TEAM GATE PASSED, and a byte comparison of official data/evaluator/contracts
against RC1 all passed. The official scoring and benchmark were not modified.

Final-source three alternating speed pairs, same harness/CPU mask as before:

| Measurement | Actual RC1 | Extracted RC2 |
| --- | ---: | ---: |
| p95 round 1 ms | 81.0937 | 84.4104 |
| p95 round 2 ms | 86.6105 | 84.1666 |
| p95 round 3 ms | 81.2731 | 79.7730 |
| Median p95 ms | 81.2731 | 84.1666 |
| Max process peak bytes | 456077312 | 455266304 |
| Median initialization seconds | 3.348535 | 3.333650 |

Median p95 is +3.56%, within the PREDECLARED +5% gate. Do not hide that increase
or claim acceleration based on the earlier candidate timings. Observed ranges
overlap; host variability limits interpretation. Memory gate passes. Final-source
reports are rc2-speed-baseline-{1,2,3}.json and rc2-speed-rc2-{1,2,3}.json.

The final release documentation records these measurements; subsequent changes
are documentation only. ZIP hash and extracted-package acceptance are recorded
in the generated handoff after building a clean, committed new archive. No old
RC1 file or archive is replaced.
