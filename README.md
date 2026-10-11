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
and an optional Jev bounded-decision adapter. End-to-end NL parsing is not yet implemented.

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
handles. See the
[compiler contract](docs/design/typed-compiler.md) for supported constructs,
explicit errors and native quantifier workarounds. Compilation does not execute
or evaluate the resulting query.

`tf_jev.retrieval.RetrievalIndex.from_schema(schema, handle)` narrows a large
string domain locally with exact or explicit normalized/prefix lookup. Results
preserve original strings and collisions. A complete result can produce a bounded
`ChoiceQuestion`; no-match and overflow block that handoff. See the
[retrieval contract](docs/design/candidate-retrieval.md) and
[real-domain lookup benchmark](benchmarks/retrieval-v1/README.md).

A versioned BHSA benchmark now has **19 requests**, including **12 supported native
gold queries** (six with independently adjudicated typed IR and exact native result
equivalence), with the original evaluation split preserved. See
[benchmark documentation](benchmarks/nl-tf-v1/README.md). Six native tutorial
candidates were promoted after real BHSA 2021 replay and separate semantic
review; eight remain [unpromoted discovery cases](benchmarks/nl-tf-v1/tutorial-candidates.md).
This establishes no Jev parsing accuracy and is not a completed #10 benchmark.

The optional `tf-jev[jev]` extra provides `tf_jev.jev.JevBackend`, a thin adapter
over the official TypeSafe SDK. It accepts the bounded decision contract, checks
all returned labels/probabilities, and records resolved model, tokens and latency.
Set `JEV_API_KEY` (or `TYPESAFE_API_KEY`) explicitly; the adapter does not load
`.env` files. Use it as a context manager to close its owned client. See the
[adapter contract](docs/design/jev-adapter.md) for failure and model pinning policy.
This adapter does not implement natural-language parsing; that remains #9.

Live synthetic contract smoke is opt-in and excluded from normal CI:

```bash
TF_JEV_LIVE=1 python -m pytest -q tests/test_jev_live.py
```

Deterministic adapter tests use the real SDK with HTTP MockTransport. They check
the transport/validation boundary and do not establish semantic model accuracy.
