# Corpus-aware bounded planning research (#48)

## Prior evidence and external comparison

The frozen #46 trace identifies support/shape, node type and predicate count as
blocking stages. Wording alone raises confidence in wrong regex/negation choices.
The current parser's first payload lacks the schema and precise operator subset.
The v2 heldout has already been observed and is unavailable for fresh evaluation.

Inspected pg-jev master at e3450d44f7f6745aa2d728c9289b9ca4a6feda9a:
[question construction](https://github.com/realZachi/pg-jev/blob/e3450d44f7f6745aa2d728c9289b9ca4a6feda9a/sql/jev--0.2.1.sql#L105-L124),
[SQL wrappers](https://github.com/realZachi/pg-jev/blob/e3450d44f7f6745aa2d728c9289b9ca4a6feda9a/sql/jev--0.2.1.sql#L497-L536),
[regression mock](https://github.com/realZachi/pg-jev/blob/e3450d44f7f6745aa2d728c9289b9ca4a6feda9a/test/mock_api.py).
It classifies concrete rows within user-written SQL, not NL into SQL. One shared
JSON state contains rows and a condition; each row gets its own Noul question.
Human SQL owns structure, joins, arithmetic, projection and execution. Batching,
connection reuse and caching improve throughput, not planning accuracy. Its .5
boolean threshold differs from our .8/.2 sequential planning gates. Its narrow
reported live row accuracy is not a versioned NL-query compilation benchmark;
checked-in CI uses mock answers. We can borrow concrete grounded questions and
independent batching, not infer structural parser quality from those claims.

## Preregistered development experiment

Freeze this protocol and helpers before live inference. Use canonical FIRST and
LAST DEVELOPMENT cases in each of the eight v2 families, never heldout cases.
Two repetitions, fixed case/variant/stage order, no replacement observations after
errors. All 116 BHSA source hashes and native TF 13.1.0 must match #46 before any
model client is constructed. Pin Jev 1.13.0 / SDK version in output. Native replay
of selected supported gold count/signatures precedes inference.

1. **control support:** exact unchanged first parser request (intercept and stop
   before executing a backend). It receives only NL, no gold.
2. **grounded support:** same five classes and order with precise supported
   predicates (literal equality/inequality, presence/absence, integer comparisons,
   up to three alternatives), two-atom relations, output projection, one embedded
   exclusion, and explicit unsupported regex, feature-to-feature comparisons,
   aggregation and top-N. Supply complete bounded type/feature/edge inventories
   and corpus-derived descriptions. No feature values or passages.
3. **grounded type:** choose the first atom's type with slot/non-slot role plus
   attested feature names. No predicted shape/type is supplied; this is an
   isolated first-role decision, not a sequential parser rollout.
4. **next feature:** given the correct first-atom type and each correct prefix of
   its feature names, choose any remaining requested feature or DONE. All corpus
   feature names remain candidates, including those absent on this type because
   presence/absence predicates can intentionally test absent annotations. Metadata
   names/types/descriptions and attested-on-type flags are context. There is no
   numeric count decision. The conditioning history comes from frozen native
   development gold, is explicitly oracle-conditioned, and cannot count as parser
   success. Any order of the remaining features is correct; DONE is correct only
   when all required features have been selected. Values/operators are not tested.

No parser, compiler, schema, backend or default threshold revision in this study.
Full schema inventories are bounded by 255 symbols/options, 64 KiB of serialized
request, with refusal rather than truncation. Corpus metadata and NL are untrusted
JSON data; original symbols resolve locally through opaque option labels. Partial
schemas are refused. Payloads contain schema metadata only, no corpus passages or
unbounded value lists. Error reports use static kinds and numeric positions only.

## Stage-specific calibration protocol

For each grounded stage, tabulate the fixed grid probability thresholds
[.5,.6,.7,.8,.9,.95,.99] and winning margins [0,.1,.2,.3,.5]. An accepted decision
must match the independently derived acceptable option set. Failed calls remain
scheduled non-acceptances with unknown usage, never dropped from denominators.

Report the original .8/.2 gate and leave-one-family-out policy selection: fit on
other families only; require zero observed training errors and at least two
DISTINCT accepted case IDs; maximize accepted observations, then prefer higher
probability and margin thresholds. If no policy qualifies, abstain on the entire
excluded family. Evaluate the selected policy only on that excluded family. Keep
replicates of a case together. Publish thresholds and accepted/wrong/total counts
for each fold, not just the pooled best grid. This is small-sample selective
classification evidence, not statistically calibrated probabilities. A single
accepted wrong decision disproves safety of that fitted policy on this diagnostic.
Even zero observed errors cannot establish production safety.

Costs: once per attempted API call, returned input/output usage, latency and
sanitized failures. Unknown failed-call usage means unknown complete estimated
cost; known returned usage may be separately estimated at the historical study
list rate (.042 USD/million input, free output), not represented as current price
or invoice. SDK retries and shared schema/native work are excluded explicitly.

## Design decision gate

Persist measured conclusions before choosing implementation. If the grounded
stages still confidently fail or have inadequate coverage, retain the current
no-go and specify the next experiment rather than shipping a prompt/threshold
patch. If promising, a follow-up parser design must cover operator/value planning,
role/direction/projection, verification and bounded termination; schema-grounded
feature selection alone is insufficient. Binary relevance is an alternative to
measure, not assumed superior after #46's failed binary shape probes.

Before grading ANY revised end-to-end parser, freeze a newly authored native-gold
benchmark with separate calibration/evaluation families and a logically independent
semantic/native review. No revised parser is graded here, so no new untouched
benchmark is claimed. The old heldout remains regression-only. Fresh evaluation
must include ambiguity, unsupported constructs, multi-constraint/role interactions,
retrieval misses and false-confidence negatives. Default use stays prohibited
until a fresh usefulness/safety/cost experiment passes. Deterministic model mocks
establish helper integrity only. Research helpers follow observed RED-first tests,
exact-head full checks and logically independent adversarial review.
