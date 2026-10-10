# Prototype development plan

The bootstrap establishes the autonomous repository contract. Behavior is split into focused issues so every change can follow research → plan → RED → implementation → exact-head verification → independent adversarial review.

## Wave 0 — bootstrap

- Python package metadata and importable `tf_jev` namespace;
- authoritative agent instructions and autonomous loop;
- pytest, Ruff and strict mypy;
- CI across the supported Python matrix;
- initial research/design documents;
- prioritized GitHub issue backlog.

## Wave 1 — establish native boundaries

1. research the current Text-Fabric search grammar and validation hooks;
2. research corpus schema/value discovery from actual Text-Fabric APIs and a real corpus;
3. define and implement the first typed query IR plus deterministic compiler for a deliberately small grammar subset.

No model-backed parsing should be merged before these boundaries are tested.

## Wave 2 — semantic parsing primitives

4. research the current Jev API, limits, cost and confidence semantics and define a backend-neutral decision interface;
5. implement deterministic high-cardinality candidate retrieval/narrowing;
6. implement Jev-backed semantic decisions and NL → IR orchestration with explicit ambiguity/abstention.

## Wave 3 — evaluation

7. build a versioned NL ↔ native-TF benchmark on a real corpus;
8. add end-to-end evaluation for parse accuracy, TF validity/result equivalence, latency and cost;
9. compare Jev with at least one baseline parser/backend before treating it as the default.

## Wave 4 — ergonomics

10. expose a stable Python API and minimal CLI, with diagnostics that show IR, compiled query, confidence and unsupported reasons;
11. document corpus integration and add examples for simple morphology, structural relations and quantifier cases.

## Prototype success criteria

The approach is worth continuing only if the benchmark demonstrates that:

- supported requests compile to syntactically valid native TF queries by construction;
- semantic parse accuracy is useful on nontrivial structural/morphological queries;
- ambiguous/unsupported requests fail safely rather than producing plausible wrong queries;
- model-backed parsing is materially cheaper than a reasonable generative-LLM baseline;
- deterministic compiler/schema layers remain usable independently of Jev.

If these conditions do not hold, preserve the benchmark and compiler work and reconsider the semantic backend rather than forcing Jev deeper into the architecture.
