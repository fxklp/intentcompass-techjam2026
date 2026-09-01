# TASK-013: dataset-specific research, 2026-08-31

## Source of truth and applicability

The live [official specification](https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/docs/competition_specification.md)
and [data README](https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/data/README.md)
identify a frozen 50,000-item Clothing/Shoes/Jewelry subset of Amazon Reviews
2023 and an interactive simulator. Exact purchased parent_asin is the target;
similar products are not equivalent. Keep official data and evaluation intact.
The live model policy permits non-LLM solutions and external APIs; mandatory
offline fallback in this repository is a stricter team rule, not a claim about
the latest official policy. This task follows the user's offline-first scope.

The [dataset authors' documentation](https://amazon-reviews-2023.github.io/)
explains that parent_asin often groups size/color/style variants. Metadata price
is a crawl-time value. Hence missing or conflicting attributes are not reliable
proof of exclusion: retain soft constraints and avoid aggressive filtering.
Runtime receives the frozen catalog and observed dialogue, not original review
histories or unrestricted user IDs. No extra Amazon data was downloaded.

## Papers and author-maintained implementations

### BLaIR / Amazon Reviews 2023: directly related

[Paper v2](https://arxiv.org/html/2403.03952v2),
[original author code](https://github.com/hyp1231/AmazonReviews2023),
[BLaIR-Bench](https://github.com/hyp1231/BLaIR-Bench).
The April 2026 v2 benchmarks semantic encoders; it should not be confused with
the original 2024 BLaIR model presentation. Section 5.3 finds that adding
descriptions to titles does not consistently improve results. Section 5.2 does
not establish that generic embedding-leaderboard rank predicts product search.
Product search, collaborative filtering and sequential recommendation use
different information and objectives; their results are not this contest's
interactive first-hit MRR/MTTC. Inference for our system: verify useful field
evidence and benchmark task-specific gains rather than replace lexical search
just because an encoder is larger. Pretrained inference remains a possible
later experiment, not something this research proves unnecessary or illegal.

### Stage-aware query decomposition: adjacent task, useful mechanism

[June 2026 paper](https://arxiv.org/html/2606.08577v1),
[author implementation](https://github.com/EIT-NLP/Query-Decompose).
On MultiConIR/SSRB, decomposing queries during retrieval can weaken conjunctions;
checking decomposed conditions during reranking is more promising. Those are
not Amazon Reviews 2023 or this contest's evaluator. Transferable hypothesis:
keep our successful whole-query candidate pool and verify explicit conditions
only during precision ordering. Our lexical test is not a reproduction of the
paper's Qwen/BGE neural rerankers and does not inherit their reported gains.

### Hint-Augmented Re-ranking: adjacent product-search task

[Amazon-authored paper](https://aclanthology.org/2025.ijcnlp-short.19.pdf).
It derives attribute hints from vague/superlative queries and uses them for
efficient ranking. Its query dataset and models differ from ours. We already
have explicit conversation slots, so test those observed requirements without
inventing attributes from words such as 'best', or importing an LLM component.

### Catalog-pattern attribute prediction: adjacent catalog task

[Amazon publication](https://www.amazon.science/publications/leveraging-product-catalog-patterns-for-multilingual-e-commerce-product-attribute-prediction),
[paper](https://aclanthology.org/2025.emnlp-industry.18.pdf).
Catalog-pattern retrieval can supply attribute evidence, but its internal
catalog/click features and attribute-generation task do not match our frozen
input. Use evidence conservatively; do not rewrite official metadata with
inferred attributes or assume unavailable behavioral features exist.

## Community repositories and technical blogs

### Bag-of-Documents: directly related metadata, different evaluation

[Author's project and experiment diary](https://github.com/dtunkelang/bag-of-documents).
It uses Amazon Reviews 2023 metadata but evaluates on ESCI judgments. The
author reports strong lexical baselines, harmful dense/lexical fusion for some
entity queries, and unsuccessful expansion/distillation experiments. It also
describes useful neural reranking with higher latency. These are author-reported
findings, with repeated test-driven comparisons, not independent evidence for
our hidden-set performance. Inference: retain precise lexical candidates,
prefer a bounded rerank, and record negative results rather than assume more
retrieval branches must help. ESCI relevance grades are not exact parent-ID
conversion. The linked Medium posts were not fully accessible; this synthesis
uses the public repository, not a claimed full reading of paywalled posts.

### Two-stage Amazon Reviews recommender: unsuitable user features

[Community implementation](https://github.com/wytili/amazon-reviews-two-stage-recsys).
Two-tower retrieval plus a ranker on Video Games demonstrates a conventional
separation of stages. It requires user/item history and has different metrics.
It is not a drop-in shopping-dialogue solution and was not adopted.

### Dataset tutorials: distinguish engineering from retrieval evidence

[Databricks employee tutorial](https://community.databricks.com/t5/lakebase-blogs/how-to-perform-semantic-search-in-databricks-lakebase/ba-p/139846)
uses Amazon Reviews 2023 All Beauty metadata with PostgreSQL/pgvector. This is
useful operational explanation, not an exact-item multi-turn quality result;
an external Lakebase service is not appropriate for our in-memory design.

[SkyPilot technical blog](https://skypilot.ai/blog/large-scale-embedding)
embeds Amazon Books reviews using large-scale GPU infrastructure. Its throughput
claims do not establish better HR/MRR/MTTC. No cloud infrastructure or spending
is justified by that tutorial for this experiment.

## Decision before experiments

Test exactly two membership-preserving pure-ranking policies: extract the prior
safe full-phrase conjunction, and prevent that conjunction from accidentally
matching across primary-field boundaries. Keep questions, constraints, retrieval
pool, terminal recovery and official evaluator unchanged. Neither candidate
hard-filters missing attributes or treats a semantic substitute as a hit.

TASK-012's combined ranking/question policy failed fresh Buying MTTC despite
better aggregate scores. Its pure ranking policy has not been independently
confirmed. This is a new predeclared round, not a reinterpretation of that
failure. Select before two new disjoint confirmations; preserve the old default
on any protected regression. Larger semantic models remain an unproven possible
avenue; we cannot infer a theoretical ceiling from these finite experiments.

All runtime implementation is original local Python reusing existing project
helpers. No third-party source/model copied, new dependency, asset license,
external corpus, API call or fee. Reproduction and exact thresholds are fixed
in `tasks/TASK-013-precision-order.md`; result claims belong in the results
report and generated immutable JSON, not in this research rationale.
