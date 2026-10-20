# Explicit Jev model versions and preview (#50)

## Research (before implementation)

Current official [model table and aliases](https://docs.typesafe.ai/models.md),
checked 2026-10-20, list version IDs jev-1.13.0 and jev-1.14.0, with latest ->
1.13.0 and preview -> 1.14.0. The authenticated SDK models.list() endpoint advertises
both aliases. That inventory alone does not prove resolution; live synthetic
Choice/Noul requests must verify the returned model field. Pricing is the same
.042 USD/million input, free output. Do not infer that a new model fixes planning.

Actual typesafe-sdk 0.7.4 system_one accepts a string model argument and exposes
model/usage in custom response decoding. No SDK upgrade or new transport is
required. Current JevBackend permits latest/preview but then checks response.model
against a single DEFAULT_MODEL, so the documented preview is rejected and explicit
1.14 is refused before transport. Existing default/studies intentionally pin 1.13.

## Minimal plan/design

Replace the single-version request allowlist with an immutable researched mapping:

| Request | Required response |
|---|---|
| jev-1.13.0 (default) | jev-1.13.0 |
| jev-1.14.0 | jev-1.14.0 |
| jev-latest | jev-1.13.0 |
| jev-preview | jev-1.14.0 |

Keep DEFAULT_MODEL at 1.13.0. Do not accept arbitrary version prefixes, silently
follow alias drift, retry a different version or relabel receipts. Each explicit
version must match itself; each alias must match its researched resolution.
Unexpected response IDs fail with sanitized BackendError('response'). Unknown
requests fail configuration before constructing a client/call. Model IDs are
backend-specific and remain outside schema/IR/compiler and parser policies.
One private expected-model field is sufficient; no mutable registry/settings,
model autodiscovery machinery, arbitrary override or new confidence mechanism.

RED-first real-SDK MockTransport tests must cover the full request/response matrix,
unchanged default and latest behavior, explicit 1.14, preview drift to 1.13/future,
wrong/secret server IDs, immutable resolved receipts, configuration failure and
caller-owned client lifetime. Use a real schema-derived bounded Choice -> local
Predicate -> deterministic compiler -> native tiny TF query as an integration
witness. Preserve answer/probability/usage/error/log validation unchanged.

## Preregistered optional live work

1. One synthetic batch of Choice and Noul for explicit 1.14 and one identical batch
   for preview, reporting requested/resolved IDs and complete returned usage/errors.
   No replacement observations after failure. These test API/version contract,
   not corpus semantics or model quality.
2. One complete grounded-v1 DEVELOPMENT run (12 requests) with pinned 1.14,
   GroundedParser strict default policy, unchanged production planner/prompts and
   the same full source-verified BHSA schema as #51. Compare descriptively to its
   already-frozen 1.13 strict calibration report. No policy/prompt tuning, new
   heldout calls, canonical v2 calls, data rewrite or fresh generalization claim.
   This dataset is already observed; the result is development evidence only.
   Private query/projection inspection must distinguish intended meaning from
   coincidental native result equality. Preserve failed attempts and unknown usage;
   meter once per API call and keep public artifacts free of raw request/query/
   prompt/option/passage/credential data. Versions/source/dataset/schema/code and
   list-estimated cost/latency/errors are explicit, with retry/invoice exclusions.

Reuse existing benchmark loader, evaluator, StageMeter and RecordingParser; no new
benchmark framework or production parser revision. Default 1.13 artifacts remain
byte-identical. Any future parser quality/default decision still needs fresh
independently reviewed native-gold evaluation. Exact-head complete tests/types/lint,
opt-in live contract evidence and logically independent adversarial review precede
merge; no release usefulness claim follows from model-version support alone.
