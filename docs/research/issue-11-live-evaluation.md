# Research: source-verified opt-in Jev evaluator (#11, second increment)

Inspected the merged offline scorer `scripts/semantic_evaluation.evaluate`, canonical `scripts.nl_benchmark_v2.load_benchmark/verify_source`, `src/tf_jev.jev.JevBackend`, `SemanticParser`, the frozen v2 BHSA JSON, existing `tests/test_jev_live.py`, and native pinned replay.

- The already merged scorer performs native TF result verification but has **no command that constructs a live model-backed parser**. The Jev adapter is available only under the optional `tf-jev[jev]` extra and needs a configured `JEV_API_KEY` (no key may be printed or written).
- The canonical benchmark is 109 cases in whole-family partitions; development has 52, heldout 57. Loading real BHSA full schema can take ~1 minute and multiple GB. Every model parse may make many bounded requests (default `max_calls=64`), so a default complete run is an unintended cost/latency exposure.
- `Benchmark.verify_source(directory)` compares all pinned TF source hashes and TF 13.1.0. It MUST happen before any Jev client creation, model call, report or corpus evaluation. The CLI uses the canonical benchmark by default; tests can exercise an injected synthetic verified tiny TF corpus, never as a measure of BHSA/model quality.
- The Jev adapter pins the actual resolved model to `jev-1.13.0`; it sanitizes SDK failures. `SemanticParser` requires **full coverage** and rejects selected-schema coverage. No backend should see gold, case family, evaluation partition, rationale or interpretation strings.
- For a financially safe manual run, require both explicit `--live` and `TF_JEV_LIVE=1` plus an explicit maximum number of cases; the report must disclose if only the prefix of a partition was evaluated. Unknown USD/token prices or missing SDK usage are NOT zero cost.
- A direct CLI should write atomic, compact, JSON-compatible **summary only**, never raw queries, prompts, corpus text or secrets. An early failure must not leave behind a stale misleading success file. No live test in normal CI.

This implementation **enables** measured Jev evaluation but cannot assert Jev accuracy without the actual API credential and pinned live run. Follow-up under #11: execute/review real development and held-out measurements, calibrate thresholds, record retrieval recall and compare alternative backend (#12).
