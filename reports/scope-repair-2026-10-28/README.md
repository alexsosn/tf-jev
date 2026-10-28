# Jev scope repair: development diagnosis (#64)

**No production adoption. #64 remains open.** This episode researches actual #57
failures, retaining Jev1.14, schema-derived choices, native execution and the exact
.8 probability/.2 margin complete-candidate gate. No production, dependency,
compiler, API or default change. All requests here are observed development cases;
no fresh quality or release claim. Old reports are preserved byte-for-byte.

[Preregistered/adaptively frozen phases](../../docs/research/issue-64-scope-repair.md)
record each hypothesis before inference. [Checkout-only helpers](../../scripts/scope_repair.py)
retain unsuccessful variants to support inspection; none is a public parser API.

## What helped, and what did not

Making node/property scope explicit in prose did not repair the three observed
scope failures. The operator controls themselves changed from their #57 answers,
so apparently better operator choices cannot be attributed to the prompt variant.
Neutral versus prose child-type probes have identical input but disagree: there
is actual backend variability, not three independent wording effects.

A joint bounded native-type pair choice gets all three observed type pairs right.
Global property selection followed by a two-node role question can recover complete
positive containment. V3 emits the correct clause-with-imperative-word query and
the tiny phrase-with-verb query, both with parent-only projection. Native raw slot
membership independently confirms the results.

Concrete small-domain predicate choices recover the complete adjective-plus-
missing-qere query in V4. They also regress cases: this is not an adoption result.
Negative containment repeatedly chooses NE inside an already-negated child, even
when instructions explicitly explain the outside negation. Other requests drop POS
or transfer another annotation's presence/absence to POS. Merely adding explicit
prose or a more elaborate coordinator is insufficient.

| Complete development phase | BHSA positive native-equivalent | Safe BHSA negatives | Tiny positives | Safe regex |
| --- | ---: | ---: | ---: | ---: |
| coordinator-v2 | 2/8 | 7/7 | 1/3 | 1/1 |
| coordinator-v3 | 3/8 | 7/7 | 2/3 | 1/1 |
| coordinator-v4 | 3/8 | 7/7 | 0/3 | 1/1 |

No wrong emitted query was observed. This small selected sample does not establish
safety/generalization. The phases are adaptive, not statistically isolated paired
ablations. Accepted BHSA cases: v2 adjacency05/06; v3 morphology02, containment07,
literal11; v4 morphology02, containment07, absence10. Different phases do not
combine into one working parser. Incomplete/rejected proposals remain failures.

The first trajectory stopped after two paid calls because the ordinary ontology
adapter requires an assigned type for a feature stage. Its complete=false report
and costs remain. A RED-tested research router then realizes the frozen rule for
unassigned global stages; the complete v2 run is separately named, not a replacement.

## Independent evidence

[Native audit](independent-native-audit.json) re-derives gold from actual feature
maps and oslots, independently of compiler/gold query text. All emitted projected
sets agree exactly, including ordered adjacency pairs. Eight BHSA raw gold sets
and all three tiny raw oracles are checked. Full116-file BHSA source hashes,
benchmark/catalog digests and native gold are verified before trajectory inference.
BHSA data/TF13.1.0/SDK0.7.4/model1.14 are unchanged from #57. The full extracted
schema identity is 4a777cf2dc316633c062e89a99580bf1f19b9c7aa2713892779b11a4c60a442c.

Correct tiny suffix-presence candidates still receive weak final yes probabilities
(v2 .57). V2 complete masculine-plural-adjective receives .78. These are failed
positives, never passed smoke tests. [#66](https://github.com/alexsosn/tf-jev/issues/66)
separates verifier false-refusal research from #64 proposal-scope errors. Wrong
candidates are also rejected here; global gate lowering would mask those errors.

## Accounting and reproducibility

[Summary](summary.json): **421 API calls**, 1,225,369 input /159,464 output tokens,
105.479s summed backend latency, **$0.051465498**, zero API errors or unknown usage.
One local ontology-routing error is separate from API errors and included in cost.
Trace calls are counted once; embedded tiny attempts are not also separate files.
Retries are disabled. Cost excludes native extraction, execution, packaging and CPU.
Price is the [official checked input-only $.042/M](https://docs.typesafe.ai/models.md),
retrieved2026-10-28. Future price/model resolution must be checked independently.

Numeric traces persist after every API attempt; full question/context structures
and predictions remain local/private, not in public report JSON. Runners are
[archived as inert text](runners/) for review, with original local paths and
credential *loading code*, never credential values. They are records, not reusable
CLI commands: do not execute them against existing observation paths. The BHSA
cache was generated locally after116-file verification, never loaded from untrusted
pickle data. Runners verify native gold and schema before constructing the client.
[Provenance corrections](provenance-corrections.json) explicitly identify inherited
tiny wheel-hash fields as historical metadata, not executed-wheel attestations,
and describe the between-case budget guard limitation. Actual phase totals remain
within their frozen caps. The final helper retains named variants; per-run BHSA helper digests identify the
observed dirty research source. Formatting and None-capability support were tidied
later; this is not exact-release-head inference evidence.

RED-first imports for scope adapter, joint choices, coordinator, ontology routing,
scoped relation/output and concrete predicates fail before each implementation;
focused native tests turn GREEN. The framing-only test was added after its helper,
and is post-hoc verification, not RED evidence. Full final-head tests and skeptical
review are required before merging this research record. There is no production
fix or wheel-release claim; installed-wheel positive/negative smoke remains a
requirement for any eventual user-facing #64/#66 implementation.

The next work should target the remaining exclusion/POS counterexamples with a
small bounded contrastive experiment. Do not extract this larger coordinator or
add a repair/search framework merely because separate variants solve different
cases. The official function-calling/beam recipes were inspected; no new provider,
beam infrastructure or unbounded candidate-repair loop was built.
