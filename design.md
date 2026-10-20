# Provisional architecture

This design is intentionally narrow and may change after the grammar/schema research issue.

## Components

### 1. CorpusSchema

An immutable snapshot of query-relevant capabilities extracted from a loaded Text-Fabric corpus.

Expected categories include:

- node types;
- node features;
- edge features;
- small enumerated feature domains;
- references to retrieval indexes for high-cardinality domains.

The schema layer must contain corpus facts, not model prompts.

### 2. Query IR

A typed, serializable representation of supported query intent.

The initial IR should be designed only after the current native TF search grammar is researched. It should make invalid combinations unrepresentable or fail validation before compilation.

Likely concepts include atoms, feature predicates, relations and a limited quantifier/composition subset.

### 3. Candidate retrieval

A deterministic layer that turns an unbounded phrase such as a lemma/name/value mention into a bounded candidate list tied to the corpus schema.

Retrieval and semantic ranking are separate concerns and must be benchmarked separately.

### 4. DecisionBackend

Backend-neutral interface for bounded semantic decisions.

A backend may expose choice, binary/noul and score-like operations with probabilities. Jev will be the first implementation researched, but no backend may bypass IR validation. The Jev implementation should prefer a thin adapter over an existing vetted Python client/toolkit; tf-jev should not own generic HTTP/retry/auth machinery without evidence that available clients are inadequate.

### 5. Semantic parser

Orchestrates schema-aware decisions to transform a natural-language request into the typed IR.

It must preserve uncertainty and be able to abstain.

### 6. Deterministic compiler

Pure code from validated IR to native Text-Fabric query text.

Properties:

- no network;
- no model dependency;
- deterministic output;
- escaping/validation owned here;
- exhaustive unit tests for supported grammar;
- parser validation against real Text-Fabric behavior.

### 7. Validation/evaluation

The final compiled query is checked using Text-Fabric and, for benchmark cases, compared with gold execution semantics.

## Dependency direction

```text
Text-Fabric app ──> CorpusSchema ──> SemanticParser ──> QueryIR ──> Compiler ──> TF search
                                    ↑
                             DecisionBackend
                                    ↑
                                  Jev
```

Candidate retrieval sits beside the schema/parser boundary and cannot emit query text directly.

## Public API principles

The eventual public result should expose at least:

- original natural-language request;
- validated IR;
- compiled native query;
- confidence/decision evidence;
- warnings/unsupported reasons;
- backend/model identity sufficient for reproducibility.

The API must permit compile-only tests from an IR without any backend credentials.

## Error policy

Distinguish:

- invalid corpus/schema state;
- unsupported TF grammar construct;
- unsupported natural-language intent;
- ambiguous parse / confidence below policy;
- candidate retrieval miss;
- backend transport/model failure;
- compiler invariant violation;
- TF parser/execution failure.

Do not collapse these into a generic "could not compile" error.

## Compatibility

The package should target an explicit supported Text-Fabric version range and test that range. Corpus-specific adapters may exist later, but generic code must not depend on BHSA feature names or annotation conventions.

The initial compiler contract (#3) is specified in
[docs/design/typed-compiler.md](docs/design/typed-compiler.md). It uses a narrow
`SymbolSchema` protocol until #5 implements the immutable corpus snapshot.

The schema extraction contract (#5) is specified in
[docs/design/corpus-schema.md](docs/design/corpus-schema.md). CorpusSchema
implements SymbolSchema while retaining full exact value membership locally,
separate from bounded summaries and later retrieval/model decisions.

The retrieval contract (#7) is specified in
[docs/design/candidate-retrieval.md](docs/design/candidate-retrieval.md). Local
identity-bound indexes preserve raw strings, expose collision/overflow counts,
and hand only complete sets of at most 32 opaque options to a decision backend.

The optional Jev adapter (#8) is specified in
[docs/design/jev-adapter.md](docs/design/jev-adapter.md). The official SDK owns
transport/retries; tf-jev checks request-bound answers, model/usage metadata and
sanitizes errors/logs before returning backend-neutral decisions and receipts.

Semantic benchmark (#10): [v2 evidence contract](docs/design/bhsa-benchmark.md)
specifies returned-column projection, frozen result-set fingerprints and strict
source/version/diagnostic gates independently of parser prompts.

Semantic orchestration (#9): [parser contract](docs/design/semantic-parser.md)
defines bounded choices, supported shapes, evidence/receipts, output projection and
sanitized non-success states. Compiler/native execution remain independent.

Grounded planning research (#48): [experimental strategy design](docs/design/issue-48-grounded-planning.md)
replaces unaided predicate counting with bounded feature/DONE selection and adds
explicit corpus/grammar context. Stage-specific policies remain research evidence;
fresh native-gold evaluation and a separate implementation gate precede adoption.


Grounded implementation (#51): `tf_jev.grounded.GroundedParser` is separately opt-in,
shares checked choices/predicates/compilation with the legacy parser, uses a tagged
feature-stop sentinel and includes the full predicted IR/projection in fidelity
context. `GroundedPolicy` has explicit finite per-stage gates and a conservative
serialized-context byte budget. Its default gates are unchanged, and its fresh
experiment failed usefulness. Production defaults remain the legacy research API.


Candidate planning (#56): [extraction contract](docs/research/issue-56-candidate-parser.md)
uses bounded proposals, unmodified weakest-proposal confidence and a separately
gated complete-candidate fidelity verdict. The deterministic explanation describes
validated IR; native TF still executes it. No per-field gate relaxation in legacy
parsers, no alternative backend, and no change to defaults.


Optional ontology context (#60): [catalog contract](docs/design/issue-60-ontology-context.md)
binds a local immutable XML snapshot to the actual schema, adds bounded exact
value descriptions, and records source/digest/dispositions/context selection in
results. Growing catalogs are data; native options/IR/compiler/execution remain
authoritative. No provider/dependency/default change.
