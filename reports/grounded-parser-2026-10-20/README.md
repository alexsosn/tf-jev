# Predicted grounded parser: fresh whole-trajectory evaluation (#51)

**Measured no-go: the revised planner solves 0/12 supported fresh evaluation
requests.** It safely withholds all nine negatives and has zero API errors, but
no correct query is emitted. No default or release recommendation. The separately
opt-in `GroundedParser` is an experimental implementation, not a validated NL API.

## Freeze and independence

New dataset [grounded-v1](../../benchmarks/grounded-v1/README.md) was frozen and
independently reviewed in `64bdf50` BEFORE implementation. Its file SHA256 is
`0a9f8d1a1808b8cfd07a1815bfcaba3ae34381d55dec3475039e1ebbe32f7b27`.
It reuses the nl-tf-v2 serialization format, not the old observed dataset. Native
TF gold and an independent NL-derived raw annotation/slot/edge oracle agree on
all 20 supported counts/signatures; all 13 negative intents were reviewed against
actual capabilities/ambiguity, with absent type/literal checked in native data.
No claim of external blinded authorship or representative population sampling.

The [protocol](../../docs/research/issue-51-grounded-parser.md) preregisters three
policies and a complete calibration-then-evaluation procedure. Production source
`35eb04e` was frozen before calibration. Each policy uses its OWN predicted state;
no gold types/features/history, benchmark examples or gold queries enter prompts.
Full suite passed before the evaluation freeze: 587 passed, 41 opt-in skips,
Ruff and strict mypy. Corpus is the same source-verified full BHSA 2021 snapshot
as #48 (116 hashes; full schema key
`4a777cf2dc316633c062e89a99580bf1f19b9c7aa2713892779b11a4c60a442c`).
Jev 1.13.0 / SDK 0.7.4 / native TF 13.1.0 remain pinned.

Calibration: eight supported and four negative requests, each of three policies
once. All have zero supported successes and zero wrong emissions, so the
preregistered tie preference selects **strict**. Independent private prediction
inspection confirms all 36 outcomes have no query/projection. Selection and
artifact hashes were committed in [calibration-freeze.json](calibration-freeze.json)
at `6c5fe27` BEFORE the single heldout run. No subsequent prompt/threshold/code
revision or favorable replacement observation occurred. Production source is
identical between the calibration and evaluation source heads.

## Complete results

| Run | Supported equivalent | Safe negatives | API errors | Calls | Input tokens | Output tokens | Estimated USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Calibration strict | 0/8 | 4/4 | 0 | 24 | 202,345 | 6,234 | .008498490 |
| Calibration exploratory | 0/8 | 4/4 | 0 | 21 | 172,639 | 4,850 | .007250838 |
| Calibration guarded | 0/8 | 4/4 | 0 | 18 | 143,227 | 3,520 | .006015534 |
| Fresh evaluation strict | 0/12 | 9/9 | 0 | 52 | 457,086 | 15,651 | .019197612 |

The recorded JSON is authoritative for metering. Costs are returned-usage list
estimates at .042 USD/million input, free output, not invoices or complete SDK
retry billing. 115 attempted calls all have known returned usage, totaling
975,297 input tokens and **$0.040962474** excluding the separate wheel smoke.
Shared schema extraction, native gold/search and CPU are excluded from model USD.

Evaluation statuses: 20 low-confidence abstentions and one explicit unsupported
result; zero query/IR emissions. Conditional native validity/semantic precision
of emitted queries are **undefined**, not 100%. Supported usefulness is 0%; safe
negatives are 100%. Evaluation p95 parse latency is 3.443 seconds, including
refusals; mean returned-usage model estimate is ~$.000914/request. Cheap and safe
refusals do not pass usefulness. The preregistered >=70% supported equivalence,
>=95% emitted precision, >=95% negative safety, <=10s p95 and <=$.01/request gate
therefore fails regardless of latency/cost. No production default change.

Stopping stages show why isolated #48 successes did not establish a full parser:

| Run | Shape | Type | Feature | Operator | Verification |
|---|---:|---:|---:|---:|---:|
| Calibration strict | 7 | 2 | 1 | 1 | 1 |
| Calibration exploratory | 9 | 0 | 0 | 3 | 0 |
| Calibration guarded | 10 | 0 | 0 | 2 | 0 |
| Fresh evaluation strict | 12 | 2 | 1 | 2 | 4 |

