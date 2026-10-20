# Autonomous development loop

## 1. Select work

Choose the highest-priority unblocked issue. Read the issue, linked research/design, open PRs and recent related changes. Do not start a duplicate implementation.

## 2. Research

Inspect actual current Text-Fabric code/documentation, real corpus metadata/data, and the current Jev/decision-backend contract relevant to the issue.

Research should answer:

- what native TF behavior must be represented;
- what is generic versus corpus-specific;
- what finite choice domain can be derived rather than invented;
- where high-cardinality retrieval is required;
- failure, ambiguity, privacy and security boundaries;
- how correctness can be tested independently of the implementation.

Persist durable findings in `research.md` or a focused `docs/research/` document. Research may create separate issues when evidence reveals independent work.

## 3. Plan/design

Before production code, define:

- public/internal API;
- typed IR or schema changes;
- invariants and failure/abstention policy;
- compatibility constraints;
- test and benchmark strategy;
- non-goals.

Broad grammar/IR changes require an update to `design.md` or a focused ADR/design document.

## 4. RED-first TDD

For testable behavior:

1. add a deterministic test against the intended production API;
2. run it before implementation;
3. preserve the observed RED result in the PR/development record;
4. implement the smallest correct behavior;
5. run the focused test to GREEN;
6. run the complete affected suite.

Compiler and schema tests should exercise real Text-Fabric contracts where feasible. Model transport mocks may not be used as evidence of semantic quality.

## 5. Integration gates

Use risk-appropriate evidence:

- TF grammar/compiler work: validate against the actual Text-Fabric parser/search API;
- schema discovery: inspect/load an actual tiny or public TF dataset;
- high-cardinality retrieval: use real feature domains and adversarial normalization cases;
- Jev/backend work: deterministic mocked transport tests plus explicit opt-in live contract/evaluation tests;
- semantic parser quality: versioned gold benchmark on a real corpus;
- release work: exact package build/install plus supported Python matrix.

## 6. Freeze exact head

Record the commit under review and run all relevant tests/lint/type checks on that exact head. Production changes after this point require re-running the affected gates.

## 7. Logically independent adversarial review

Review the exact final head from a fresh skeptical perspective. Re-derive failure modes from the user-facing NL request and native TF semantics instead of validating the implementer's explanation.

Attack questions include:

- Can model output inject or invent TF syntax?
- Does the IR permit a combination that the compiler cannot map unambiguously?
- Is the compiler escaping feature values correctly?
- Does schema extraction confuse node features with edge features?
- Did a BHSA-specific name or convention leak into generic code?
- Does candidate retrieval silently omit the correct high-cardinality value?
- Does confidence aggregation hide one low-confidence structural decision?
- Can an unsupported semantic request produce a valid but wrong structural query?
- Are benchmark queries leaking into prompts/examples in a way that inflates accuracy?
- Are tests proving actual TF parser/execution behavior rather than a local imitation?
- Are credentials, corpus data or prompts exposed in logs/errors?

Any behavior-changing fix invalidates the old review and requires re-review of the new head.

## 8. Merge and continue

Merge only after the exact head is green and independently reviewed. Close the issue, reconcile the backlog and take the next unblocked item.

If the feature backlog is empty or blocked, continue performance, stability, ergonomics, documentation, evaluation quality, security, release engineering and edge cases under the same loop.

When diagnosing model failures, distinguish a wrong semantic choice from a correct
proposal rejected by an admission gate. An exclusive-choice distribution over
several equally valid required properties is not whole-query confidence. Inspect
bounded complete hypotheses and native results before blaming/replacing the
backend. Diagnostic hypotheses never count as accepted user successes. Preserve
all observed failures; adaptive development cases cannot become fresh evaluation.
