# BHSA NL ↔ native TF benchmark (historical seed v1)

Superseded for parser/evaluation work by the complete [v2 benchmark](../nl-tf-v2/README.md).
This fixture and its original evaluation split remain unchanged as provenance evidence.

Research dataset for [#10](https://github.com/alexsosn/tf-jev/issues/10), originally seeded and first expanded on 2026-10-11.
Corpus: [ETCBC/bhsa](https://github.com/ETCBC/bhsa) TF data version **2021**,
release v1.8.1, used with Text-Fabric 13.1.0.

The fixture contains **27 English requests**: twenty supported native-query gold
examples with observed result-*tuple* counts, three ambiguous requests and four
unsupported requests. Six original counts come from
`tests/conformance/test_tf_search_grammar_bhsa.py`; fourteen additional queries originate
from official ETCBC search tutorial cells and were rerun against pinned BHSA 2021
in [the native replay workflow](../../.github/workflows/bhsa-replay.yml). Their
hand-adjudicated typed IR witnesses in `scripts/bhsa_gold_ir.py` must compile to
queries with **identical native result tuples**, not just equal counts.
The original evaluation partition is unchanged; new cases are train/development only.
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
The local commands do not download any corpus. The dedicated GitHub Actions replay
job uses an immutable, sparsely checked-out upstream corpus commit. Validation checks
the SHA256 of `otype.tf` and Git blob hashes of all **sixteen** referenced features
and structural source files, then executes supported gold queries
through Text-Fabric's native search and checks strict diagnostics and full
row counts (with one-extra-row overflow detection).

**Scope of source pin:** The fixture now authenticates the on-disk `otype.tf`,
`oslots.tf`, `sp.tf`, `gn.tf`, `nu.tf`, `function.tf`, `mother.tf`,
`book.tf`, `qere.tf`, `dist.tf`, `typ.tf`, `vs.tf`, `vt.tf`, `ps.tf`, `lex.tf`, and `rela.tf` against the
upstream [BHSA 2021 tree](https://github.com/ETCBC/bhsa/tree/master/tf/2021),
using Git blob SHA-1 and an additional SHA256 for `otype.tf`. Other feature
files, overlays, and in-memory TF changes are not authenticated. Runtime
counts guard against semantic drift within the tested gold queries.

`scripts.nl_benchmark.equivalent(api, gold, candidate)` is a lower-level
research helper for comparing **trusted compiler-produced** native queries.
It compares the full sorted tuple sets, not only result counts, and explicitly
fails on TF diagnostics or a row-count ceiling. Do not execute raw untrusted
model text through this interface.

The fourteen added gold requests were adapted and independently reviewed from the
[official notebook candidates](tutorial-candidates.md), with full native tuple
identity checked on the pinned corpus. All fourteen replayed in-scope tutorial queries now have native gold pairs; the remaining four deferred-grammar examples are discovery/abstention candidates. No natural-language parser has
been evaluated on the gold pairs.

## License and provenance

Underlying BHSA corpus data is [CC BY-NC 4.0](https://github.com/ETCBC/bhsa#license).
Attribution: Eep Talstra Centre for Bible and Computer, VU University Amsterdam,
[dataset DOI](https://doi.org/10.17026/dans-z6y-skyh).

No corpus text or per-node data is redistributed in this seed; it contains
original NL requests, native query syntax and documented aggregate counts.
Software in this repository remains MIT licensed.
