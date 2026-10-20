# Issue 56: opt-in production extraction

The semantic development trajectory is the extraction target. Keep legacy parsers,
Jev 1.13 default, all frozen evidence and compiler semantics unchanged. Introduce
CandidateParser in tf_jev.candidate, using GroundedPolicy's global .8/.2 gate only
for complete-candidate fidelity. Reject stage-specific gates rather than silently
ignoring them. Every earlier decision is a bounded proposal; retain its actual
probabilities and weakest-proposal confidence. No calibrated quality claim.

Reuse existing schema grounding, retrieval, limits, receipts, typed IR and native
compiler. Extract only the semantic strategy, not the experimental variants. The
verifier receives the exact proposed IR and deterministic complete explanation,
original request, grammar and untrusted-data contract. Validate before explaining.
Correctly disclose native inequality's inclusion of missing annotations and
presence's inclusion of empty strings. No executor or model-generated query text.

Before implementation: production import/native-path tests must fail. Then test
weak proposals versus weak/negative final verdict, native multi-condition results,
parent/witness scope, bounded failures and actual SDK transport. Replay recorded
semantic requests/distributions against production extraction without inference.
Independently audit native results and actual annotation meanings. Finish with
installed-wheel live Jev smoke tests, full exact-head suite and adversarial review.
All adaptive development scores remain development evidence; fresh evaluation is
required before changing defaults or making general usefulness claims.

Installed-wheel smoke protocol (frozen before inference): use the existing native
synthetic conformance corpus with honest added feature descriptions (sp part of
speech: verb/subs/adjv/prep; gn grammatical gender m/f; nu grammatical number sg/pl).
Run once each: feminine singular substantives (word 2); phrase nodes containing a
verb (10,12,13); unresolved complements; verb count per verse (unsupported); absent
missing_feature_jev56='yes' (schema mismatch). Jev 1.14.0, no retries, 30-second
timeout, at most $.01 known usage, independent of the research budget. Execute
accepted queries natively and compare projected node IDs to fixture data. Record
all failures without replacement; this is packaging/usability smoke, not quality
or heldout evidence. The earlier adaptive BHSA development study remains separate.
