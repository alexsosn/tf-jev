# Fresh evaluation of the ontology-enabled candidate parser (#57)

**The frozen usefulness gate fails: 5/13 correct positives, versus at least 11/13
required.** All seven negatives safely withhold queries, and no emitted query is
wrong in this sample. Keep Jev and the current no-default/no-release recommendation.
The concrete next repair is predicate/role scope (#64), not a provider change or
lower global confidence threshold. Alias drift is separate #63.

## Frozen setup

- Inference source d0af0c8; production code unchanged from main f757526.
- OntologyParser, GroundedPolicy final .8/.2 gate, Jev1.14.0, SDK0.7.4,
  TF13.1.0, no retries, once per case in fixed ID order.
- Historical licensed ontoTF XML snapshot 4d1112b9c9ec077e3dbf6cd6150b69ac6e53d3b9,
  digest in comparison.json. Pinning avoids confounding catalog growth with parser
  evaluation; ordinary catalog use remains data-driven.
- [Twenty new requests/native gold](../../benchmarks/candidate-v1/README.md), with
  thirteen nonempty supported and seven ambiguity/unsupported/schema/conflict
  negatives. Native type/feature/slot oracles and full gold projection semantics
  were independently adjudicated BEFORE inference. Exact request and exact gold
  text overlap with prior benchmarks are empty, but feature families overlap:
  this is fresh-request evidence, not family-heldout or population reliability.
- All116 native source hashes, full schema, fixed input digests and native gold
  checked before creating the model client. No gold/rationale sent to parser/model.
- Case19 deliberately replaces sp feature description with a synthetic hostile
  note. Native domains/execution remain unchanged; base native key AND effective
  feature-description digest distinguish it from actual corpus-authored metadata.
- No retries, replacement trials, post-result changes, dropped cases, changed
  gold, prompt tuning or production fixes during collection. Every numeric API
  observation is saved atomically before a further call; raw contexts/candidates
  remain private. [Protocol](../../docs/research/issue-57-fresh-evaluation.md).

## Results

| Measure | Observed |
| --- | ---: |
| Correct supported intents and complete native results | 5/13 (38.5%) |
| Positive emissions | 5 |
| Wrong emissions | 0 |
| Correct among emitted positives | 5/5 |
| Safe negative withholding | 7/7 |
| API calls | 179 |
| Input / output tokens | 609,333 / 63,774 |
| API errors / unknown usage | 0 / 0 |
| Summed backend time | 48.107 s |
| Estimated model cost | $0.025591986 |

The five successes are masculine-plural adjectives, emphatic substantives,
reversed adjective/substantive output after native adjacency, a verb predicate
with literal prs=absent, and clause number<5. Four match exact gold text; the
reversed adjacency uses inverse node roles and relation direction with the correct
ordered projection, independently adjudicated as the same complete meaning.
Native equivalence is never accepted based on equal counts alone. All thirteen
raw expected sets were independently re-derived after collection and all five
emitted complete sets/semantics rechecked. [Audit](independent-audit.json).

The metadata-injection positive ABSTAINS and therefore fails its positive task;
it is not counted as an eighth safe-negative success. No malicious all-phrase
query is emitted, but one example does not establish injection robustness. The
other seven negatives withhold; status category correctness is separate from
safe withholding. Zero observed wrong emissions on this small set is not a
safety/generalization guarantee.

[Comparison](comparison.json) preserves case results and effective metadata
identity; [summary](summary.json) aggregates canonical per-case *-calls.json
records once. Do not double count receipt totals in comparison.json.

## Failure evidence: distinguish wrong proposals from gated correct ones

All eight failed positives reach final verification. Three have correct complete
candidates but final yes below .8: exact lexeme .70, adjective-before-substantive
adjacency .76, and metadata-attack first-person verbs .79. These are failures of
accepted coverage, not accepted successes or proof that a lower gate is safe.

Five have incomplete/wrong candidates:
- First-person singular verbs omit singular; yes .61 is below gate. The raw
  broader candidate contains 1,026 extra plural words. Lowering admission enough
  to accept it would be a correctness regression.
- Imperative containment proposes two clause nodes with same slots, no imperative
  condition and both columns; fidelity rejects it.
- Exclusion drops the conjunction witness predicate, expressing no words at all;
  fidelity rejects it.
- Substantive + qere-present becomes qere-present AND sp-present, losing the
  required substantive value; fidelity rejects it.
- Adjective + missing qere becomes sp-absent, losing the intended feature/node
  condition; fidelity rejects it.

These are actual code/prompt/distribution/candidate observations, not a conclusion
from abstention counts. #64 owns a scoped, bounded research/RED-first repair using
this now-observed set only as development/regression evidence. The final gate,
ambiguity handling, native compiler and Jev backend remain unchanged here.

## Installed-wheel diagnostic appendix (NOT fresh score)

[Diagnostic](diagnostic.json) ran outside the checkout against an exact wheel,
new synthetic native TF fixture and tiny local catalog, each case once. It
preserves the prior 2026-10-20 containment failure and does not replace it. This
new dated observation is diagnostic, not a fresh or favorable repeated trial.
All question/options/selected distributions were retained privately; public data
contains code-authored stage IDs, positional numeric probabilities and accounting.

| Case | Native expectation | Observed |
| --- | --- | --- |
| Original containment wording | phrases10,12,13 | unsupported/no_candidates — FAIL |
| Annotation presence including empty strings | words1,2,3,4 | correct candidate, final yes .65 — FAIL |
| Missing annotation, distinct from empty string | words5,6,7,8 | correct native result — PASS |
| Unsupported regex | withhold query | unsupported — PASS |

Containment trace now explains the failure: relation shape, parent phrase type,
then part-of-speech feature sp selected for that parent (.49; attested_on_type=false),
equality and count1. The phrase/sp domain is empty, so value selection stops before
planning the word witness. This is direct parent/witness constraint transfer;
no ontology payload was added on those scopes. The old trace lacked questions,
so this new evidence does not claim to reconstruct its unknowable exact choices.

Do not globally remove unattested features: legitimate annotation-absence
predicates need them. Do not silently skip the failed predicate. Recover correct
scope in bounded planning and test it through native data. Presence's correct
candidate explicitly includes empty-string nodes; refusal is a real usability
failure, not a passed positive. Missingness and regex smokes pass. The appendix
records every failure without rerun or changing the parser.

Diagnostic accounting: 18 attempts, 15,129 input / 1,442 output tokens, all usage
known, zero API errors, estimated $0.000635418. Fresh study and diagnostic combined:
197 calls, $0.026227404 model cost. Official $.042/M input/free output price rechecked
2026-10-28. CPU/schema extraction, native execution and package build time are
excluded from model cost/backend latency. No runtime speed/default claim.

## Reproduction and next gates

The checkout-only scripts.candidate_evaluation requires TF_JEV_LIVE=1 AND --live,
new output/private directories, exact SDK/TF versions, frozen input hashes, full
native source verification and native gold validation. Re-running creates a NEW
observation; never overwrite or reinterpret this recorded once-only study as
fresh after tuning. Production package/IR/compiler/defaults are unchanged.

#57's evaluation is complete, and its usefulness gate failed. #64 must research
scope repair before implementation; #63 separately refreshes the now-changed
jev-latest alias contract without changing explicit pins/defaults. A later parser
revision requires new independently adjudicated native-gold requests for any
quality/default/release claim. This study's outputs are now observed evidence.
