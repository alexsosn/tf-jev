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
