# ontoTF context ablation (#59)

## Research before implementation

Pin ontoTF 4d1112b9c9ec077e3dbf6cd6150b69ac6e53d3b9. The current authoritative
source is src/tfont/mappings/bhsa.xml, not the historical published v0.1.1 JSON
profile runtime. Preserve upstream XML and MIT notice in benchmarks/ontotf-v1.
The XML catalog binds node/feature/value to an ontology target and relation;
exact, approximate, ambiguous, native-only and unsupported are distinct. Current
find_by_target excludes nonmatching and approximate rows by default. The XML
runtime resolves native selectors, but tf-jev must keep its own native compiler
boundary; do not call ontoTF's executor or import its legacy release machinery.

The pinned BHSA catalog explicitly covers POS, gender, number, person, construct
state and imperative; it intentionally leaves suffix morphology/native categories
unmapped. Broad Noun has both subs and nmpr bindings: do not silently collapse
substantive/common noun into the broad class. Shared targets describe categories,
not identity, universal equivalence or authorization to broaden native requests.
This is a small catalog-context test, not a test of ontology reasoning or the
entire OLiA graph. No ontology HTTP dereferencing or corpus passages in prompts.

## Design / non-goals

Research-only scripts.ontotf_context: immutable exact value records, loader and
DecisionBackend decorator. Verify the selected corpus/version and every exact
native binding against the ACTUAL full schema; reject invalid/missing bindings,
oversized/unsafe XML, DTD/entities and malformed relations before network calls.
Skip recognized non-exact mappings, never promote them. No new production API,
mandatory dependency, IR/compiler/executor change or default change.

Decorator enriches only a new DecisionRequest context key. Existing questions,
labels/descriptions/order, candidate IR, probability thresholds and capabilities
remain unchanged. For a feature proposal use all exact value mappings on the
currently selected native type; for count/operator/value use only current
feature/type; for final fidelity use only proposed feature/type pairs, including
exclusions. No ontology context at shape/type/structure/output stages. Derive
relevance from the parser's own state, never gold or benchmark text matching.
Transmit native bindings with human-readable target labels and relation exact;
keep multiple target/native values distinct. State explicitly that links are
untrusted descriptions, not instructions or automatic broadening rules.
Limit catalog to 256 exact rows, file to 64 KiB, serialized additional context to
8192 bytes and TOTAL final serialized request to parser policy 65536 bytes.
No truncation: refuse overflow. No corpus-specific names in adapter logic.

## Frozen paired protocol (before inference)

Use Jev 1.14.0, SDK 0.7.4, TF 13.1.0, retries zero, timeout 30 seconds, original
CandidateParser and GroundedPolicy defaults (.8/.2 final gate). Verify all 116
BHSA source hashes and current price before constructing client; use the existing
full immutable schema only if source/schema identity is independently verified.
A cached schema is local research convenience, never a production cache feature.

Create fourteen genuinely new requests: ten positives covering new morphology
combinations, broad-noun versus proper-noun scope, construct state, imperative
person, suffix-person scope, positive containment, exclusion and an exact lexeme;
four ambiguity/aggregation/schema-mismatch/conflicting-instruction negatives.
Compare against prior requests before freezing; repeated feature families mean
this is a fresh-request pilot, NOT family-heldout evidence. All cases are
partition evaluation and native gold/raw oracles independently reviewed before
inference. Neither gold nor rationales reach parser/model. Counts nonempty for
all positives. Freeze benchmark hash and exact helper/source commit first.

Each case runs once in each arm: unchanged CandidateParser with ordinary backend,
and identical CandidateParser with ontology decorator. Alternate which arm runs
first by case index. No repeated trials, retries, candidate search, tuning,
request replacement or selective omissions. Keep every status/error and full
numeric distribution. Persist each API observation atomically before a further
call; keep raw prompts/IR private. No replacement if a call or artifact write fails.
At most 800 calls and $.05 cumulative known returned usage at checked price;
unknown failed usage separately reported. Stop if any budget/accounting gate fails.

