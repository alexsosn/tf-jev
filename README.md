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
The [first measured evaluation](reports/jev-rules-2026-10-20/README.md) is a no-go
for the current Jev pipeline: it abstained on every supported benchmark request.
The conservative rule baseline also had no supported heldout successes.
Neither is recommended as a default natural-language parser.
[Development-only diagnosis](reports/abstention-diagnosis-2026-10-20/README.md)
localized the blocking stages; simple prompt changes did not establish a safe fix.
[Grounded stage research](reports/grounded-planning-2026-10-20/README.md) improves
selective local decisions, but does not yet establish end-to-end parser quality.
The [fresh grounded-parser evaluation](reports/grounded-parser-2026-10-20/README.md)
also solves 0/12 supported requests. Both parsers remain experimental; the
model-free typed compiler/CLI is available independently.

[Jev repair research](reports/jev-focus-2026-10-20/README.md) identified integration
failures and adds an opt-in CandidateParser. Its adaptive BHSA development run
solves 6/10 supported requests, including complete morphology and containment;
all six negative requests withhold queries. This is development evidence, not
a fresh quality estimate or a default recommendation.

A [frozen paired ontoTF-context pilot](reports/ontotf-context-2026-10-20/README.md)
observes 7/10 correct positives with ontology context versus 5/10 control, with
no ontology wrong emissions and all four negatives safely withheld. Input cost
increases about 27%; one imperative case regresses. This is checkout-only
research supporting the experimental opt-in integration described below, not a
default change.

The [fresh production-parser evaluation](reports/candidate-evaluation-2026-10-28/README.md)
solves **5/13** new supported requests, safely withholding all seven negatives.
It fails the frozen usefulness gate. Actual traces identify parent/witness and
per-feature scope failures; #64 owns the focused Jev repair. Defaults remain
unchanged. The separate wheel diagnostic preserves containment and presence
failures rather than treating refusals as passed positives.

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

CI tests Python 3.11–3.13 against the pinned TF 13.1.0 evidence runtime and
Python 3.12 against the latest release in the supported `>=13.1,<14` range
(currently 13.1.1). Synthetic tiny-corpus tests record the actual runtime version.
Canonical BHSA benchmark/research reports remain pinned to **13.1.0**; a compatible
newer package runtime does not change their version or source verification gates.

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
and tutorial replay remain historical research evidence. This establishes frozen
native ground truth; measured parser results are in the
[evaluation report](reports/jev-rules-2026-10-20/README.md).

The optional `tf-jev[jev]` extra provides `tf_jev.jev.JevBackend`, a thin adapter
over the official TypeSafe SDK. It accepts the bounded decision contract, checks
all returned labels/probabilities, and records resolved model, tokens and latency.
Set `JEV_API_KEY` (or `TYPESAFE_API_KEY`) explicitly; the adapter does not load
`.env` files. Use it as a context manager to close its owned client. See the
[adapter contract](docs/design/jev-adapter.md) for failure and model pinning policy.
The adapter stays independent of semantic parsing.

The default remains pinned to `jev-1.13.0`. To explicitly use the researched newer
version, construct `JevBackend(model="jev-1.14.0")`. `jev-latest` currently requires
1.13.0 and `jev-preview` requires 1.14.0; unexpected resolved versions fail instead
of silently changing results. Receipts retain the actual validated version. Version
support alone does not establish parser quality or change the no-default decision.


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
Scripted real-corpus tests prove orchestration and compiler boundaries. The
[measured evaluation](reports/jev-rules-2026-10-20/README.md) found no supported
query successes with the current Jev policy; the grounded planning research is
recorded in #48 and does not change the default parser or policy.


## Explicit opt-in Jev evaluation (#11)

The checkout-only `scripts.run_jev_evaluation` command connects the canonical
BHSA 2021 v2 benchmark to `SemanticParser` and the pinned
`JevBackend`. It verifies Text-Fabric 13.1.0 and all source feature SHA256
hashes **before constructing the model client**. Set `JEV_API_KEY` securely
in the environment. Install the exact research runtime before a benchmark run:

```bash
python -m pip install -e '.[dev,jev]' 'text-fabric==13.1.0'
```

A small development run:

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
failed the measured usefulness gate in #11/#12 and remains research-only. The
installed wheel's CI smoke creates a real tiny TF corpus and invokes the
`tf-jev` console command for compilation, bounded execution, and failure.


## Experimental opt-in grounded parser

The newer experimental `tf_jev.candidate.CandidateParser` uses bounded choices to
propose a complete typed candidate and a deterministic explanation of that exact
candidate for final fidelity verification. It preserves the .8/.2 final gate,
all proposal distributions, schema checks and budgets. Result `confidence` is
the weakest selected proposal probability, which may be below .8 even for an
accepted candidate; it is **not calibrated whole-query confidence**. Stage-specific
gates are rejected. Opt in explicitly:

