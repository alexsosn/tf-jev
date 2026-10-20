# Relevant ontoTF context: paired Jev pilot (#59)

**The small pilot supports a minimal opt-in integration, not a default change.**
Ontology context improves complete correct positives from 5/10 to 7/10, removes
one observed wrong emission, and keeps all four negatives safely withheld. It
also loses one correct imperative/person result and increases input cost about
27%. This is a once-per-arm fresh-request pilot with overlapping known feature
families, not a replicated causal estimate or general safety/usefulness claim.

## Frozen setup

- Package/source at inference: e2e8856, unchanged CandidateParser and native IR/
  compiler; Jev 1.14.0 / SDK 0.7.4 / Text-Fabric 13.1.0, retries zero.
- Full BHSA 2021 schema and 116 native source-file hashes verified before client
  creation. Native gold re-executed before any paid inference.
- [Fourteen fresh requests](../../benchmarks/ontotf-v1/README.md), ten nonempty
  native-gold positives and four ambiguous/unsupported/schema/conflict negatives,
  frozen and independently adjudicated before inference. No exact request reuse;
  existing morphology/structure families overlap, explicitly disclosed.
- ontoTF XML pinned to 4d1112b9c9ec077e3dbf6cd6150b69ac6e53d3b9, 24 exact native
  value records checked against actual schema. Source XML/license are preserved.
  This measures target-label/native-binding context, not the full OLiA graph.
- Same parser/native choices/questions/thresholds/retrieval/compiler in both arms.
  Only a bounded ontology context field is added, using the parser's OWN current
  type/property/candidate. No gold, rationales or native passages in model context.
  No ontology executor, provider change, package dependency or default change.
- Exactly one trial per case/arm, alternating which arm ran first (seven each).
  No replacement trials, post-result tuning or hidden outcome removal. Every API
  observation was atomically persisted before a further call.

[Preregistered protocol](../../docs/research/issue-59-ontotf-ablation.md),
[comparison](comparison.json), [accounting summary](summary.json), and
[independent semantic/raw/request audit](semantic-audit.json) retain the evidence.

## Complete results

| Measure | Control | Ontology context |
| --- | ---: | ---: |
| Supported requests correctly answered | 5/10 | 7/10 |
| Total positive emissions | 6 | 7 |
| Wrong emissions | 1 | 0 |
| Correct among emitted positives | 5/6 | 7/7 |
| Safe negatives withheld | 4/4 | 4/4 |
| API calls | 124 | 134 |
| Input tokens | 350,674 | 445,073 |
| Output tokens | 42,926 | 45,889 |
| Summed backend latency | 40.661 s | 45.142 s |
| Estimated model cost | $0.014728308 | $0.018693066 |
| API errors / unknown usage | 0 / 0 | 0 / 0 |

Three ontology-only wins:
- Proper-noun plural words: the control confidently verifies a wrong name-type
  presence predicate; ontology context selects the requested POS category.
- Explicit broad noun (substantives AND proper nouns included as OR alternatives):
  both propose the same correct candidate, but only ontology fidelity clears .8
  (yes .84 versus .72). This is acceptance assistance, not a new planning success.
- Phrase containing a plural adjective: control omits the adjective condition
  and safely rejects its incomplete candidate; ontology includes both conditions
  and returns the correct parent-only projection.

One control-only win:
- Second-person imperative verbs: both form semantically correct candidates,
  but ontology fidelity yes .76 misses the fixed .8 gate; control yes .88 passes.
  The ontology candidate includes all three explicit predicates. Extra context
  can hurt admission confidence; do not lower thresholds to recover this result.

Both solve masculine-dual substantives, feminine-singular adjectives, construct
state and suffix-person requests. In particular, own-word person ontology links
are not substituted for the suffix-person annotation. Both fail negative
containment and exact lexeme retrieval. Both withhold all four negative requests;
this is safe withholding, not a claim that their negative status labels are all
correct. No overall reliability claim from zero observed ontology mistakes.

## Independent adversarial semantic checks

Re-derive expected sets from actual word/phrase/clause types, native feature
maps and oslots membership, independently of the compiler/gold text. Every
accepted ontology query exactly matches the frozen native query and projection,
so no extra native alternative or missing condition is hidden by equal results.
The sole correct non-exact control query uses vt=impv and ps=p2 without redundant
sp=verb. Native metadata defines vt as verbal tense, the pinned catalog identifies
impv as ImperativeVerb, and every actual imperative word has sp=verb. Its verbal
meaning is therefore justified beyond accidental count equality. The other control
emission is wrong and remains a wrong emission.

Review checks broad Noun versus substantive/proper-noun scope, own-person versus
suffix-person scope, all morphology conjunction terms, containment direction,
negation, witness conditions and returned columns. See the audit artifact for
all 13 emitted-query adjudications and all actual request replay counts.

## Accounting, limits and decision

Total 258 API calls, 795,747 input / 88,815 output tokens, $0.033421374 known
model cost at the rechecked official $.042/M input/free-output rate. No API error
or unknown usage. Per-trial *-calls.json files are canonical once-per-attempt
records; don't count comparison receipt totals again. Latency above is summed
backend time, not wall time or schema/native CPU cost. Full traces contain only
static/redacted stage IDs, positional numeric distributions and usage/errors.
Raw requests/candidates stay private. Public benchmark gold and the pinned XML
are deliberate research inputs, not model transcripts.

The predeclared adoption gate passes: net two extra correct positives and no
additional wrong emission or unsafe negative. #60 owns the smallest separately
opt-in production extraction, with its own RED/test/exact-head review and installed
wheel smoke; #57 still owns broader fresh evaluation. No package/default change
is made by this research PR. The 14 cases are now observed and cannot be reused
as fresh evidence after tuning.

A post-study adversarial test found UTF-16 XML could bypass the research byte-level
DTD guard. RED -> strict UTF-8 decode before declaration checks -> GREEN. The
actual pinned UTF-8 catalog and all recorded model request structures are
unchanged under replay; reports preserve the actual inference source commit.
No paid calls or gold were rerun/replaced. This hardening is not a new model result.

Reproduce the frozen study only as a NEW observation (never overwrite this run):
set TF_JEV_LIVE=1 and credentials explicitly, then run
`python -m scripts.ontotf_experiment /path/to/bhsa/tf/2021 --live --output /new/public --private-review /new/private`.
It requires exact research dependency versions and new output directories.
