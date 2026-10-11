# BHSA NL ↔ native TF benchmark (seed v1)

Research dataset for [#10](https://github.com/alexsosn/tf-jev/issues/10), frozen 2026-10-11.
Corpus: [ETCBC/bhsa](https://github.com/ETCBC/bhsa) TF data version **2021**,
release v1.8.1, used with Text-Fabric 13.1.0.

The fixture contains **13 original English requests**: six supported native-query
gold examples with empirically recorded result-*tuple* counts, three ambiguous
requests and four unsupported requests. The original gold counts come from
`tests/conformance/test_tf_search_grammar_bhsa.py` run against real BHSA 2021.
The fixture has an immutable train/development/evaluation assignment.
No parser/model has been evaluated on these cases yet.

**This is an incomplete seed, not the full #10 acceptance dataset.** It does not
yet cover the breadth of high-cardinality feature-value resolution, morphological
values, scope ambiguity, and roughly 100 independently validated examples.
The future parser must not use `evaluation` cases for prompt examples, heuristic
construction, or threshold selection. Evaluation should remain sealed until #11.

## Reproduction

From a checkout with `pip install -e '.[dev,jev]'`:

```sh
python -m scripts.nl_benchmark
python -m scripts.nl_benchmark --corpus /path/to/ETCBC/bhsa/tf/2021
TF_JEV_BHSA_DIR=/path/to/ETCBC/bhsa/tf/2021 python -m pytest tests/test_nl_benchmark.py -q
```

The first command checks structural integrity without executing Text-Fabric.
The others require the local corpus; **nothing is downloaded**. The runner
checks the recorded SHA256 of `otype.tf`, then executes supported gold queries
through Text-Fabric's native search and checks strict diagnostics and full
row counts (with one-extra-row overflow detection).

**Scope of source pin:** `otype.tf` is digest-pinned as an early drift guard;
this does **not** authenticate all feature files or in-memory overrides.
Until a complete feature-manifest pin and real-corpus verification are added,
a passing check on its own is insufficient to certify corpus equivalence.
Native count assertions detect many, but not all, feature-level drifts.

`scripts.nl_benchmark.equivalent(api, gold, candidate)` is a lower-level
research helper for comparing **trusted compiler-produced** native queries.
It compares the full sorted tuple sets, not only result counts, and explicitly
fails on TF diagnostics or a row-count ceiling. Do not execute raw untrusted
model text through this interface.

## License and provenance

Underlying BHSA corpus data is [CC BY-NC 4.0](https://github.com/ETCBC/bhsa#license).
Attribution: Eep Talstra Centre for Bible and Computer, VU University Amsterdam,
[dataset DOI](https://doi.org/10.17026/dans-z6y-skyh).

No corpus text or per-node data is redistributed in this seed; it contains
original NL requests, native query syntax and documented aggregate counts.
Software in this repository remains MIT licensed.
