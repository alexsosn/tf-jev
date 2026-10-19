# Grounded stage planning and calibration (#48)

**Grounding improves selective acceptance in this small development diagnostic,
but does not establish a usable revised parser.** Keep the current no-go/default
prohibition. Proceed with the [experimental planner design](../../docs/design/issue-48-grounded-planning.md)
under the fresh benchmark gate in [#51](https://github.com/alexsosn/tf-jev/issues/51),
rather than globally lowering thresholds.

## Frozen experiment

Protocol commit `99ef1f0`; inference source
`f021bae1b878a118a3daabc9cf32133f8b0d7a99`. Model Jev 1.13.0, SDK 0.7.4,
TF 13.1.0, original full BHSA schema
`4a777cf2dc316633c062e89a99580bf1f19b9c7aa2713892779b11a4c60a442c`.
All 116 source hashes match #46. The 16 cases are canonical first and last
DEVELOPMENT requests in each of eight families. Two repetitions per fixed probe;
138 scheduled calls, 138 completed, zero backend/response errors. No new heldout
calls, outcome-driven replacements, production changes or end-to-end query grading.

The [protocol](../../docs/research/issue-48-grounded-planning.md) and helper design
were committed before live inference. Missing-module RED preceded helper code.
The API client was created only after all source, schema/budget and native gold
checks. One initial setup stopped at client configuration before any API call;
the shell had no exported credential. A second launch explicitly supplied the
already-configured local key without changing code or the planned observations.
The CLI does not automatically read `.env`. No credential is in artifacts.

## Results

"Accepted" uses the old .80 probability / .20 winning-margin gate.
Wrong means the selected option is outside the independently derived acceptable
set, not merely that the model expressed uncertainty.

| Stage | Correct top choices | Accepted | Wrong among accepted | Family-separated accepted | Family-separated wrong |
|---|---:|---:|---:|---:|---:|
| Exact control support | 24/32 | 10 | 2 | 8/32 | 0 |
| Grounded support | 24/32 | 20 | 0 | 18/32 | 0 |
| Grounded first-output type | 24/24 | 17 | 0 | 21/24 | 0 |
| Grounded next feature/DONE | 46/50 | 38 | 0 | 44/50 | 0 |

Grounded support gives the model the precise compiler subset and actual corpus
capabilities: 13 native node types with slot/non-slot roles and attested feature
names, 108 node features with dtype/description, plus edge names/descriptions.
It fixes the original missing-contract problem. Yet overall top-choice accuracy
remains 24/32, with changed error patterns: grounded shape still misclassifies
one containment case twice, one negated-containment case twice, and both ambiguous
cases twice. The old control confidently calls regex supported at .80 and .83;
the grounded version correctly selects unsupported for both repetitions. Higher
confidence is useful only alongside correctness; it is not a general accuracy win.

All 24 type choices are correct, but seven remain below the original gate. The
50 next-feature probes replace numeric counting with any remaining feature or
DONE. Their four wrong winners all occur for unconstrained returned parents in
containment/exclusion: the model selects the corpus `kind` annotation instead of
DONE, at .42–.48 probability. All four are rejected by the old and fitted gates.
This is direct evidence that parent/witness scope still needs attention.

Feature probes use correct first-atom types and correct feature-name prefixes
from existing development gold. They measure **oracle-conditioned local decisions**,
not autonomous parsing. They do not select operators/values, construct predicted
IR, test second-node roles, or prove whole-query verification. Type probes have no
predicted support prerequisite and do not include negative requests. No revision
of the parser was graded, so no fresh untouched end-to-end score is claimed.

## Calibration and limits

The fixed 7x5 probability/margin grid is fit separately by stage, excluding an
ENTIRE family and all its case replicates each time. Fit only zero-error policies
with at least two distinct accepted training case IDs; maximize coverage, then
prefer higher thresholds. Evaluate only on the excluded family. Every fold and
training count is in [analysis.json](live/analysis.json). No qualifying policy means
abstaining on that family. No observations/errors are removed from denominators.

Support folds select p=.90 (one .95), margin=.50. Type folds select p=.60–.70,
margin=.30–.50. Feature folds select p=.50–.60, margin=.30. Those different policies
retain more correct local type/feature choices without observed accepted errors
on these few cases. They are NOT calibrated whole-query probabilities, statistical
safety guarantees, or settings installed into the production parser. Full predicted
trajectories and fresh unseen evaluation remain necessary. Few cases, only two
repeats, correlated prefixes and fixed variant order prevent a causal/statistical
claim that one change alone accounts for the results. The grounded payload changes
schema context, grammar information and wording jointly.

## Cost and reproducibility

| Stage | Returned input tokens | Returned output tokens | Median call seconds | p95 call seconds |
|---|---:|---:|---:|---:|
| Control support | 15,692 | 2,240 | .261 | .403 |
| Grounded support | 222,444 | 2,240 | .339 | .518 |
| Grounded type | 190,304 | 3,600 | .343 | .554 |
| Grounded feature | 712,734 | 55,120 | .433 | .584 |

All 138 attempts have returned usage: **1,141,174 input / 63,200 output tokens**,
**$0.047929308** returned-usage list estimate at .042 USD/million input, free
output. This is not an invoice or complete retry billing. SDK retries, shared
schema extraction, native execution and CPU costs are not measured in model USD.
Grounded support alone uses about 14.2 times the control input tokens. Relevant
capability retrieval/batching deserve measurement before claiming cost benefits.

Current official [models documentation](https://docs.typesafe.ai/models.md),
checked 2026-10-20, confirms that price and lists 1.14 as a preview while latest
still resolves to 1.13. [1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
explicitly identify counting, indirection, irrelevant state and adversarial content
as risks; [Choice documentation](https://docs.typesafe.ai/primitives/choice.md)
confirms independent shared-state questions and the 255-option limit. Actual
SDK request/response boundaries were tested via mocked HTTP, then exercised by
all live calls. Preview support is separate #50, not a substituted model here.

[Observations](live/observations.json) contain static case/stage IDs, positions,
validated distributions, margins, per-attempt usage/model/latency and sanitized
error fields. They contain no raw request/prompt/query, option description/label,
corpus passage or credential. Source metadata/hashes anchor reconstruction.
[Native independent review](native-review.json) reproduces all 12 selected
supported gold counts/signatures from raw annotation sets and slot intersections,
without TF search/compiler to derive the answers. Separate native TF replay
verified the same gold before client creation. Independent reconstruction from
native inventories and gold structure checks all 138 positional decisions and
all calibration folds, rather than trusting family-to-shape mappings.

Review found two helper edge cases: an actual feature named DONE colliding with
the stopping sentinel, and the same case assigned to two calibration families.
Two observed RED tests preceded diagnostic-only refusal fixes. A saved real tiny
TF CLI test additionally checks native gold rejection before client construction.
The frozen live JSON is byte-identical and the full analysis recomputes unchanged
with the repaired helpers. Neither corpus hits the new refusals. No src parser,
policy, schema, backend, compiler or canonical benchmark file changed.

Reproduce from the frozen inference source, with an explicitly exported key and
new output directory (paid calls):

```bash
TF_JEV_LIVE=1 python -m scripts.grounded_planning /path/to/bhsa/tf/2021 \
  --output /tmp/new-grounded-planning --live
```

The exact-head full suite, SDK/mock/native checks and logically independent
adversarial review are recorded on this research PR. Artifact [SHA256 manifest](sha256.json)
protects the frozen evidence; future parser experiments must not overwrite it.
