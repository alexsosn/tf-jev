# Jev failure repair (#56)

User direction: retain Jev and explain/repair the integration before considering
another backend. #54 is deferred; no alternative-provider code or calls occurred.
This document precedes new production behavior or model calls.

## Evidence and falsifiable explanations

The frozen #51 strict development run stops 7 times at shape, 2 at type, 1 at
feature, 1 at operator and 1 at verification. The #50 run changes only the Jev
version and solves one integer request. These are not evidence that every losing
trajectory was semantically wrong: the probability gate may reject a correct
winner. Existing records do not expose all distributions for those runs, so obtain
an unchanged control with complete numeric traces instead of inferring causes
from status counts. Old artifacts remain immutable.

Actual GroundedRun.context supplies the full corpus inventory, grammar, every
operator/relation, roles, focus and accumulated selections at EVERY stage. Even
its first shape call consumes about 7,030 input tokens. Subsequent single-field
questions inherit unrelated metadata and serialize selected feature information
indirectly through JSON strings. Predicate operator criteria are just enum names;
the question never names the current feature directly. These are concrete design
properties; their causal contribution requires controlled tests.

Current official [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
(last-reviewed 2026-10-02, fetched 2026-10-20) explicitly warns about irrelevant
state, indirection, literal instructions, counting and chained generation. The
[function-calling cookbook](https://docs.typesafe.ai/cookbooks/function_calling)
uses direct semantic argument descriptions and stated/not-stated questions over
closed sets. This supports testing our integration, not assuming model incapacity.
pg-jev owns structure in code and judges concrete rows; its narrower task is not
proof that our existing planning decomposition is adequate.

## Fixed development experiment

Use all 12 grounded-v1 DEVELOPMENT cases only (8 supported / 4 negative), same
source-verified full BHSA 2021 schema and TF 13.1.0 / SDK 0.7.4. Never load heldout
requests into the experiment. Pin Jev 1.14.0, .8 probability/.2 margin throughout.
No threshold tuning or replacement runs. Validate native development gold first.
For each case, run these variants in fixed order, once each:

1. Exact unchanged GroundedParser control, recording full distributions and actual
   prompts privately for semantic failure inspection (no gold in model context).
2. Focused-state ablation: same questions/options and gates, but send only request,
   grammar for shape, current role/predicted focus for other stages, and the current
   feature/operator selections when relevant. Feature choices still enumerate ALL
   features from the full schema; type/value choices are unchanged. No lexical
   pruning, selected-coverage claim or guessing omitted symbols. Candidate fidelity
   sees complete predicted IR/projection plus grammar. This tests distracting state.
3. Focused state plus literal criteria: same admissible choices, with plain-language
   operator meanings and a question explicitly naming the selected node/feature;
   no change in allowable operators or corpus-specific hardcoding. This tests an
   additional semantic indirection hypothesis; it does not isolate every wording
   effect and must not be described as such.

Only the parser's OWN predicted history is used. Record ALL call attempts, errors,
receipt usage/latency/version and positional distributions. Unknown failed usage
stays unknown. No retries; no old outcome replacement. Model budget <=.10 USD in
known-returned-usage at the verified .042/M input/free output rate (recheck before
calls); stop before a further call if the measured budget is reached. Native/schema
CPU and possible unreturned usage remain separate. Keep raw prompts/query/predictions
private for review; public output uses static case/stage IDs and numeric data.

Compare complete emitted semantics, native projection/results and independently
re-derived raw annotation/slot/edge oracles; stages are diagnostic only. Inspect
correct winners rejected by confidence separately from wrong winners, dropped
constraints, wrong scope/value/operator and verifier failures. No claim that a
confidence increase alone improves correctness. A development success is not a
fresh generalization score. If no full positive works, explain the observed next
blocking mechanism before choosing a further small experiment.

## Gates after evidence

Research helper transformations require deterministic RED-first tests and exact
wire mapping checks before inference. Production changes only after persisted
results/design and their own RED-first tests. Keep native compiler/schema/retrieval,
explicit non-success without query, bounded symbols/values/calls/context and all
legacy behavior. Do not globally lower gates or hardcode benchmark phrases.

Before a default/quality claim, freeze independently reviewed fresh native gold;
observed v2/grounded-v1 remain regression evidence. Exact-head complete suite,
logically independent skeptical review and genuine installed-wheel NL morphology
and relation positive plus safe-negative smokes finish a successful dev episode.

## First results and second fixed probe

Frozen source bc0f055; all 36 scheduled trajectories returned, zero API errors.
Control emits the correct cal-08 integer query (167 clauses); focused and literal
emit none. All four negatives are withheld by every variant. Removing context is
not a demonstrated fix. In the captured focused trajectories, cal-01/cal-02 type
winners become sentence_atom and cal-03 becomes phrase_atom, all below the gate.
The actual requested types are word/word/phrase. Current focus contains shape=atom
and the selected shape description starts with atom; corpus type descriptions are
JSON objects, many names contain _atom, and word is last in native type order.
These are possible terminology/format/order interactions, not proven causes.

Before further calls, freeze 16 type-only observations: cal-01, cal-02, cal-03,
cal-08, using the ACTUAL type question captured from the focused predicted run.
For each case, once in order: exact captured control; request+contract-only state
(same prompt/options); that state plus direct 'Which corpus object type is being
requested?' wording and plain native type-name descriptions; reverse the latter
options with labels/mappings preserved. The last two change multiple wording/
format elements and do not isolate their individual contribution. No gold is
passed; no type is removed; no threshold changes; all observations/errors remain.
These are diagnostic type choices, never end-to-end successes. Continue the .10
USD cumulative known-usage budget; source hashes/version checks still precede calls.

The 16 type probes returned without errors. Exact focused controls selected three
wrong _atom types; removing predicted focus/history made all four winners correct.
Plain native names/direct wording kept all four winners correct; two pass .8/.2.
Reversing that same set keeps all four winners correct; three pass. This implicates
our supplied planning history/format in wrong type selection, but confidence and
ordering remain issues. No threshold is changed and type success is not parser
success. The probe's initial test-only union-narrowing type errors were corrected
without changing its runtime implementation or the recorded outcomes.

Next fixed type probe, before calls: the same four cases, one call each, plain
native names/direct prompt as above, adding ONLY compact native type capabilities
(name, slot role, attested feature names) from each captured unchanged CONTROL's
corpus context. No predicted shape/history, feature definitions, relation/operator
lists or gold. This tests restoring relevant type evidence rather than deleting
necessary grounding together with distracting state. Same gates/model/budget.

All four compact-capability type probes choose the intended type and pass the
unchanged gate (.92/.98/.98/1.00). This is development-only, fixed-order and small-N;
it supports restoring relevant evidence, not a general accuracy claim.

Next freeze one whole-trajectory development variant: `attested` uses focused state
and literal operator criteria, except its type question uses request+contract,
plain native names/direct prompt and compact type capabilities (slot role/attested
feature names) from the FULL actual schema. No predicted history enters type
classification. Parent/child target role wording is retained for two-node queries;
this extra scope requirement is necessary to avoid asking for the parent twice.
Use all 12 development cases once, same model/gates/budget, native gold/source gates
and public/private metering. No default change. All other choices/predicate limits,
retrieval and verification remain unchanged. RED-first tests precede this helper.

## Multi-label feature mismatch

The attested variant passes all six attempted type decisions at the unchanged
gate, yet emits only the same integer positive. On cal-01/cal-02, the winning
feature is correctly gn at .46/.43: gn, nu and sp are ALL legitimate next choices.
Our question explicitly permits ANY additional required feature but then demands
.8 on one mutually exclusive choice. This is a design mismatch between a set-valued
semantic task and exclusive classification; it is not evidence of an incorrect
winner or a reason to fabricate confidence. Other failures remain (shape/stop/
operator/fidelity); this finding does not explain them all.

Freeze four feature-set probes before calls: cal-01, cal-02, cal-03 and cal-06,
using their actual accepted predicted node type from the attested run (word,
word, phrase, clause). For each, one batch of independent yes/no Choice questions,
one per EVERY native node feature, asking whether the request constrains that
specific annotation on that node/role. No gold feature set enters the question.
Supply the request and explicit output/returned-parent scope, with each feature's
native name/dtype/description in its own question. All features remain candidates,
including unattested features for explicit absence tests. No values/passages.
Maintain .8 top/.2 margin for each binary decision; report uncertain negatives
rather than silently assume absent. Code counts selected features and enforces
predicate limits. Independently adjudicate expected sets from NL/native gold only
AFTER inference (3/3/1/0 required features). This is a mechanism probe, not a
parser or quality success. Same 1.14/source/budget/no-retry/accounting policy.

The four all-feature binary batches are NOT a fix: the three positive requests
select extra annotations (including phrase-dependent or suffix morphology), with
many uncertain negatives; the unfiltered parent probe correctly selects none.
No uncertain negative is silently treated as absent and no query is emitted.
This rejects the naive all-features relevance design, while preserving evidence.

## Candidate ranking versus semantic acceptance (next fixed experiment)

A next-feature distribution can rank proposals even when several proposals are
valid. Test a separate ranked-candidate strategy, not a global gate reduction:
use the existing next-feature Choice as a proposal ONLY (no probability/margin
acceptance gate for this ranking). Before using ANY proposed feature in a predicate,
ask a separate literal yes/no Choice whether the request explicitly constrains
that specific native feature on the current node/role. Require .8/.2 on this
semantic acceptance and every other existing semantic stage. A proposed stop
requires a separate .8/.2 completeness check of current node predicates. A no,
uncertain check or error refuses the WHOLE query; no trying a favorable alternate,
constraint deletion or implicit negative default. Full-candidate fidelity remains.
All ranking distributions remain evidence and the existing weakest-probability
result field remains unmodified; do not relabel a .46 proposal as .99 certainty.
The extra checks are correlated model judgments, not independent proof of safety.

Freeze all 12 DEVELOPMENT requests once using relevant attested type grounding,
focused state and literal operator criteria from the previous variant. One rank
and one validation per feature/stop, <=64 total calls, original .8/.2 on all semantic
checks, original predicate/retrieval/compiler limits. No gold, schema aliases,
handwritten phrase matches, retries or heldout inference. This must produce actual
semantically correct morphology before any production design is considered.

Ranked-candidate DEVELOPMENT solves cal-03 (phrase function=Time) and cal-08,
withholds all four negatives, and has zero errors. It reaches cal-01's correct gn=m
predicate, then rejects the correct nu proposal at its literal check (.74 yes).
Cal-02's correct gn check is .65 yes; cal-05's correct vs check is .63 no. The latter
is an actual wrong winner, not a gate-only refusal. Old context includes all prior
planning selections in a question about a single named technical annotation.

Freeze a pointwise relevance wording/context probe before calls: cal-01 nu,
cal-02 gn, cal-05 vs and cal-03 function (positive); cal-01 prs_gn and suffix_gender
(negative contrasts, since the request constrains the word's own morphology, not
its suffix). Six calls, each with ONLY original request, actual predicted native
node type/role and this native property's ID/meaning, no selected plan history.
Question asks for semantic restriction on property_meaning and explicitly says the
technical ID need not appear in the request. No annotation is accepted from these
probes; expected labels are adjudicated after inference. Same .8/.2, model, source,
no retries and metering. Test both positive and misleading related-property cases.

The six pointwise property probes also fail usefulness/scope safety: no correct
positive passes .8/.2, and both suffix-property negatives incorrectly pass as yes
(.83). Therefore do NOT promote abstract property relevance as acceptance.

Next fixed diagnostic: judge a COMPLETE concrete proposed predicate rather than
whether a property is relevant. Ten single calls: cal-01 gn=m, nu=sg, sp=subs;
cal-02 gn=f, nu=pl; cal-05 vs=nif (required); cal-01 gn=f, nu=pl (contradicted),
prs_gn=m and suffix_gender=m (not stated). These are explicitly conditioned probes,
not predicted parser success; this conditioning must be disclosed. All symbols/
values are checked against the actual schema before calls. No gold query is sent.
Three bounded outcomes distinguish required, contradicted and merely related/
not stated. Context contains only original request, native node/role, exact native
feature meaning/operator/value. Require .8/.2 on the right category; report unsafe
required predictions on negatives. Same model/source/accounting/budget. This tests
whether our abstract-field question discards the concrete condition Jev needs.

Concrete predicate probes accept all three cal-01 required predicates at .83/.89/.90,
cal-02 nu=pl at .86, and both contradictory values correctly at .97/.98. Cal-02
gn=f is wrong/uncertain (.53), vs=nif is correct/uncertain (.70), prs_gn=m correctly
not-stated/uncertain (.51), and suffix_gender=m is wrongly required at .80. Thus
concrete entailment improves some judgments but is NOT a proven safety solution.
The initial probe invocation failed before ANY API call on an attribute-name bug;
RED/fix/GREEN preceded the completed ten-call run; no model observation was replaced.

Freeze `concrete` whole trajectories on all 12 development cases once: feature
Choice is a proposal; construct the complete predicate with existing operator/
value gates, then require the three-way concrete predicate check's `required`
outcome at .8/.2 before accepting it. Stop completeness and full-candidate fidelity
retain .8/.2. No abstract feature relevance call; no retry after a rejected predicate.
Only the OWN predicted predicate enters the check. Retain ranking evidence and
weakest probability. Keep exact candidate/scope/native semantic review separate
from result equality, given the known unsafe suffix contrast.

Also freeze one `attested` predicted trajectory per DEVELOPMENT case with
probability/margin gates zero **for diagnosis only**, to inspect downstream
argmax errors hidden by early stops. These are untrusted hypotheses, NOT accepted
user queries, policy selection or success claims. Compiler/schema/native bounds
still apply; no gold is fed back into decoding. Record wrong/unsafe candidates
and every distribution. Do not use this permissive mode in a production parser.

## Full-trajectory finding and minimal correction

The ungated diagnostic produces the EXACT full three-predicate intended IR/native
results for cal-01 and cal-02. Both have strong final yes (.94/.88); feature ranking
is .51/.58 and .44/.49. This directly demonstrates Jev can plan those complete
morphology requests. It does not validate permissive deployment. Cal-05 emits only
vs=nif, omitting explicit sp=verb (execution equivalent because nif annotations
are on verbs); do not silently count that as full semantic coverage without an
independent implication proof. Exclusion cases produce incomplete candidates that
fidelity correctly rejects; cal-04 wrongly routes unsupported. All four diagnostic
negatives withhold a query. Errors are mixed, not one universal confidence issue.

Freeze `verified`: exactly the attested strategy, except next-feature/DONE Choice
is candidate ranking only (no local probability gate). Every other single-valued
stage retains .8/.2 and full-candidate fidelity retains .8/.2 before compilation/
query emission. No separate abstract feature or predicate check (those measured
worse); no automatic retry/repair. Keep every ranking distribution and unmodified
weakest probability in evidence. This explicitly changes the semantic role of
feature Choice, not its reported probability, and does not globally lower gates.
A proposed feature or stop cannot emit a query before the complete candidate is
verified; native compiler/schema validation and three-predicate boundary remain.

One whole DEVELOPMENT run, all 12 original development requests plus four freshly
frozen DEVELOPMENT witnesses: verb/substantive adjacent ordered pairs; returned
phrases containing verb witnesses; explicit missing feature; unsupported lex regex.
Freeze native gold and independent raw slot/annotation oracle before model calls.
No fresh heldout/default claim; these witnesses become observed development data.
Use exact same model/source/budget and independent semantic review of full emitted
constraints/projection. Require actual morphology AND relation positives before
promoting even an opt-in production strategy or installed-wheel positive claim.

Verified completes 3/8 original positives (full cal-01 morphology, cal-03, cal-08),
withholds all six negatives including the two new ones, and abstains on both new
relation witnesses. The adjacency router's CORRECT relation winner is .79; the
positive-containment request incorrectly chooses atom at .76. The first criterion
says 'One node type filtered by annotations', which can also describe a returned
phrase filtered by a child condition. It fails to distinguish output arity from
witness/relational structure. This is another question-contract error, not a
backend diagnosis. Storage interrupted after the first completed model observation;
it was saved from memory and continuation began at case 2, with no repeated call.

Freeze `routed` on the same 16 DEVELOPMENT cases once. Only routing criteria change
from verified: atomic requires NO second-node/witness condition; positive relation
includes containment/immediate adjacency, allows identical types and returning one
or both nodes; negative containment explicitly excludes matching children. Unknown
literal familiarity is deferred to schema/value validation; unsupported grammar
and unresolved intent remain explicit choices. Type/context/feature proposal policy,
all .8/.2 single-valued/fidelity gates, limits, values and compiler are unchanged.
No threshold tuning or model/observation replacement. Require actual whole-query
morphology and relation successes, inspect all constraints/ordered projection, and
keep public default prohibition absent fresh evaluation.

Routed classifies both new positive structures correctly (.97 relation/.80
relation), retains full cal-01 morphology and all negatives safely. Adjacency
stops at literal-alternative count: correct 1 wins only .55 because the request
mentions verb and substantive values for DIFFERENT nodes; the count question
never names its current node/feature. Containment and cal-06 stop at child type:
they incorrectly repeat phrase/clause instead of word. Type context deleted all
history, and 'being requested' primes the returned parent instead of the witness.
These are separate scope omissions visible in actual prompts/distributions.

Freeze scoped on the same 16 DEVELOPMENT cases once, inheriting routed:
- child/second-node type context adds only the already-predicted first node type
  and explicit target role; prompt asks about that child/witness rather than the
  requested output. Same-type pairs remain allowed. First-type behavior unchanged.
- alternative count names the current native property/meaning, node type and
  explicit parent/child/first/second role; count criteria describe one/two/three
  OR alternatives for THAT property, not values mentioned for other nodes/features.
  Its context carries only original request and those local facts.
No choices/domains, gates, model, retrieval/compiler or final fidelity change.

Before scoped inference, source inspection also shows focused fidelity context
removed the relation-token legend: candidate IR encodes containment/adjacency as
native enum values such as [[ and <: without explaining them to the verifier.
Restore the closed compiler-relation meaning map ONLY at verification. These are
code-owned native semantics, not corpus passages or extra schema inventory.
Add this prerequisite to scoped; keep older variants/outcomes byte-identical.

Scoped keeps the cal-01 complete morphology result, but the remaining per-field
gates still block relations before a whole candidate exists. Do not interpret
these refusals as evidence that Jev cannot plan the query. The diagnostic already
showed complete correct plans hidden behind low proposal probabilities.

Freeze joint on all 16 DEVELOPMENT requests once: all bounded field choices are
PROPOSALS to a typed candidate, with no per-field probability admission threshold.
Existing structural budgets, domain membership, explicit non-success states and
compiler validation remain mandatory. Only final COMPLETE-candidate fidelity has
the original .8/.2 acceptance gate; a low/negative fidelity returns no query.
Use scoped question/context improvements and the native relation legend. This is
an explicit experimental acceptance-policy change, NOT unchanged per-field gates
or calibrated confidence. Retain ALL alternatives/probabilities and the unmodified
weakest probability in results; never represent proposal probabilities as certainty.
Measure wrong emissions as well as correct ones; no default/quality recommendation.
No retries, alternate-candidate search, model changes or gold in the parser.

Joint produces correct COMPLETE adjacent-pair and positive-containment candidates,
including values/direction/projection, but fidelity yes is only .71/.52. These are
not accepted user successes. The JSON candidate still uses compact feature and
operator codes and references. A separate native relation legend did not remove
that interpretation burden. Cal-01/cal-03/cal-04/cal-08 emit correct queries;
all six negatives withhold; no wrong emitted query so far.

Freeze semantic on all 16 DEVELOPMENT requests once: same joint proposals, domains,
questions, limits and .8/.2 final acceptance, but final verification receives a
deterministic plain-language explanation of the EXACT typed IR plus raw IR.
Explain every predicate with native feature metadata, actual operator/value(s),
relation with bound source/target roles, exclusions, and ordered distinct output
columns. Validate IR/projection before explanation. Never add inferred/missing
conditions or describe gold instead of the prediction. The explanation is model
context, not a second execution language/engine. Keep untrusted literals/metadata
quoted/escaped and bounded. Final state needs only original request, grammar,
untrusted-data contract, raw candidate and its complete explanation; discard
irrelevant intermediate selections there. Explicitly reject missing/invented
conditions, broader alternatives, wrong scope/direction/output and unsupported
operations. Source/native tests must show the explanation covers the actual IR,
including negative containment, edge direction, distance and reversed projection,
before this variant is inferred. No model/threshold changes or replacement runs.

## Extraction outcome

Semantic produces six native-equivalent positives out of ten supported development
requests, with all six negatives safely withheld. Complete morphology and positive
containment now work. Exact lexeme, negative containment and adjacency remain
failures. Preserve all attempts; no fresh quality/default claim. #57 tracks fresh
independent native-gold evaluation with Jev retained.

Production CandidateParser is separately opt-in and rejects per-stage gate options.
RED production import failed before source creation; native morphology, weak/final
admission, complete explanation, SDK, witness, sentinel and bounded-failure tests
pass. Native source inspection confirms inequality includes missing values and
presence includes empty strings; production explanation explicitly states these.
The installed wheel passed live NL morphology and containment with nonempty native
results, plus all three safe negatives. Report assembly then failed on the .tf
cache directory and lost receipt counters; smoke cost/latency/usage stay unknown,
no calls repeated. Research accounting remains complete and separately reported.
