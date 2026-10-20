# Jev failure repair (#56)

User direction: retain Jev and explain/repair the integration before considering
another backend. #54 is deferred; no alternative-provider code or calls occurred.
This document precedes new production behavior or model calls.

## Evidence and falsifiable explanations

The frozen #51 strict development run stops 7 times at shape, 2 at type, 1 at
feature, 1 at operator and 1 at verification. The #50 run changes only the Jev
version and solves one integer request. These are not evidence that every losing
trajectory was semantically wrong: the probability gate may reject a correct
winner. Existing records do not expose all distributions for those runs, so obtain
an unchanged control with complete numeric traces instead of inferring causes
from status counts. Old artifacts remain immutable.

Actual GroundedRun.context supplies the full corpus inventory, grammar, every
operator/relation, roles, focus and accumulated selections at EVERY stage. Even
its first shape call consumes about 7,030 input tokens. Subsequent single-field
questions inherit unrelated metadata and serialize selected feature information
indirectly through JSON strings. Predicate operator criteria are just enum names;
the question never names the current feature directly. These are concrete design
properties; their causal contribution requires controlled tests.

Current official [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
(last-reviewed 2026-10-02, fetched 2026-10-20) explicitly warns about irrelevant
state, indirection, literal instructions, counting and chained generation. The
[function-calling cookbook](https://docs.typesafe.ai/cookbooks/function_calling)
uses direct semantic argument descriptions and stated/not-stated questions over
closed sets. This supports testing our integration, not assuming model incapacity.
pg-jev owns structure in code and judges concrete rows; its narrower task is not
proof that our existing planning decomposition is adequate.

## Fixed development experiment

Use all 12 grounded-v1 DEVELOPMENT cases only (8 supported / 4 negative), same
source-verified full BHSA 2021 schema and TF 13.1.0 / SDK 0.7.4. Never load heldout
requests into the experiment. Pin Jev 1.14.0, .8 probability/.2 margin throughout.
No threshold tuning or replacement runs. Validate native development gold first.
For each case, run these variants in fixed order, once each:

1. Exact unchanged GroundedParser control, recording full distributions and actual
   prompts privately for semantic failure inspection (no gold in model context).
2. Focused-state ablation: same questions/options and gates, but send only request,
   grammar for shape, current role/predicted focus for other stages, and the current
   feature/operator selections when relevant. Feature choices still enumerate ALL
   features from the full schema; type/value choices are unchanged. No lexical
   pruning, selected-coverage claim or guessing omitted symbols. Candidate fidelity
   sees complete predicted IR/projection plus grammar. This tests distracting state.
3. Focused state plus literal criteria: same admissible choices, with plain-language
   operator meanings and a question explicitly naming the selected node/feature;
   no change in allowable operators or corpus-specific hardcoding. This tests an
   additional semantic indirection hypothesis; it does not isolate every wording
   effect and must not be described as such.

Only the parser's OWN predicted history is used. Record ALL call attempts, errors,
receipt usage/latency/version and positional distributions. Unknown failed usage
stays unknown. No retries; no old outcome replacement. Model budget <=.10 USD in
known-returned-usage at the verified .042/M input/free output rate (recheck before
calls); stop before a further call if the measured budget is reached. Native/schema
CPU and possible unreturned usage remain separate. Keep raw prompts/query/predictions
private for review; public output uses static case/stage IDs and numeric data.

Compare complete emitted semantics, native projection/results and independently
re-derived raw annotation/slot/edge oracles; stages are diagnostic only. Inspect
correct winners rejected by confidence separately from wrong winners, dropped
constraints, wrong scope/value/operator and verifier failures. No claim that a
confidence increase alone improves correctness. A development success is not a
fresh generalization score. If no full positive works, explain the observed next
blocking mechanism before choosing a further small experiment.

## Gates after evidence

Research helper transformations require deterministic RED-first tests and exact
wire mapping checks before inference. Production changes only after persisted
results/design and their own RED-first tests. Keep native compiler/schema/retrieval,
explicit non-success without query, bounded symbols/values/calls/context and all
legacy behavior. Do not globally lower gates or hardcode benchmark phrases.

Before a default/quality claim, freeze independently reviewed fresh native gold;
observed v2/grounded-v1 remain regression evidence. Exact-head complete suite,
logically independent skeptical review and genuine installed-wheel NL morphology
and relation positive plus safe-negative smokes finish a successful dev episode.
