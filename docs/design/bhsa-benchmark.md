# Versioned BHSA benchmark contract (#10)

Freeze `benchmarks/nl-tf-v2/bhsa-2021.json`, independently versioned from parser
prompts and retrieval-v1. Aim near 100 cases while keeping meanings defensible.
Each case has a stable ID, family, partition, request, expected classification and
rationale. Supported cases have a native gold query, output-column projection,
distinct projected count and SHA256 signature. Ambiguous cases have at least two
interpretations; unsupported cases explain the prototype limitation. Abstentions
have no executable gold. A zero-result supported query is a legitimate answer.

The internal evidence tool `scripts/nl_benchmark_v2.py` validates the artifact,
verifies source hashes and TF version, executes native TF with error/overflow
checks, and compares projected result sets. It neither parses NL nor generates TF
query text. The default partition is development; held-out execution requires an
explicit flag. Report support classes separately and do not count abstentions as
execution passes. Full parser metrics/latency/cost belong to #11.

Result signatures encode output width and sorted distinct tuples using canonical
JSON. Projection order determines semantic roles, so swapping columns can change
the score. Witness multiplicity and native enumeration order do not. No gold
regeneration mode exists in the runner. Version/source mismatch, malformed cases,
invalid native templates, missing output columns and result overflow fail closed.

RED tests cover strict artifact validation, partition isolation, set/projection
semantics, genuine empty results and invalid quantifier diagnostics using a tiny
real TF corpus. Opt-in BHSA integration executes every supported gold and compares
frozen counts/signatures. Independent adversarial review re-derives semantic results
from raw features, slots and edges instead of relying only on gold re-execution.

## Version migration

`nl-tf-v2` is the canonical complete benchmark for parser/evaluation work.
`nl-tf-v1` and its tutorial/native replay are historical provenance tooling,
not a second active parser dataset. Retain all original v1 evaluation requests
in v2 heldout; add tests preventing development exposure. The new JSON version
adds family, interpretations and output projection/signatures, so v1's strict
loader remains unchanged. Use a separate versioned loader and the shared native
`run_template` diagnostic contract. No parser is allowed to combine the legacy
v1 development cases with v2 heldout families for tuning.
