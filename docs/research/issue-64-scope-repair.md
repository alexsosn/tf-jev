# #64: scope repair, development protocol

## Evidence and hypothesis (before inference)

The actual #57 requests show that feature questions use “this node” and an
all-stage selected-history JSON. The empty-domain diagnostic puts the child's
POS on its phrase parent; fresh-08 stops before the excluded word's POS.
Fresh-09/10 apply qere presence/absence to POS. Their operator question names
`sp`, but omits its actual part-of-speech description. Fresh-07 chooses clause
again for the other entity. These are integration hypotheses, not evidence that
Jev cannot express the intent. Native TF and existing gold remain authoritative.

No symbols, options, probabilities, final .8/.2 gates, models or catalogs change.
Unattested features remain selectable: native ABSENT is meaningful for them.
Corpus metadata is untrusted data and must remain under the existing contract.
No BHSA-specific interpretation belongs in production code.

## Frozen first experiment

Replay six observed stage inputs once each, control then explicit-scope variant,
Jev 1.14.0, SDK 0.7.4, no retries; maximum 12 API calls / $0.01 input cost.
No replays may replace failures. Original observations remain untouched.

1. Tiny containment atom0.pred0.feature: STOP, no parent condition requested.
2. fresh-07 atom1.type: word, the other entity is explicitly a word.
3. fresh-08 atom1.pred0.feature: sp, conjunction restriction on child word.
4. fresh-09 atom0.pred1.operator: EQ, substantives constrain POS.
5. fresh-10 atom0.pred0.operator: EQ, adjectives constrain POS.
6. fresh-09 atom0.pred0.operator: PRESENT, retain correct qere interpretation.

Variant: make the current native type, role, property meaning (when selected)
and already-completed conditions explicit; remove unrelated selected history
from feature/operator context. Preserve supplied ontology context and every
native choice. Second-type question names the first type as its counterpart.
Question adaptation is deterministic, generic and unit-tested RED-first.
These oracle-conditioned observed probes are development diagnosis only; stage
wins do not count as end-to-end successes. Freeze full-trajectory trials before
any later calls. Production adoption requires complete native-result paths,
safe controls, exact-head tests, wheel smoke and independent adversarial review.

## First observations and next frozen probes

The 12-call first experiment is complete. Explicit scope produces no stage-win
increase: parent POS leakage, child-type error and exclusion STOP all persist.
Both current operator controls now choose EQ, unlike #57: variability rules out
claiming a causal operator improvement. No production change is justified.

Second experiment: three failed inputs above, three variants, once each (9 calls,
$0.01 cap), in parent/type/feature order. No favorable replacement of prior rows.
- neutral: map question ID to `decision`, remove selected-history, roles, focus,
  planned_first_type/target_role; retain request/contract/type capabilities/ontology.
  Put current native type/index and already-completed predicates in plain context.
  Ask first/second-mentioned native type; feature question asks own native type.
- prose: neutral plus render native feature/STOP options as concrete scoped
  statements, retaining option labels, native feature IDs and attestation facts.
- polarity: prose plus make exclusion's existential matching role explicit in
  the child question: define the condition a child would match, not whether any
  such child exists; keep positive annotation meaning within negated containment.
  For parent questions clarify that merely containing a filtered child does not
  imply an annotation condition on the parent. For second-type ask the second
  entity's type with no first-node capability priming. No NL substring rules.

These test task framing, native *_atom/question-name priming and negative-scope
interference. None adds an oracle/type/feature absent from original options.

## Third experiment, frozen before calls

Framing phase has mixed wins; identical child-type inputs disagree between calls.
No prompt variant is adopted. Next test the missing competing scope explicitly:
- joint type selection from Cartesian product of actual expressible types, in
  mention order, same-type pairs included, cap255. No relation or type invented.
- joint next-feature selection over both predicted native node roles and all
  native features plus STOP, cap255. A feature is not pruned for non-attestation.

Three observed requests (tiny containment, fresh-07 containment, fresh-08
exclusion): one joint-type call each followed by one joint-feature call using the
predicted pair, not the gold pair. Thus six calls total / $0.01 cap. Include both
native roles in each option so the child's POS competes with the parent's POS.
Expected first choices: tiny phrase/word and word sp; fresh07 clause/word and word
vt; fresh08 phrase/word and word sp. Count stage success only; no query emitted.
This is a bounded decomposition experiment, not candidate repair/retry or a new
execution engine. Full native schema/options are obtained from original captured
corpus inputs; the two BHSA feature inventories are identical; tiny has10 features.

## Fourth experiment: complete development trajectories (frozen before calls)

Joint type selection gets all three pairs right. Joint feature-and-role gets
2/3 right; imperative still lands on clause. Test the smaller questions separately:
choose next property across the whole request, then choose its node role from the
already-proposed native pair. This exposes both roles without the 2×feature option
inventory. No correction/retry of a proposed candidate. Same type may receive the
same feature on both roles; remove a feature only after both roles have it.
Each node retains the three-condition cap; a fourth condition fails explicitly.

