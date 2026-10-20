# Jev integration repair: adaptive development evidence (#56)

Jev remains the backend. The earlier failures established that our integration
failed, not that Jev was intrinsically incapable. CandidateParser is a separately
opt-in prototype; default parsers/model remain unchanged. No alternative-provider
implementation, dependency or paid call was made.

## Observations and correction

The old planner sent a roughly 7,000-token full inventory/history to every stage.
Removing context indiscriminately made type decisions worse: predicted atom state
and indirect JSON descriptions primed native *_atom types. Controlled type probes
recovered correct types with plain native names and compact, actual type/feature
capabilities. Retaining first-role type and asking explicitly about the witness
corrected a separate returned-parent versus constrained-child confusion.

The old feature decision asks for ANY required remaining property but uses an
exclusive-choice .8 gate. Several equally valid required properties split the
probability mass. Ungated diagnostic rollouts exposed complete correct morphology
plans hidden by early admission gates. These diagnostic hypotheses are NOT
accepted successes. Abstract independent feature checks and concrete predicate
checks introduced false extra constraints and were rejected as solutions.

Other actual prompt defects: alternative counts did not name the current property
and node; structural routing confused output columns with witness nodes; raw IR
used unexplained feature/relation codes in final verification. The extracted
strategy uses explicit local scope and a deterministic explanation of the exact
validated candidate. All bounded intermediate choices are proposals; only final
complete-candidate fidelity retains .8 probability/.2 margin admission. This is
an explicit changed policy, not improved calibrated certainty. Weakest-proposal
confidence and all alternatives remain visible. No benchmark phrase/symbol rules,
gold context, arbitrary generated query text or second execution engine were added.

## Results and limits

All inference used Jev 1.14.0, SDK 0.7.4, TF 13.1.0 and source-verified full BHSA
2021 schema (116 source hashes in each trajectory report). All iterations were
fixed-order, once per frozen phase, using DEVELOPMENT requests. Additional
[relation/schema witnesses](../../benchmarks/jev-repair-v1/README.md) were frozen
before their first inference. Earlier observed cases were repeatedly used to
adapt the design: these results are heavily selected development evidence,
**not a fresh/generalization score**. Prompt changes are not statistically isolated
causal effects. Previous no-go reports are preserved byte-for-byte.

| Phase | Supported native-equivalent / eligible | Safe negatives |
| --- | --- | --- |
| Original control | 1/8 | 4/4 |
| Focused / literal context | 0/8 each | 4/4 each |
| Attested type capabilities | 1/8 | 4/4 |
| Ranked / concrete checks | 2/8 each | 4/4 each |
| Verified / routed | 3/10 each | 6/6 each |
| Scoped | 2/10 | 6/6 |
| Joint whole-candidate admission | 4/10 | 6/6 |
| Semantic candidate explanation | 6/10 | 6/6 |

The final phase emits complete masculine-singular-substantive and feminine-plural-
adjective morphology, Time phrases, nifal words, an integer clause filter, and
phrases containing a verb (parent-only projection). No emitted query has different
native projected results from its gold. Failure cases remain: exact lexeme,
negative containment, and ordered adjacent pairs. All six negatives withhold a
query; safe withholding does not imply correct negative-category classification.
Native equivalence alone is insufficient: independently check requested types,
annotation meanings and raw word/slot membership, including the verbal-stem
constraint's relationship to part of speech. See production replay for audit.

[Research protocol](../../docs/research/issue-56-jev-failure-repair.md) records each
adaptive phase before inference; [extraction contract](../../docs/research/issue-56-candidate-parser.md)
records RED-first production gates. Reports contain positional numeric choices,
usage/errors/latency and static case/stage IDs; raw prompts/options/predictions
remain private for direct review. Trace is counted once per call, not again via
its duplicate attempt record. The diagnostic phase intentionally disabled gates;
its five equivalent hypotheses must never be counted as accepted successes.

## Accounting and packaging

[Summary](summary.json): 724 API calls, 1,966,306 input and 234,562 output tokens,
263.241 seconds summed backend latency, no API errors or unknown research usage.
At the checked $.042/M input/free-output price: **$.082584852** research model cost.
CPU, local extraction/native execution and packaging time are excluded. Two local
storage interruptions preserved in-memory observations before resuming; no inference
was repeated. The predicate-probe coding failure preceded any API call.

The isolated installed-wheel [smoke](wheel-smoke.json), run outside the checkout,
passed once-only live NL morphology and containment positives with nonempty native
results, plus ambiguous/unsupported/schema-mismatch safe negatives. Its report
assembly failed on the .tf cache directory AFTER all five comparisons passed;
receipt counters were lost. Smoke usage/latency/cost are explicitly **unknown**,
separate from research accounting. No calls were repeated to replace outcomes.
This is synthetic native packaging evidence, not an additional quality benchmark.

A fresh, independently adjudicated native-gold evaluation must precede any revised
usefulness/default/release recommendation. Keep Jev and test remaining negative
containment, exact-value retrieval, adjacency, ambiguity and prompt-injection
failure modes there; avoid adding infrastructure without demonstrated user need.

## Independent native audit

[Direct raw oracles](native-audit.json) derive accepted results from requested
object-type sets, actual feature values and oslots membership, independently of
the compiler and gold query. Counts are 57,057 masculine singular substantives;
312 feminine plural adjectives; 4,079 Time phrases; 4,145 nifal verbal words;
167 clauses numbered above 12; and 73,459 phrases containing verb words. Every
emitted native projected set equals its raw oracle. Actual metadata identifies
vs as verbal stem, and every word with vs=nif has sp=verb in this exact corpus;
the emitted stem-only predicate therefore preserves that request's verbal
restriction here. No generic compiler/parser rule infers this dependency.

[Production replay](production-replay.json) checks all 16 original requests,
119 question/context/option structures, recorded distributions and resulting
statuses/query/projection, then re-executes accepted queries natively. Private
JSON retained array/string content but sorted mappings, so this is structural
request equality, not proof of original wire key insertion order. The explicit
missing/empty explanation correction is also covered by deterministic native
tests; none of these recorded final candidates used those operators.
