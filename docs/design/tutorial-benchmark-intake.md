# Tutorial candidate intake design (#10)

API in `scripts/nl_candidates.py`: `load_candidates(path) -> CandidateCatalog`, `verify_candidate_source(directory, catalog) -> None`, `run_candidate(api, case, *, max_rows=500000) -> int`. Immutable records and exact JSON schema; no model calls or raw NL execution. Candidate `capability` is `in_scope` or `deferred`; only in-scope examples are replayed. Historical `reported_count` is stored but never asserted as BHSA 2021 truth.

The source manifest includes pinned Git blob hashes for corpus files used by candidate queries; verification is separate from existing benchmark gold to avoid altering #10's already frozen seed. The native runner uses the existing `tests.conformance.tf_harness.run_template` diagnostic cache and demands at most `max_rows` results with a one-extra-row limit. The CLI `python -m scripts.nl_candidates` validates the fixture; `--corpus /path/to/bhsa/tf/2021` authenticates the raw source files and replays in-scope cases against actual TF search; it prints observed counts plus a comparison field describing any disparity against notebook results and does **not** promote anything automatically.

The companion tests assert that no unversioned or 2017 count accidentally enters verified gold, including a fixture comparison over IDs. Held-out cases in the prior gold benchmark are intentionally unchanged. Promotion requires a separate issue/PR after 2021 corpus replay and adversarial review.

Research → design → RED tests → implementation → exact-head GitHub CI → independent code/data review → merge, without closing #10.
