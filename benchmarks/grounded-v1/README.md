# Grounded parser benchmark v1

New dataset identity **grounded-v1**; file SHA256
`0a9f8d1a1808b8cfd07a1815bfcaba3ae34381d55dec3475039e1ebbe32f7b27`.
Uses the existing **nl-tf-v2 serialization format**, not its previously observed
requests/partition. Load with `load_benchmark(path)`; report this dataset name and
actual file hash, never the canonical v2 digest. Pin BHSA 2021 / native TF 13.1.0.
All feature-source hashes required for gold are in the JSON.

33 newly authored NL requests: calibration (development) has eight supported,
two ambiguous and two unsupported; evaluation (heldout) has twelve supported,
two ambiguous and seven unsupported. Family names/construct groups do not cross
partitions. Calibration has conjunction, literal lexeme, phrase function, integer
comparison and parent exclusion. Evaluation stresses disjunction/inequality,
annotation presence, slot/edge direction and output projection, positive
containment, mixed exclusion and frequency. Negatives include four-predicate and
four-alternative overflow, unknown type/literal, regex, feature-to-feature
comparison, aggregation, three atoms, per-parent top-one and unresolved references.

Frozen before revised parser implementation or model inference. The same context
authored and independently reviewed this dataset, re-deriving each supported NL
request from actual annotation membership and raw slot/edge relationships without
TF search or compiler. All 20 result counts/signatures match separate native gold
execution; [independent evidence](independent-review.json). Negative review checks
missing reference/interpretations and exact compiler capability boundaries, not
merely empty corpus results; unknown paragraph type and nonexistent lex literal
were also checked against actual native inventories. Native regex is deliberately
outside this IR, while presence and inequality retain native missing-value rules.

Fresh means unobserved by this parser/model experiment, not unknown to the author
or a large independent population sample. Some basic concepts recur from older
research. Do not claim external blinded annotation or statistical representativeness.
Gold is scoring/review input only, never production prompt/candidate construction.
No tuning on evaluation after inference. The previously observed v2 is regression
only. The fixed policies, selection and success gates are in
[the preregistered protocol](../../docs/research/issue-51-grounded-parser.md).

Native source verification and replay:

```bash
python -m scripts.nl_benchmark_v2 /path/to/bhsa/tf/2021 \
  --benchmark benchmarks/grounded-v1/bhsa-2021.json --partition development
python -m scripts.nl_benchmark_v2 /path/to/bhsa/tf/2021 \
  --benchmark benchmarks/grounded-v1/bhsa-2021.json --partition heldout
```

These are model-free gold checks, not parser scores. Dataset bytes and semantic
labels stay immutable once frozen; any correction after quality measurement must
be disclosed rather than silently regenerating a favorable evaluation.