These are last attempted static stage IDs, not adjudications that every winner
was wrong. Some full candidates reach verification but fail its gate. Intermediate
candidate correctness is not claimed. The full pipeline still exposes uncalibrated
operator/fidelity decisions and uncertain structure. Stage-local oracle accuracy
cannot be multiplied into an end-to-end quality claim. Do not react by globally
lowering thresholds or tune on the now-observed grounded-v1 evaluation.

## Implementation boundary and verification

`GroundedParser` supplies corpus/grammar context before support, corpus-native type
roles, predicted partial state and a complete typed candidate/projection before
fidelity. It replaces feature-predicate counting with schema feature or tagged
stop choices; a real feature named DONE remains distinct. After three predicates,
explicit stop is required; selecting a fourth refuses without dropping it. Compatible
operators, bounded literal/alternative retrieval, relation/edge direction, projection,
compiler and native execution remain shared. Context checks account conservatively
for escaped SDK-shaped JSON. `GroundedPolicy` defaults remain .8/.2; static optional
stage gates are validated finite experiments, not whole-query probabilities.

The legacy `SemanticParser` remains unchanged in behavior. An independent replay
against source at `02edbd1` compares complete serialized results AND every backend
request for 12 atom/relation/without strong/weak cases; all are identical. Full
legacy tests remain green. New deterministic tests cover real tiny TF execution,
parent/witness scope, a real DONE feature, fourth-constraint refusal, escaped-budget
and partial-schema refusal, finite stage policies, sanitized failures, fidelity
and full real-SDK MockTransport. Only request-bound labels select local typed
symbols; no model-generated TF or corpus passages. Research is outside src.

Public reports contain static case/stage IDs, bounded numeric diagnostics,
sanitized attempt errors, usage, latency, source/schema/model versions and hashes;
no raw request/prompt, native query, option description/label, passage or key.
Private inspection confirms all 21 evaluation predictions withhold a query and
projection. Full partition IDs, source/dataset identity, selection, accounting and
no-query metrics were independently reconstructed from artifacts.

## Autonomous installed-wheel smoke

Built the package and installed it with TF 13.1.0 / SDK 0.7.4 into a fresh virtual
environment; imports resolve to installed site-packages outside the checkout.
The typed console command against real BHSA (`--type word --eq sp=verb --execute
--limit 100000`) returns exactly **73,710** complete results, matching the independent
native oracle. The new live Python API against a saved synthetic TF corpus
abstains on the positive verb request (three calls, low confidence) and explicitly
rejects aggregation (one call). No query is executed from either NL outcome.
[wheel-smoke.json](wheel-smoke.json) records this honestly: **positive NL smoke does
not pass usefulness**, while packaging/typed CLI and safe negative behavior work.
It is not a successful model-quality demonstration or release-ready package.
Its separate 5,524 input / 336 output tokens (~$.000232008) are excluded above.
Wheel production source is `35eb04e`, unchanged in the final reviewed production
code; final CI also imports the grounded module without the optional SDK installed.

Follow the existing #50 explicit-version/preview work next to test a newer backend
without more planner infrastructure. Any future quality improvement must use
fresh reviewed evaluation; grounded-v1 is now regression evidence. Preserve these
failed measurements rather than overwrite them. Exact-head checks and independent
adversarial review are recorded on the PR before merge.

Reproduce with explicit exported credentials and NEW output paths (paid calls):

```bash
TF_JEV_LIVE=1 python -m scripts.grounded_experiment /path/to/bhsa/tf/2021 \
  --phase calibration --output /tmp/new-calibration \
  --private-review /tmp/new-private-calibration --live
# Inspect predictions/eligibility before freezing a policy and evaluating:
TF_JEV_LIVE=1 python -m scripts.grounded_experiment /path/to/bhsa/tf/2021 \
  --phase evaluation --policy strict --output /tmp/new-evaluation \
  --private-review /tmp/new-private-evaluation --live
```

[Artifact hashes](sha256.json) protect the frozen measurements. Replay is not a
fresh untouched score; different model runs can vary even under a pinned version.