```python
from tf_jev.candidate import CandidateParser
from tf_jev.jev import JevBackend

with JevBackend(model="jev-1.14.0") as backend:
    result = CandidateParser(schema, backend).parse("Return feminine singular substantives.")
```

Use the actual loaded corpus schema; `result.query` exists only after acceptance.
The legacy parser, grounded parser and default Jev version remain unchanged.
See the [repair report](reports/jev-focus-2026-10-20/README.md) for remaining failures
and the required fresh evaluation.

`tf_jev.grounded.GroundedParser` adds actual corpus/grammar context and selects
additional features or a tagged stop instead of guessing a predicate count. It
preserves native compilation, bounded retrieval, diagnostics and explicit refusal.
The legacy parser/default policy stays unchanged. This strategy **failed the fresh
usefulness gate** and is available for research, not as a recommended NL interface.
Full schema extraction is required and can be expensive on a large corpus.

```python
from tf_jev.grounded import GroundedParser
from tf_jev.jev import JevBackend
from tf_jev.schema import extract_schema

schema = extract_schema(api)  # loaded native Text-Fabric API; full coverage
with JevBackend() as backend:  # explicitly configured environment credential
    result = GroundedParser(schema, backend).parse("Return words annotated as verbs.")
    print(result.status.value, result.reason)
    if result.query is not None:
        print(result.query)  # compilation alone never executes it
```

Abstention is an expected outcome, including for this simple example. Every
non-supported status clears the query/IR/projection. `GroundedPolicy` optionally
accepts validated `Gate` objects for shape/type/feature stages; its defaults remain
.8 probability/.2 margin. These gates and the weakest decision probability are not
calibrated whole-query correctness. Its context budget counts conservative escaped
SDK-shaped JSON bytes, including descriptions. No benchmark/gold or corpus passage
enters production prompts. See [design/protocol](docs/research/issue-51-grounded-parser.md)
and the [complete measured no-go](reports/grounded-parser-2026-10-20/README.md).


## Optional ontoTF catalog context

`tf_jev.ontology.OntologyParser` adds schema-validated descriptions from a local
ontoTF XML catalog to the candidate parser. It has no additional dependencies,
network catalog download or ontology executor. Select a catalog matching your
actual corpus source/version; matching feature names alone does not prove the
mapping's semantic applicability.

```python
from pathlib import Path
from tf_jev.ontology import OntologyParser, load_catalog
from tf_jev.jev import JevBackend

catalog = load_catalog(
    Path("/path/to/ontoTF/src/tfont/mappings/bhsa.xml"),
    schema,
    corpus="bhsa",
    version="2021",
    # revision="your-selected-ontoTF-commit",  # optional provenance label
    # expected_sha256="actual-64-character-digest",  # pin evaluations explicitly
)
with JevBackend(model="jev-1.14.0") as backend:
    result = OntologyParser(schema, backend, catalog=catalog).parse(
        "Find feminine singular noun words."
    )
print(result.status, result.query)
print(result.catalog.sha256, result.catalog.revision)
print(result.ontology_context)
```

A newer XML file can add native value/concept mappings without tf-jev code edits.
Reload it to create a new immutable snapshot; existing parsers retain their old
snapshot. Results identify the actual XML digest, caller revision label, source,
version, schema key and skipped record dispositions. No bundled fixed concept or
feature list controls coverage. Exact **value** mappings supply context; approximate,
ambiguous/native-only entries and other known mapping kinds are counted but not
used as value-equivalence instructions. New query structures still need compiler
support.

For larger catalogs, the adapter first scopes by its own predicted type/property.
If the complete context exceeds the budget, it retrieves descriptions using
request/target-label token overlap, preserving every scoped binding for each
matched target. Unmatched synonyms may lose extra assistance. If that complete
subset still does not fit, optional context is omitted with `omitted_budget`
diagnostics; native choices remain available. It never truncates a concept's
native alternatives to fit. Catalog input is limited to 2 MiB/10,000 records;
added context to 8 KiB and the complete request to the parser's byte budget.

This remains experimental. The 7/10 versus 5/10 pilot used a fixed small catalog;
the growing-catalog overflow path has deterministic tests but no new quality
measurement. Keep the recorded imperative regression, higher input cost and #57
fresh-evaluation requirement in view. Legacy parser/model defaults are unchanged.
See the [contract](docs/design/issue-60-ontology-context.md) and
[integration evidence](reports/ontology-integration-2026-10-20/README.md).
