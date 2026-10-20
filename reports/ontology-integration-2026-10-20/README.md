# Optional ontology integration (#60)

OntologyParser/load_catalog expose the measured metadata path as an explicit
opt-in package feature. Caller-selected XML snapshots can grow without concept/
feature registry edits; native symbols are validated against the actual full
schema. Catalog digest/revision/source/version/schema/dispositions and per-stage
complete/retrieved/omitted context diagnostics are preserved in the result.

[Replay](replay.json): all 14 historical #59 ontology trajectories / 134 actual
model request structures, distributions, statuses and emitted query/projection
reproduce identically with the public parser. There are no new model calls or
fresh quality claim. Private sorted JSON did not preserve mapping insertion order,
so equality is structural rather than original wire-order proof. Original pilot
and its 7/10 results, imperative regression and cost increase remain immutable.

The growing-catalog overflow path is additional resource behavior, tested with
synthetic catalog additions: scope first, then retrieve complete matched-target
sets by request/label tokens, or omit optional descriptions and expose the reason.
No native option is removed. This path is not claimed to improve semantic quality.
#57 remains the fresh usefulness/safety gate; no model/parser default changes.

The [design](../../docs/design/issue-60-ontology-context.md) records RED/implementation
and installed-wheel once-only smoke protocol before inference. No ontoTF package,
legacy release machinery, HTTP ontology fetch or second executor is added.

## Installed-wheel live smoke (once only)

[Smoke artifact](wheel-smoke.json) records exact source 4126a4f, wheel digest,
synthetic fixture source hashes and catalog digest, all 27 API attempts, five
case results, usage/errors/latency. The wheel ran outside the checkout with
Jev 1.14.0 / SDK 0.7.4, no retries. It returned the intended nonempty feminine-
singular noun result (node2); ambiguous complements, unsupported per-phrase
counting and a named missing annotation all withheld queries safely.

The additional positive containment case FAILED with unsupported/no_candidates.
All five calls on that trajectory used unmapped scopes, so no added ontology
context was sent there. No rerun/replacement, prompt tuning or claim of complete
smoke success. Native/SDK tests and the historical BHSA containment replay pass,
but this wording/fixture/model trajectory is a preserved live usability failure;
#57 must investigate coverage before any quality/default recommendation.

All 27 calls have complete returned usage and no API errors: 24,096 input /
1,987 output tokens, 9.214 s summed measured backend time, estimated $0.001012032
at the rechecked $.042/M input/free-output rate. Full accounting was saved after
each call before another request. The live runner correctly exited failure for
the containment miss; that result is not reclassified as a passed positive.

The local package feature is explicitly opt-in and preserves the old measured
request path. It is not a release/default recommendation or proof that growing
ontology coverage solves structural planning. The overflow retrieval path remains
deterministically tested only, not a new quality estimate.