Research-only coordinator uses existing CandidateParser bounded choices, predicate
planning, relation/output construction, compiler and exact final fidelity gate.
It first proposes native types (joint pair for two nodes), then next property,
then property role, then operator/value under local property/type context. Global
feature context carries both planned types and completed predicates, not the
unrelated selected-history JSON. Native feature JSON options and STOP remain.
Operator context names actual meaning and type; annotations/requests are untrusted.
Ontology backend remains unchanged: globally unassigned feature choices have no
single type and receive no type-scoped catalog; assigned operator/value/count and
final candidate stages retain ordinary catalog assistance. No catalog selection
or final verification code changes.

Run once on observed fresh-07/08/09/10 plus all seven fresh negative controls and
fresh-02/05/06/11 positive regressions, and tiny containment/presence/absence/regex.
Order: tiny four, then ascending BHSA IDs. Native gold and raw/source oracles
precede inference. No performance/default quality claim; all are development.
Cap400 calls/$0.05; stop on transport/accounting/native-source drift, retain every
attempt. No retries or substitution of favorable outcomes. Need complete correct
containment, exclusion, multiproperty presence/absence with safe negatives before
any production extraction; otherwise retain findings and continue focused research.

Fourth-phase runner stopped after two successful paid calls on tiny containment:
the unchanged ontology adapter expects `focus` for any atom*.feature stage; global
feature context deliberately has none. This is a local integration error, not a
model semantic failure; retain tiny-trajectories.json complete=false and its cost.
Before continuation, add a research backend router that bypasses optional ontology
only for context with `planned_nodes` (global feature/role questions). This realizes
the already-frozen no-type-scoped-catalog rule, without modifying the production
ontology adapter. Resume as named revision `coordinator-v2` with all four tiny
cases once; retain the interrupted run as a separate failure, never replace it.

## Fourth outcome and fifth frozen correction

Coordinator-v2 completes: BHSA 2/8 supported positives, 7/7 safe negatives; tiny
1/3 positives, regex safely unsupported. No wrong emissions. Two concrete complete
candidates reveal downstream contract gaps: containment chooses edge instead of
slot embedding and returns both columns; exclusion chooses NE inside an already
negated child, double-negating conjunction. On three lexical+presence requests,
the global feature stage omits POS. This phase lost ontology's POS category help
because it had no single-node scope. These are failures, not acceptance evidence.

Freeze coordinator-v3 on the SAME tiny4/BHSA15 requests once, cap400calls/$0.05.
Keep all v2 observations. Change only:
1. Global feature/role context may include catalog bindings for the union of the
   already-proposed native types, bounded to8KiB and the existing wire limit.
   Omit optional assistance when it does not fit; never narrow native options.
2. Negative-containment child operator prompt explains that structural exclusion
   is already applied outside this child predicate, and asks what a matching child
   would satisfy. Do not invert the requested child's literal test twice.
3. Directed relation options substitute actual proposed native type/role labels
   for opaque atom0/atom1. Output options explain actual ordered native node types
   and which other node is merely a witness. No relation/output option removed.
Final candidate verification/context/gates remain exactly unchanged. Thus correct
proposals rejected by final confidence remain failures; no verifier tuning here.

## Sixth frozen diagnostic: concrete small-domain predicates

V3 recovers native-equivalent tiny and BHSA containment, but exclusion still picks
NE; fresh09 omits POS; fresh10 applies ABSENT to POS. These are observed failures.
V3 is not eligible for production extraction. No global gate change is justified.

Test coordinator-v4 once on the same tiny4/BHSA15, cap400calls/$0.05 total.
Keep v3 type/role/relation/output/fidelity. Render each global feature option with
its actual native enumerated values only when the inventory is <=32 (no large
vocabulary sent). This supplies concrete native categories while retaining feature
JSON identity and all options. For a selected small string domain, ask ONE bounded
choice among complete EQ/NE single-literal predicates, PRESENT, ABSENT, or a tagged
multiple-values branch that delegates to the unchanged bounded predicate planner.
This eliminates the abstract operator/value separation for single-literal tests.
Every alternative is deterministically derived from actual schema; no new model
text reaches IR/compiler. The explicit multiple-values option preserves OR intent;
no pair/triple enumeration or silent truncation. Large domains and integers keep
the existing local-retrieval/operator contract, so high-cardinality presence does
not require value retrieval. Condition options identify native type, feature ID,
meaning and actual literal. Negative-containment predicate wording defines the
matching child and describes the outside negation separately. Final candidate
and .8/.2 verification remain unchanged. No retries/outcome replacements.

## Episode outcome

[Durable report](../../reports/scope-repair-2026-10-28/README.md): 421 calls/$0.051465498,
no API errors/unknown usage, one retained local routing interruption. All accepted
queries pass independent full-set native oracles. V2/V3/V4 solve2/8,3/8,3/8 BHSA
positives, respectively; all seven negatives withheld in each phase. Tiny solves
1/3,2/3,0/3. No variant recovers the required combination of complete exclusion
and multi-property presence/absence. Do not extract into production; #64 stays open.
#66 separately owns correct-candidate verifier false refusals. This episode is
research evidence, not a user-facing fix or a release candidate.

Current authoritative sources inspected2026-10-28: TypeSafe
[models](https://docs.typesafe.ai/models.md),
[function-calling recipe](https://docs.typesafe.ai/cookbooks/function_calling.md),
[hierarchical bounded beam recipe](https://docs.typesafe.ai/cookbooks/hierarchical_classification.md),
and [documented1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md).
Jaggedness describes1.13, not proof of1.14 behavior. Actual1.14 calls are the evidence.
