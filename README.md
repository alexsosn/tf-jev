# tf-jev

Experimental natural-language compiler for native [Text-Fabric](https://github.com/annotation/text-fabric) search queries.

The project explores whether cheap bounded-decision models such as TypeSafe Jev can decode a natural-language request into a **typed query representation** that is then compiled deterministically into native Text-Fabric search syntax.

## Core rule

The model does **not** generate arbitrary Text-Fabric query text.

The intended pipeline is:

```text
natural language
    ↓
corpus schema extraction / candidate retrieval
    ↓
bounded structured decisions
    ↓
typed query IR
    ↓
deterministic compiler
    ↓
native Text-Fabric search template
    ↓
Text-Fabric parser / search
```

This lets the compiler restrict node types, features, values, edge features, relations, operators and quantifiers to constructs actually supported by the loaded corpus and the researched Text-Fabric grammar.

## Status

Research prototype with a deterministic compiler, corpus schema, local retrieval,
an optional Jev bounded-decision adapter, and a first bounded semantic parser.
Model parsing quality has not yet been established.

The first development goal is to establish whether the approach is accurate and cheap enough on real Text-Fabric queries, using a benchmark with gold natural-language ↔ native-query pairs and at least one real corpus.

## Intended public shape

The exact API is intentionally deferred until the relevant research tickets are complete. A likely eventual interface is conceptually:

```python
compiler = QueryCompiler(app)
result = compiler.compile(
    "find feminine plural verbs immediately followed by singular feminine nouns"
)

print(result.query)
print(result.ast)
print(result.confidence)
```

The returned `query` must come from a deterministic compiler over a validated typed representation.

## Prototype principles

- prefer native Text-Fabric search over inventing a parallel query language;
- derive admissible choices from the actual loaded corpus schema;
- retrieve/narrow high-cardinality feature values before model classification;
- treat confidence, ambiguity, unsupported requests and abstention as correctness behavior;
- test compilation separately from semantic parsing;
- evaluate against real TF syntax and a real corpus, not only mocks;
- keep the decision backend replaceable so Jev can be compared with other structured parsers.

## Development

```bash
python -m pip install -e '.[dev,jev]'
python -m ruff check .
python -m mypy
python -m pytest -q
```

Real-corpus conformance tests in the ordinary matrix are opt-in and run against BHSA 2021:

```bash
TF_JEV_BHSA_DIR=~/text-fabric-data/github/ETCBC/bhsa/tf/2021 python -m pytest -q tests/conformance
```

For reproducible benchmark research, the scoped
[BHSA replay workflow](.github/workflows/bhsa-replay.yml) checks out a
commit-pinned public BHSA 2021 corpus, executes native TF 13.1.0 queries,
and compares aggregate results to the
[native-only observation reference](benchmarks/nl-tf-v1/native-observations-2021.json).
The normal Python matrix does not download BHSA. Reproduce locally with
`python -m scripts.bhsa_replay --corpus /path/to/bhsa/tf/2021 --expected benchmarks/nl-tf-v1/native-observations-2021.json --output /tmp/bhsa-report.json`.
The 14 replayed tutorial cases still require independent NL↔query semantic
adjudication before promotion to benchmark gold.

Repository development is issue-driven. Coding agents must start with [AGENTS.md](AGENTS.md) and follow the research → plan/design → RED-first TDD → implementation → exact-head verification → logically independent adversarial review loop.

See [research.md](research.md), [design.md](design.md), [plan.md](plan.md), and [docs/agentic-dev-loop.md](docs/agentic-dev-loop.md).

The typed compiler subset is available independently of any model:
`tf_jev.ir` defines frozen query records and closed operator enums;
`tf_jev.compiler.compile_query(query, schema)` validates and renders native TF
search text. Its `SymbolSchema` protocol is the boundary for corpus-grounded
symbol/value checks; `tf_jev.schema.extract_schema(api)` extracts an immutable
`CorpusSchema` from a loaded Text-Fabric core API. Extraction loads admissible
local features and retains exact membership, with high-cardinality inventories
kept out of its JSON summary. See the
[schema contract](docs/design/corpus-schema.md) for identity, lookup and retrieval
handles.

For deterministic, known-feature queries, schema extraction can be explicitly
scoped to a feature shortlist without suggesting the entire corpus was examined:

```python
from tf_jev.schema import extract_schema

scoped = extract_schema(api, node_features=("sp", "gn", "nu"), edge_features=())
assert scoped.coverage.mode == "selected"
assert "lex" in scoped.coverage.omitted_node_features
```

Only covered features have validated inventories. Unloaded but discovered
features are **unknown**, not absent, and compiler access to them raises an error.
An explicit empty tuple differs from omitting the option: with both parameters
omitted, the legacy **full** extractor and its original corpus identity remain
unchanged. Selected feature names are included in the snapshot identity and
large-domain retrieval handles. The current natural-language `SemanticParser`
abstains on all selected-coverage schemas; partial-mode NL parsing requires a
separately reviewed completeness policy. The
[schema coverage design](docs/design/issue-37-selected-coverage.md) details
these boundaries. To measure a local selected feature set:

```bash
python -m scripts.profile_schema /path/to/bhsa/tf/2021 \
    --node-features sp gn nu --edge-features
```

See the
[compiler contract](docs/design/typed-compiler.md) for supported constructs,
explicit errors and native quantifier workarounds. Compilation does not execute
or evaluate the resulting query.

`tf_jev.retrieval.RetrievalIndex.from_schema(schema, handle)` narrows a large
string domain locally with exact or explicit normalized/prefix lookup. Results
preserve original strings and collisions. A complete result can produce a bounded
`ChoiceQuestion`; no-match and overflow block that handoff. See the
[retrieval contract](docs/design/candidate-retrieval.md) and
[real-domain lookup benchmark](benchmarks/retrieval-v1/README.md).

The canonical [BHSA benchmark v2](benchmarks/nl-tf-v2/README.md) has **109 requests**:
86 supported gold queries, 11 ambiguous and 12 unsupported cases. All supported
gold has frozen projected-result counts and signatures, verified against native
TF and independent raw corpus oracles. Whole families are held out, including
all original v1 evaluation requests. The [v1 seed](benchmarks/nl-tf-v1/README.md)
and tutorial replay remain historical research evidence. This establishes no
model parsing accuracy; that remains #9/#11.

The optional `tf-jev[jev]` extra provides `tf_jev.jev.JevBackend`, a thin adapter
over the official TypeSafe SDK. It accepts the bounded decision contract, checks
all returned labels/probabilities, and records resolved model, tokens and latency.
Set `JEV_API_KEY` (or `TYPESAFE_API_KEY`) explicitly; the adapter does not load
`.env` files. Use it as a context manager to close its owned client. See the
[adapter contract](docs/design/jev-adapter.md) for failure and model pinning policy.
The adapter stays independent of semantic parsing.

Live synthetic contract smoke is opt-in and excluded from normal CI:

```bash
TF_JEV_LIVE=1 python -m pytest -q tests/test_jev_live.py
```

Deterministic adapter tests use the real SDK with HTTP MockTransport. They check
the transport/validation boundary and do not establish semantic model accuracy.

`tf_jev.parser.SemanticParser(schema, backend).parse(request)` composes bounded
schema-derived choices into validated QueryIR and deterministic query text. The
prototype supports one atom, two related atoms, and negated containment, with
up to three feature predicates per atom. Every result preserves decision
distributions/receipts and the weakest selected probability. Low confidence,
unsupported intent and failed whole-candidate verification return no query.
`result.projection` specifies ordered columns for distinct output tuples; native
TF still returns all witness columns. Large values use exact local literal
retrieval before selection, with explicit miss/budget failures. See the
[parser contract](docs/design/semantic-parser.md) for limits and data flow.
Scripted real-corpus tests prove orchestration and compiler boundaries, not model
semantic accuracy; #11/#12 must evaluate quality and cost before default use.


## Explicit opt-in Jev evaluation (#11)

The checkout-only `scripts.run_jev_evaluation` command connects the canonical
BHSA 2021 v2 benchmark to `SemanticParser` and the pinned
`JevBackend`. It verifies Text-Fabric 13.1.0 and all source feature SHA256
hashes **before constructing the model client**. Set `JEV_API_KEY` securely
in the environment and install `.[dev,jev]`. A small development run:

```bash
TF_JEV_LIVE=1 python -m scripts.run_jev_evaluation /path/to/bhsa/tf/2021 \\
  --partition development --max-cases 1 --live --output /tmp/tf-jev-dev-1.json
```

This makes paid network calls; both `TF_JEV_LIVE=1` and `--live` are
required, as is a deliberate case limit. Each request can use several model
calls. Output files must be new, and the report explicitly identifies
canonical-prefix samples rather than mislabeling them as whole-partition
measurements. Add `--input-usd-per-million` and `--output-usd-per-million`
only when the corresponding model prices are independently verified; otherwise
estimated cost remains unknown. No prompt, raw corpus text, gold query or
API credential is written to the report. Treat held-out results as evaluation
only; do not tune the parser after inspecting them and still claim an
unbiased held-out score. Scripted CI tests verify safety and native TF
integration but do not establish Jev accuracy.


## Model-free diagnostic CLI

After installing the package (also available from its wheel), compile an
explicitly typed, corpus-grounded Text-Fabric query **without Jev or credentials**:

```bash
tf-jev compile --corpus /path/to/bhsa/tf/2021 --type word --eq sp=verb
tf-jev compile --corpus /path/to/bhsa/tf/2021 --type word --eq sp=verb \
  --execute --limit 100000
```

The command emits machine-readable JSON with native query text, schema
identity, and `coverage_mode=selected`. Optional `--execute` asks native TF
to run the validated query and reports only a complete result count; it
**fails rather than truncating** when the explicit result limit is exceeded or
Text-Fabric reports an execution error. Other supported predicates are repeated
`--eq FEATURE=VALUE`, `--present FEATURE`, and `--absent FEATURE`; the
CLI checks node/feature types and literals against the actual loaded corpus.

This intentionally supports one atom and known annotations, without pretending
to interpret natural-language requests. The experimental natural-language parser
remains gated by independent accuracy and cost evaluation (#11 and #12). The
installed wheel's CI smoke creates a real tiny TF corpus and invokes the
`tf-jev` console command for compilation, bounded execution, and failure.
