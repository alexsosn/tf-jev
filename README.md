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

Bootstrap / research prototype. There is no production Jev integration yet.

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
python -m pip install -e '.[dev]'
python -m ruff check .
python -m mypy
python -m pytest -q
```

Real-corpus conformance tests are opt-in and run against BHSA 2021 (no download in CI):

```bash
TF_JEV_BHSA_DIR=~/text-fabric-data/github/ETCBC/bhsa/tf/2021 python -m pytest -q tests/conformance
```

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
