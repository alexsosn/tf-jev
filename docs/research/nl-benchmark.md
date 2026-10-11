# NL ↔ TF benchmark: first pinned seed (#10)

Date: 2026-10-11. Source authority: the repository's real Text-Fabric 13.1.0 BHSA 2021 conformance evidence (`tests/conformance/test_tf_search_grammar_bhsa.py`, `tests/test_compiler.py`), corpus source hashes from `benchmarks/retrieval-v1/bhsa-2021.json`, and the native diagnostics-aware `run_template` fixture. The BHSA dataset is ETCBC/bhsa release v1.8.1 (data version 2021).

## Observed, rather than inferred

The existing opt-in real-BHSA tests establish the following exact native result counts: `word sp=verb` 73,710; `word sp=verb gn=f nu=pl` 725; `clause\n  word sp=verb` 73,710 *result tuples* (not necessarily distinct clauses); `word sp=verb\n<: word sp=subs` 15,336; `a:clause\nb:clause\na -mother> b` 13,917; `clause\n/without/\n  phrase function=Pred\n/-/` 31,061. Counts come from real corpus execution already recorded, and are to be rechecked opt-in on every local corpus run. Do not infer cardinality from English descriptions.

Text-Fabric silently truncates when given an explicit search limit, and an invalid quantifier body can otherwise fail open. `run_template` retains the diagnostic cache and checks quantifier errors. A gold runner must request one more row than the recorded cardinality so an unexpectedly larger result cannot appear to pass via limit truncation. Native result tuples are ordered by query atom projection: comparing only counts is insufficient for semantic equivalence.

## Dataset decisions

- Store natural-language requests in a separate, versioned JSON fixture, independent of retrieval-v1 and any future prompts.
- Labels are `supported`, `ambiguous`, `unsupported`. An abstention case has no gold query; a supported case must have a gold native query, an empirically attested exact cardinality and a rationale.
- Freeze train/development/evaluation splits in the fixture before #9. The evaluation split must not be used to select parser prompts, rules or thresholds. The current seed is **not** a quality measurement of Jev or any semantic parser.
- Start with six verified native templates plus abstention probes. This is a deliberately partial foundation for #10: semantic diversity, especially literal-value retrieval, and independent held-out expansion toward ~100 examples remain open.
- Validate the actual `otype.tf` SHA256 before running the native BHSA cases. Check strict JSON schema fields, unique case identifiers and separation of gold from abstention labels. No data download or remote model calls.
- An evaluation helper may compare a *compiled* candidate's full native result tuples with gold, but cannot accept count parity or truncated results as equivalence. Its output is not yet a #11 quality report.

## Security, licensing and scope

The corpus is CC BY-NC 4.0; no BHSA excerpts or copied node content are added here. Annotation names and attested aggregate cardinalities are evidence, not a redistribution of corpus text. The benchmark contains original English queries and native TF syntax. The runner never sends corpus content to a model. The known `otype.tf` digest from retrieval-v1 is used to reject corpus drift.

Next step: add deterministic RED tests for malformed catalogues, silent-limit overflow, native semantic equality versus equal counts, and SHA mismatch; then implement the smallest evaluator and confirm all CI checks. Native BHSA gold verification must be run separately wherever BHSA 2021 is present; CI deliberately does not fetch the corpus.