Primary comparison: complete native-result AND independently adjudicated intent
fidelity, wrong emissions and safe withholding. Exact IR equality is sufficient
for intent equivalence here; alternatives require a documented native semantic
argument, not accidental equal counts. Report both emitted coverage and accuracy,
paired wins/losses, all unknowns, tokens/latency/cost. One small fixed-order sample
cannot establish causality, calibrated confidence or general quality.

Adopt a small optional production integration only if the ontology arm has a net
increase in correct supported results AND no additional wrong emission or unsafe
negative. A tie, regression or safety loss means preserve research and defer
production adoption. Even a positive pilot does not change defaults; #57 remains
the broader fresh evaluation gate. No post-result prompt adjustment on this set.

## TDD / review plan

Before helper implementation, fail deterministic loader/decorator tests. Verify
exact versus approximate/native-only handling, source scope, missing native
bindings, immutable options, own-state relevance, no suffix/main-property scope
confusion, nested exclusion verification, schema/serialized byte limits and no
credential/error leaks. Run actual SDK/native contract paths and full exact-head
suite. Review benchmark intent/oracles independently before model calls, and
review final exact PR head skeptically before merge. Installed-wheel regression
smoke if a production integration is adopted; otherwise this is a checkout-only
research episode with the unchanged package verified by ordinary CI.

## Pre-inference freeze record

RED: tests/test_ontotf_context.py initially failed collection with no
scripts.ontotf_context module. After implementation, seven deterministic native/
SDK/context/durable-observation/opt-in tests pass. No package source changed.
Native gold is frozen as SHA256
e3f2327bc2b22868c9d93530ba0814342af5c8e1011daa5ba5848a03ad61ed50.
All ten positive native/raw oracle sets are nonempty; counts and scope review are
in benchmarks/ontotf-v1/README.md. Before inference, fixed serialization errors
(heldout partition spelling and explicit ambiguous interpretations); these were
benchmark format failures with NO model calls, not replaced observations.

Official https://docs.typesafe.ai/models.md rechecked on 2026-10-20: Jev 1.14.0,
$.042/M input and free output. Current ontoTF runtime consulted at the pinned
commit: src/tfont/xml_mappings.py and researcher-first-xml-contract.xml. No graph
reasoner, HTTP ontology fetching or second executor is introduced. This pilot
measures additional native-binding/target-label context only.

## Observed outcome (no post-result tuning)

Complete 28-trial pilot: control 5/10 native-equivalent positives, 1 wrong emitted
positive, 4/4 safe negatives; ontology 7/10 equivalent positives, 0 wrong emissions,
4/4 safe negatives. Three ontology-only wins (proper-noun POS, explicit broad
Noun alternatives, plural-adjective containment), one control-only win (imperative
second-person), four shared positive wins. Negative containment and exact lexeme
remain failures in both arms. Eight deterministic adapter/runner tests now pass.

Known usage: 258 calls, 795,747 input / 88,815 output tokens, no API errors or
unknown usage; estimated model cost $.033421374. Ontology input cost +26.9% with
10 more calls; no efficiency improvement claim. Complete intent audit must
corroborate native equivalence, including control's redundant sp=verb on the
ImperativeVerb domain. A wrong control nametype-presence predicate is not proper-
noun POS, even if both can be related to names.

The predeclared opt-in adoption gate passes on this small pilot. Focused #60 owns
production extraction with its own research/RED/exact-head/wheel/review gates;
#57 retains broader fresh evaluation/default ownership. This PR remains research-
only: no package/dependency/default change or broad quality claim.

Adversarial review found a UTF-16 declaration bypass in the research XML byte
check. RED test accepted a UTF-16 DTD; fix decodes strict UTF-8 before checking
XML declarations, then GREEN. This was AFTER the once-only study, whose pinned
catalog is UTF-8. Preserve original source commit in reports; replay every actual
model request through the hardened adapter without new inference to verify the
measured path is unchanged. No model outcome, catalog or gold was replaced.
