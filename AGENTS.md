# tf-jev agent instructions

tf-jev is designed for autonomous, issue-driven development. Coding agents must treat this file as the mandatory entry point.

## Read first

Before changing behavior, read in order:

1. `README.md`
2. `research.md`
3. `design.md`
4. `plan.md`
5. `docs/agentic-dev-loop.md`
6. the active GitHub issue and all linked PR/review discussion

When work depends on Text-Fabric, a concrete corpus, Jev/TypeSafe, or another decision backend, verify the current contract against actual code, data and authoritative documentation rather than relying on memory.

## Development gates

Every behavior-changing ticket follows:

**research → plan/design → RED-first TDD → implementation → exact-head tests → logically independent adversarial review**

- Work from a GitHub issue with explicit acceptance criteria.
- Check open issues/PRs for overlap before starting.
- Persist material research before implementation.
- Add a deterministic failing test before production behavior whenever the change is testable.
- Implement the smallest coherent contract that satisfies the researched need.
- Run the complete relevant suite on the exact final head.
- A review is valid only for the exact reviewed head. Any production-code change after approval invalidates it.
- Behavior-changing review fixes repeat RED → fix → GREEN → re-review.
- Review must be skeptical and evidence-driven, preferably exercising a real Text-Fabric query/corpus path.
- Merge only after acceptance criteria, exact-head tests and independent review pass.

Research may open focused follow-up issues when evidence reveals separate work. Do not manufacture scope.

## Architectural invariants

### Native TF remains authoritative

tf-jev compiles into native Text-Fabric search. Do not build a second execution engine when Text-Fabric already owns the semantics.

### No free-form model query generation

A model backend must not directly emit arbitrary TF search strings. The model may select or score bounded alternatives used to construct a typed IR. Query text is produced by deterministic code.

### Schema-grounded choices

Node types, node features, edge features, feature values and other corpus-specific symbols must be derived from or validated against the actual loaded corpus. Never hard-code BHSA semantics into the generic compiler.

### Deterministic compiler boundary

Given the same validated IR and compiler version, emitted query text must be deterministic. Compiler tests must not require a model or network.

### High-cardinality values

Do not send unbounded vocabularies to a bounded-choice model. Research and implement deterministic retrieval/narrowing before the semantic decision step.

### Ambiguity is data

Confidence, alternatives, abstention and unsupported-query states are part of the public correctness contract. Do not silently coerce an uncertain parse into a query.

### Backend independence

Jev is the first target decision backend, not the package architecture. Keep backend-specific HTTP/auth/model details outside the corpus schema, IR and compiler layers.

## Evaluation requirements

A convincing prototype needs all of:

- unit tests for IR validation and deterministic compilation;
- grammar coverage tests against Text-Fabric's real parser/search surface;
- at least one real TF corpus in integration/evaluation work;
- a versioned benchmark of natural-language requests with gold native TF queries or equivalence expectations;
- exact-match metrics where appropriate plus execution/result equivalence metrics;
- latency/token/cost/error accounting for model-backed parsing;
- adversarial examples for ambiguity, unsupported semantics and schema mismatch.

Mocks may test transport and deterministic edge cases but cannot establish semantic parser quality.

## Security and data handling

- Treat natural-language requests and corpus schema/feature values as untrusted input.
- Never interpolate unchecked model output into executable TF query text.
- Keep credentials out of logs, fixtures, recorded benchmark artifacts and exception strings.
- Network-backed tests must be opt-in unless the active issue explicitly establishes a safe deterministic contract.
- Do not send corpus text to a model merely to compile a structural query unless the researched design explicitly requires and documents that data flow.

## Autonomous loop

When no unblocked feature ticket remains, continue with performance, stability, ergonomics, documentation, evaluation quality, security, release engineering and edge cases using the same gate sequence.

Do not leave duplicate or orphaned implementation PRs/branches. One ticket should have at most one canonical active implementation PR.
