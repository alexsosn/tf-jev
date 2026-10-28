# Prototype development plan

The bootstrap establishes the autonomous repository contract. Behavior is split into focused issues so every change can follow research → plan → RED → implementation → exact-head verification → independent adversarial review.

## Wave 0 — bootstrap

- #1 — bootstrap package metadata, autonomous workflow, CI, research/design framing and backlog.

## Wave 1 — establish native boundaries

- #2 — research the current Text-Fabric search grammar and validation hooks;
- #3 — define the first typed QueryIR and deterministic native-TF compiler;
- #4 — research corpus schema/value discovery from actual Text-Fabric APIs and a real corpus;
- #5 — implement CorpusSchema extraction and schema-grounded symbol validation.

No model-backed parsing should be merged before these boundaries are tested.

## Wave 2 — semantic parsing prerequisites

- #6 — research the current Jev API, existing Python clients, limits, cost and confidence semantics and define a backend-neutral decision interface;
- #7 — implement deterministic high-cardinality candidate retrieval/narrowing;
- #8 — implement the Jev DecisionBackend adapter;
- #10 — build and freeze a versioned BHSA NL ↔ native-TF benchmark with a held-out partition.

## Wave 3 — semantic parser and evaluation

- #9 — implement schema-aware NL → QueryIR orchestration with explicit ambiguity/abstention against the pre-existing benchmark;
- #11 — add end-to-end evaluation for parse accuracy, TF validity/result equivalence, latency and cost;
- #12 — compare Jev with at least one baseline parser/backend before treating it as the default.

## Wave 4 — ergonomics

- #13 — expose a stable Python API and diagnostic CLI after the evaluation gates justify it.

Documentation and examples should evolve with the implementing tickets rather than being postponed into a disconnected final pass.

## Prototype success criteria

The approach is worth continuing only if the benchmark demonstrates that:

- supported requests compile to syntactically valid native TF queries by construction;
- semantic parse accuracy is useful on nontrivial structural/morphological queries;
- ambiguous/unsupported requests fail safely rather than producing plausible wrong queries;
- model-backed parsing is materially cheaper than a reasonable generative-LLM baseline;
- deterministic compiler/schema layers remain usable independently of Jev.

If these conditions do not hold, preserve the benchmark and compiler work and reconsider the semantic backend rather than forcing Jev deeper into the architecture.

## Research follow-through

- #48 — completed grounded stage diagnostics and stage-specific development calibration;
  no production parser change or fresh end-to-end quality claim.
- #51 — implemented the separately opt-in grounded planner; fresh native-gold
  whole-trajectory evaluation failed usefulness (0/12 supported), so no default change.
- #50 — explicit 1.14/preview support with strict resolved-version checks; observed
  development comparison remains insufficient for a parser recommendation.
- #54 — deferred by user direction: retain Jev before reconsidering another backend.
- #56 — diagnose and repair the Jev integration with controlled focused-state and
  literal-question experiments before another backend or confidence-policy change;
  freeze fresh evaluation before any new quality/default claim.
- #56 implementation — opt-in CandidateParser proposes a complete typed candidate
  before gated semantic fidelity verification; all uncertainty/schema/compiler
  bounds remain explicit. Adaptive development successes do not change defaults.
- #57 — fresh independently adjudicated native-gold evaluation of the repaired
  Jev parser, including remaining exclusion/adjacency/exact-value failures and
  adversarial safety; required before any quality/default recommendation.

- #59 — completed frozen paired ontoTF-context pilot; positive limited opt-in
  adoption gate, with regression/cost limits and no package/default change.
- #60 — extract only the measured bounded ontology metadata adapter into an
  explicitly opt-in public boundary, with separate production RED/wheel/review gates.
- #60 implementation — optional schema-bound XML catalogs, data-driven growth,
  bounded complete-target retrieval/omission diagnostics and exact pilot replay;
  live containment miss remains a #57 usability investigation, not a passed smoke.

- #57 — completed fresh-request evaluation: 5/13 positives, 7/7 safe negatives;
  usefulness gate fails. Containment/presence diagnostic failures preserved.
- #64 — highest feature priority: research scope-preserving parent/witness and
  per-feature bounded Jev proposals; no global threshold lowering/provider pivot.
- #63 — separate bounded alias-contract refresh after upstream jev-latest drift;
  pinned model and default remain unchanged.

#64 development episode: no production extraction after2/8–3/8 positive results
from observed scope variants. Continue focused exclusion/POS-scope research;
[#66](https://github.com/alexsosn/tf-jev/issues/66) isolates correct-candidate
verification false refusals. Preserve final gates and require wheel positives
plus safe negatives before any eventual user-facing fix.
