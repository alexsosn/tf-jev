# Explicit Jev versions and development follow-through (#50)

**The adapter now supports pinned Jev 1.14 and the researched preview resolution,
while keeping the default pinned to 1.13.** Live batches confirm both explicit
`jev-1.14.0` and `jev-preview` return validated model `jev-1.14.0`. Drift and unknown
versions fail; model IDs in receipts are never relabeled. This fixes a real public
configuration bug, not the measured NL parser usefulness failure.

## Research, RED and minimal implementation

[Official models/aliases](https://docs.typesafe.ai/models.md), checked 2026-10-20,
list latest -> 1.13, preview -> 1.14, both explicit version IDs and the same .042
USD/million input price (free output). Authenticated SDK model inventory advertises
both aliases; actual resolution is established by the live inference below.
Actual SDK 0.7.4 system_one accepts model strings, so no SDK upgrade, new transport
or backend registry was needed. [Research/design/protocol](../../docs/research/issue-50-model-versions.md)
was committed before implementation and measurement.

Old code allowed preview requests but required every response to equal 1.13, and
rejected explicit 1.14 before transport. Observed RED: **8 failed, 14 passed** in
new targeted tests. Replace the single-version allowlist with an immutable four-row
request/expected-response map and one private per-instance expected-model field:

| Request | Required response |
|---|---|
| jev-1.13.0 (default) | jev-1.13.0 |
| jev-1.14.0 | jev-1.14.0 |
| jev-latest | jev-1.13.0 |
| jev-preview | jev-1.14.0 |

No arbitrary prefixes/future IDs, automatic alias following, version retry or
fallback. Error/log/probability/usage validation and caller-owned lifecycle stay
unchanged. Twenty request/response combinations include wrong versions, aliases
returned as versions, future IDs and a fake secret server ID. Resolved receipts
remain frozen. An actual schema-derived bounded choice compiles to native tiny
TF with three expected verbs. Adapter suite: 56 pass. Complete suite/type/lint
and exact-head independent adversarial review precede merge.

## Preregistered live contract and development comparison

Frozen inference source `7b425a3ad99de2cec4a2e9f7410643b2496a6e7c`, Python 3.12.11,
SDK 0.7.4, TF 13.1.0. No replacement observation after failure. Two synthetic
shared-state Choice/Noul batches (one each for explicit 1.14 and preview) both
pass the answer/version contract: [contract.json](contract.json). Each returns
330 input / 53 output tokens; model resolution is 1.14. This demonstrates transport
and typed API compatibility, not corpus semantic accuracy.

Use the unchanged strict GroundedParser and all twelve grounded-v1 DEVELOPMENT
requests once. Full schema identity and all 116 corpus source hashes match #51.
Planner/policy/prompt source is byte-identical to its 1.13 inference source;
only the adapter model/version contract differs. Gold enters only scoring/private
inspection. No new heldout or old v2 calls and no tuning. This dataset has already
been observed: **development/regression evidence only**, not fresh generalization.

| Pinned model / run | Supported equivalent | Safe negatives | API errors | Calls | Input / output tokens | Estimated USD |
|---|---:|---:|---:|---:|---:|---:|
| 1.13 frozen strict calibration (#51) | 0/8 | 4/4 | 0 | 24 | 202,345 / 6,234 | .008498490 |
| 1.14 development | 1/8 | 4/4 | 0 | 25 | 209,403 / 6,269 | .008794926 |

The one 1.14 supported emission correctly returns clauses whose number annotation
is greater than 12. Independent NL/compiled-structure inspection checks node type,
strict integer comparison and output projection. A separate raw F.number filter
with F.otype clause membership (no compiler/search to derive it) reproduces **167**
clauses and the frozen projected signature: [independent-review.json](independent-review.json).
All eleven other private predictions withhold the query/projection. Native validity
and intent correctness hold for this single emission, not a population precision
guarantee. Different single runs/times and stochastic choices preclude a causal or
statistical superiority claim. The 1.13 control was not rerun or rewritten.

[Development JSON](development.json) preserves every attempted static stage,
usage, latency, sanitized error, version/source/dataset identity and complete
partition selection. Median/p95 parse latency is .460 / 3.314 seconds for this
mixed successful/refused set, versus .591 / 2.965 for the older 1.13 run. These are
descriptive samples, not a controlled performance claim. Model 1.14 solves only
12.5% of supported development requests here, which does not justify default use.
No fresh heldout score or release usefulness claim is made.

The two contract calls plus 25 development calls have complete known returned
usage: 210,063 input / 6,375 output, **$0.008822646** list estimate. SDK retry/invoice
billing and shared corpus/schema/native execution are not measured. Unknown
failed usage would remain unknown rather than zero; all these attempts succeeded.

## Autonomous installed-wheel smoke

Build and install the new wheel outside the checkout. Explicit 1.14 makes a live
schema-derived bounded value choice, constructs local typed IR, and compiles and
executes native TF: three expected verb nodes. The installed module reports 1.14
in its receipt and still exposes DEFAULT_MODEL=1.13. No model-generated query text
or corpus passage is involved. [wheel-smoke.json](wheel-smoke.json) anchors wheel
hash and source; its separate 326 input / 34 output tokens (~$.000013692) are
excluded from the experiment total. This verifies the bounded backend/native
mechanism and packaging, not autonomous NL query planning. #51's failed positive
NL smoke remains unchanged and disclosed.

Public numeric artifacts contain no raw request/prompt/query, option label/
description, corpus passage or credential. Private emitted structure and all
other abstentions were independently inspected, and source/schema/accounting/
selection/hash/disclosure checks were re-derived before review. Existing #11,
#46, #48 and #51 artifacts remain byte-identical. [SHA256 manifest](sha256.json)
protects this study.

Keep both parsers experimental and the default-model pin unchanged. The next
main-feature task is [#54](https://github.com/alexsosn/tf-jev/issues/54): research a
capable bounded planning backend before further orchestration infrastructure.
Any future parser quality/default decision still requires fresh independently
reviewed native-gold evaluation; grounded-v1 is now regression-only.

Reproduce through existing primitives: use `JevBackend(model="jev-1.14.0")`, the
unchanged `GroundedParser`, `StageMeter`/`RecordingParser`, `evaluate` on
`load_benchmark(Path("benchmarks/grounded-v1/bhsa-2021.json"))` with partition
`development`, and `account`. Verify all sources before corpus-dependent calls;
never pass gold into parser prompts. Export credentials explicitly and use new
artifact paths. Model runs are paid and can vary; repetition is not a fresh score.
