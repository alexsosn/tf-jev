# nl-tf-v2: BHSA 2021 NL ↔ native TF

This is the canonical frozen semantic benchmark created before the parser (#9), separately
from the literal candidate-retrieval benchmark. Gold queries are authored native
TF templates, not model output. The artifact pins Text-Fabric 13.1.0 and every
source feature used by the gold through SHA256 hashes.

The 109 cases comprise 86 supported, 11 ambiguous and 12 unsupported requests.
Development has 44 supported + 8 abstentions (52 total); heldout has 42 supported
+ 15 abstentions (57 total). `nl-tf-v1` is retained unchanged as historical seed
and tutorial provenance, and is superseded for #9/#11. All five original v1
evaluation requests remain held out in v2. Never use v1 development data to tune
on equivalent v2 heldout families. The dedicated native replay CI verifies both
v2 partitions against its immutable BHSA checkout.

## Running

From the checkout with Text-Fabric 13.1.0 installed:

```sh
python -m scripts.nl_benchmark_v2 /path/to/bhsa/tf/2021
python -m scripts.nl_benchmark_v2 /path/to/bhsa/tf/2021 --partition heldout
TF_JEV_BHSA_DIR=/path/to/bhsa/tf/2021 python -m pytest tests/test_nl_benchmark_v2.py
```

The default is the development partition. The runner executes all supported gold
in the chosen partition without a model or network, checks frozen counts and
signatures, and reports supported/ambiguous/unsupported classes separately.
Abstention cases are labels for future parser evaluation, not native searches.
A failed native query or result cap is an error, never a correct empty result.

## Return semantics and equivalence

`gold.projection` indexes native result columns (zero-based), in the requested
output order. Deduplicate projected tuples before scoring. A clause containing
three verbs is one returned clause when the request asks for distinct clauses.
The signature is SHA256 over UTF-8 canonical JSON with sorted keys and no spaces:
`{"rows":[...sorted distinct tuples...],"width":output_column_count}`.
Empty results still encode their output width. Role order matters for pairs.
A predicted query can use different atom order/syntax if its explicitly selected
output projection yields the same count and signature. Do not compare unprojected
native witness tuples, and do not infer projection merely to maximize a score.
Exact query-string match remains a separate metric for #11.

## Partition and use policy

Split entire named semantic families; IDs and requests are unique. Development
cases may inform prompts, examples and debugging. Held-out requests, gold and
rationales are evaluation-only: do not import them into parser prompts, heuristic
rules, demonstrations or training. Corpus schema remains available to the parser.
The family split tests unseen request structures/annotation combinations, not
complete lexical disjointness. The public holdout is a procedural constraint.
Record every evaluation and any tuning informed by held-out results; such tuning
requires a new benchmark/holdout version before claiming unbiased generalization.

Supported cases deliberately target the existing IR subset, with annotation-
explicit language. Empty and missing annotation values differ. Literal lexeme,
pointed-form and gloss matching does not demonstrate translation quality.
Ambiguous cases have at least two defensible interpretations. Unsupported labels
are relative to this prototype's schema/IR, not a claim about all TF capabilities.
Native gold validation alone does not establish parser quality.

Never overwrite frozen gold when a comparison fails. Research the cause and
version changes to requests, labels, source pins or gold. The runner has no
regeneration mode. See [research](../../docs/research/bhsa-benchmark.md) and
[design](../../docs/design/bhsa-benchmark.md) for the evidence and test strategy.

## Attribution and license

BHSA annotation literals and gold result fingerprints derive from the
[Eep Talstra Centre for Bible and Computer, Vrije Universiteit Amsterdam BHSA](https://github.com/ETCBC/bhsa),
data version 2021, [dataset DOI](https://doi.org/10.17026/dans-z6y-skyh).
BHSA data is [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
The benchmark's BHSA-derived data retains that attribution/license; tf-jev's MIT
software license does not relicense the source corpus. No biblical text is copied
into this benchmark or sent to a model by the runner.
