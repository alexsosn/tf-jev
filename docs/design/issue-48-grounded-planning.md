# Experimental grounded planner design (#48)

Status: researched, not a production parser implementation. The first measured
stage results are in [the report](../../reports/grounded-planning-2026-10-20/README.md).
The current SemanticParser and ParsePolicy remain unchanged and research-only.

## Boundary and proposed orchestration

Keep ParseResult/QueryIR/compiler/native TF execution boundaries. Implement a
separate opt-in strategy, not an unnoticed change to the first measured parser.
Its first support decision must contain the actual IR limits/operators/relations
and corpus capabilities, with explicit distinction between native TF and the
compiler subset. Pass only schema facts, NL and locally selected descriptions;
never arbitrary model text, unrestricted feature values or corpus passages.

The research `build_probe(schema, request, stage, kind, selected)` constructs an
immutable DecisionRequest plus a local positional symbol map. It refuses partial
schemas, oversized inventories (>255 combined symbols), >255 options, >64 KiB of
SDK-shaped JSON and invalid histories; it never truncates. JSON-escaped corpus
metadata remains data. Slot versus non-slot roles and attested feature names
come from actual schema domains, not BHSA-specific assumptions. Types retain
native order. A type with no attested values can still support an absence test;
feature candidates must not be discarded merely for being unattested on it.

Replace up-front numeric predicate counts with a bounded iteration: select one
new feature or a typed DONE sentinel, select compatible operator and bounded
values, update the typed partial plan, repeat. Any remaining feature is acceptable
regardless of order. Feature selection is semantic; counts, duplicate checks and
termination are deterministic. At the three-predicate boundary, require a final
DONE/complete decision or explicitly abstain; never drop a fourth requested
constraint. The implemented research helper refuses an actual `DONE` feature
name to avoid a string sentinel collision. A production design should use a
separate tagged sentinel so all valid corpus feature names remain usable.

The stage study supplies GOLD type and feature prefixes solely for conditional
measurement. A real planner must use its OWN predicted state; no benchmark,
gold query, oracle type or feature history may enter production prompts. Validate
selected symbols and literals against the same schema snapshot before compile.

## Confidence and refusal

A proposed stage policy maps static stage classes (support, type, feature,
operator, value, relation, output, verification) to finite probability/margin
thresholds and records all distributions/receipts. Validate finite numbers and
exclude bool coercion. Keep the weakest decision evidence, not an invented
whole-query probability. Unknown/unmeasured stages retain the existing gate;
no global threshold reduction. Explicit ambiguity, unsupported and low-confidence
states return no query. Error/usage reports stay sanitized, and a failed call
remains an attempted call with unknown usage when no receipt is available.

The development grid suggests different thresholds for support versus type and
feature. It is NOT an approved production policy: family cross-validation covered
few cases and oracle histories, not full predicted trajectories or adversarial
features. No threshold from the study is installed into SemanticParser.

Full capability context improves selective acceptance but costs much more input.
Before optimizing it, measure deterministic relevant capability retrieval with
recall and unsupported-request tests; do not silently omit a required capability
or treat an omitted feature as absent. Independent decisions may share one
request; choices depending on a predicted feature/operator stay sequential.
Compare Noul feature relevance with next-feature choice as a separate controlled
experiment, without assuming binary questions are better.

## Implementation and evaluation gates

1. Freeze a newly authored versioned NL/native-gold benchmark and independent
   intent/native review before grading a revision. The observed v2 heldout is
   regression-only. Separate calibration/evaluation families; do not use the fresh
   evaluation partition for prompt/policy selection. Include ambiguous/unsupported
   contrasts, role/direction/projection, negation, absent annotations, retrieval
   collisions/misses, fourth-constraint overflow and unsupported regex/aggregation.
2. RED-first test the optional strategy against real tiny TF and BHSA paths;
   prove bounds, sentinel identity, actual schema context, termination, no gold
   leakage, malformed responses and unchanged default strategy.
3. Use versioned development diagnostics to calibrate the complete predicted
   trajectory, including false confident support and feature/operator/value errors.
   All tested model variants retain complete cost/error ledgers and model IDs.
4. Evaluate the frozen revision on the fresh benchmark once, with native projected
   equivalence and independently inspected semantic intent. Report usefulness,
   wrong supported emissions, latency and cost together. Isolated correct stages
   cannot establish parser quality.
5. Exact-head relevant suites and logically independent adversarial review precede
   merge. Default use stays prohibited until fresh usefulness/safety/cost gates pass.

The concrete implementation and benchmark freeze are a follow-up to this research
rather than a prompt patch folded into a diagnostic study. Explicit Jev 1.14
model-version support/comparison is separately tracked in #50; keep the 1.13
study immutable and never silently substitute a preview response.
