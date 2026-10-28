# Frozen candidate/ontology evaluation (#57), 2026-10-28

Research: current main f757526 contains the separately opt-in OntologyParser;
#59/#60 preserved seven successes on ten fresh-request pilot positives but those
cases are now observed. #60's extra synthetic containment smoke failed after five
calls, all unmapped, with no_candidates. Its durable accounting does NOT retain
questions/selections, so it cannot distinguish empty value domain, integer
extraction without a numeral, or another empty choice. Do not claim a cause.
Freeze a separate once-only diagnostic with full private request/distribution
traces; preserve the old failure and don't count this diagnostic as fresh quality.

Jev stays pinned to 1.14.0, SDK0.7.4 / TF13.1.0 / GroundedPolicy .8/.2 final gate.
Official models.md rechecked 2026-10-28 still quotes $.042/M input, free output.
Its jev-latest alias now resolves to 1.14 instead of our historical expected1.13;
this is separate contract drift, not grounds to change defaults or this experiment.
Use explicit 1.14 and preserve strict resolved-version validation.

## Plan frozen before inference

Use the exact production OntologyParser with the historical licensed ontoTF XML
snapshot 4d1112b9c9ec077e3dbf6cd6150b69ac6e53d3b9, digest pinned in runner. This
isolates parser evaluation from catalog updates; ordinary use remains data-driven.
No production code, thresholds, prompts, ontology payload or retrieval changes
while collecting or interpreting this set. No gold/rationales to parser/backend.

Twenty new requests: thirteen supported nonempty native-gold queries (new morphology
combinations, exact lexeme, both adjacency/output orders, containment, exclusion,
qere presence/absence, literal sentinel, integer comparison and one deliberately
hostile feature-description overlay) and seven ambiguity/unsupported/schema/
conflicting-instruction negatives. Reject exact prior request reuse and disclose
any semantic/family overlap; this is fresh-request evidence, not family-heldout
or a population reliability estimate. Freeze raw native type/feature/slot oracles,
counts/signatures and independent intent review before model calls.

For the metadata-attack case only, replace sp description in an immutable schema
copy with an explicitly recorded adversarial test note. Native domains and actual
TF execution are unchanged. Record original schema key PLUS the full effective
metadata SHA256 and overlay identity; don't call the injected metadata corpus-
authored or hide it under the unmodified native source manifest. Reload catalog
against that schema. No other per-case routing, lexical rules or gold assistance.

Run once per case in fixed ID order. Keep all refusals/errors/wrong emissions;
no reruns, retries, tuning, dropped cases or replaced gold. Public numeric trace
is saved atomically after each API attempt before another call; raw requests/
candidates are private. Stop after a transport/accounting/persistence error.
Verify all116 source hashes, actual full schema and native gold BEFORE creating
client. Budget ≤800 attempts and $.05 known usage, with conservative per-call
reserve; unknown failed usage explicitly separate. Model output remains bounded
labels only, native compiler/executor authoritative.

Primary metrics: independently adjudicated complete intent AND complete native
projected-result equivalence, selective coverage/wrong emissions, safe negative
withholding, exact text where appropriate, token/cost/latency/API errors/unknowns.
Prototype usefulness gate: ≥80% of 13 positives correct (≥11), zero wrong emissions
including negatives, all seven negatives safely withheld, complete accounting.
Even passing this small gate is not permission to change defaults/release. Failing
it retains no-default status, with focused follow-up issues only for demonstrated
failures. Equal counts alone cannot justify constraint omission or broadened values.

## TDD / review / smoke

Reuse existing Benchmark/evaluate/DurableTrace/Budget/native execution. Add a small
checkout-only runner, with RED-first explicit-live and frozen-input gate tests,
then native/oracle verification and complete relevant exact-head checks. No new
transport, evaluator framework or execution engine. Independent skeptical pass
adjudicates all fresh gold before inference, then all emitted semantics afterward.

Separate installed-wheel diagnostic appendix (not fresh score): use a new native
synthetic fixture, the historical tiny ontology meanings, once each for original
containment wording (expected phrases10,12,13), suffix annotation presence INCLUDING
empty strings (words1,2,3,4), missing suffix annotation (5,6,7,8), and unsupported
regex. Record whole private question traces and public numeric attempts, native
expected sets derived independently, individual failures unchanged. Retry0,
max100 calls / $.01 known-usage cap. Pin exact wheel/source/catalog/fixture hashes.
A positive refusal remains a failure; no second favorable replacement. Installed
wheel smoke runs after source freeze, before final review/merge.

## Pre-inference gate record

RED: runner import absent in tests/test_fresh_evaluation.py before implementation.
Explicit-live and frozen-input gates plus attack-overlay immutability/native-domain
checks now pass. Native benchmark SHA256:
c449f9080a5c575df139367399ec5d5a636b052160c5f1e523b07b55b3276a96.
All13 complete native/raw oracle sets are nonempty and match. Exact prior request
and exact gold-text overlap scans are empty; feature families still overlap.
Initially proposed feminine-plural proper names had zero results and were replaced
before freeze/inference. An older benchmark with list-shaped gold caused an
initial overlap-scanner format failure; corrected before artifact freeze, no API
calls or replaced observations.

Current alias drift is recorded separately in #63; explicit model/default unchanged.
The metadata fingerprint identifies the complete effective node/edge feature-
description pairs; base native schema key identifies native domains. Their pair
makes the hostile description overlay explicit rather than falsely corpus-authored.
