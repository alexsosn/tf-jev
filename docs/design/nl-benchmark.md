# NL benchmark seed design (#10)

## Data and limits

`benchmarks/nl-tf-v1/bhsa-2021.json` contains a versioned catalogue: corpus, data version, a SHA256 pin, and cases. Every case has id, split (train/development/evaluation), status (supported/ambiguous/unsupported), difficulty, English request, gold query or null, expected result tuple cardinality or null, and rationale. Strict loading rejects unknown fields, duplicate IDs, booleans as counts, blank queries and gold queries on abstention cases. It never interprets or executes request prose.

`scripts/nl_benchmark.py` exposes `load_catalog`, `verify_source`, `check_gold`, and `equivalent` for the research harness. `check_gold` executes each supported native TF query with a limit one above its expected count and requires exact cardinality and zero TF diagnostics. `equivalent` compares complete sorted native result tuples (including atom columns), bounding each execution by `max_rows+1`; results over the bound produce explicit failure, not a success/false equivalence. The runner uses the existing diagnostic-aware real TF `run_template` test harness and does not introduce a second search engine.

`python -m scripts.nl_benchmark --corpus /path/to/bhsa/tf/2021` verifies pinned source and gold queries locally. Without `--corpus`, it validates the catalogue only. Model inference is intentionally out of scope.

## RED → GREEN → review

Write tests against a nonexistent `scripts.nl_benchmark` module and run CI to observe RED. Implement and run Ruff, mypy and pytest in CI (3.11, 3.12, 3.13), plus native tiny-corpus tests. If BHSA 2021 is unavailable in this execution environment, do not claim opt-in corpus validation; historical BHSA counts remain separately identified as earlier evidence. Finally review independently for query-projection mismatch, truncation, incorrect abstention classification, split leakage, and corpus-version drift.

This PR is a **partial increment** of #10, not closure. Expand the dataset to diverse, independently validated held-out cases before #9; do not optimize prompts on evaluation examples.
