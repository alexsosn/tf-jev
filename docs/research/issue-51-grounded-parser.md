# Opt-in grounded parser (#51): research and protocol

## Evidence and scope

#48's original supported-stage choices are conditional on gold histories and do
not establish autonomous parsing. Its strongest concrete result is rejection of
regex after supplying the exact compiler subset, and more correct type/feature
decisions surviving gates. Full context costs ~14.2x control input for support.
Do not build a new retrieval/execution framework or replace the backend to test
this change. Reuse CorpusSchema, DecisionBackend, validated QueryIR/compiler,
native TF search and the existing benchmark/evaluation/metering utilities.

Read actual parser.py, compiler/IR, schema domain contracts, TF grammar conformance
and current SDK adapter. Native TF 13.1 owns presence/absence, inequality including
missing annotations, slot relations, edge directions and quantifier execution.
Existing conformance/native tests establish those semantics; the new benchmark
must verify them independently on BHSA. The parser's first decision lacks this
capability context; predicate-count decisions precede feature semantics. A tagged
stop alternative plus deterministic iteration can remove this counting task
without generating arbitrary query text. No new generic model transport needed.

## Implementation plan (before production changes)

- Separate public `GroundedParser(schema, backend, policy=GroundedPolicy())`; keep
  `SemanticParser`'s default behavior, public result and compiler unchanged.
- Share the existing checked choose/receipt/value/operator/compiler machinery by
  factoring small overridable context, threshold and predicate helpers into _Run.
  Legacy tests must prove unchanged behavior/payloads. Grounded _Run adds actual
  corpus/grammar context, corpus-native slot/type roles, and complete typed
  predicted state. Never import research helpers or benchmarks into src.
- Each atom chooses a schema type and repeatedly chooses a new feature or a
  unique enum sentinel. No unaided predicate count. Require a fourth decision
  after three predicates: DONE succeeds; any fourth requested feature refuses
  before selecting its operator/value. Real features named DONE remain usable.
- Preserve literal alternative count (1-3), compatible operators, bounded local
  retrieval, integer extraction, relation direction, output role projection and
  final fidelity checks. Explicitly describe operators/roles; no oracle state.
- Grounded policy contains optional static stage gates (shape/type/feature/other),
  finite validated probability/margin pairs, and ordinary parser budgets. Defaults
  stay .8/.2 everywhere. Explicit stage policies are experimental call-site
  configuration, not a claimed calibrated whole-query probability.
- Full schema is required. Budgets include complete serialized state/question
  after escaping, not only raw descriptions; no truncation or unbounded values.
  Corpus/type/feature metadata is untrusted JSON. Keep absence-eligible features
  even when unattested on the chosen type. Bound symbol inventories to 255 each.
- Record the complete predicted candidate including relation and requested
  projection before verification; all choices still resolve to local typed values.
  A wrong fidelity answer must abstain. Exceptions remain static/sanitized.

## Fresh benchmark and independent freeze

New `benchmarks/grounded-v1/` contains newly authored NL/native-gold examples, using
existing `nl-tf-v2` SERIALIZATION FORMAT, not the previously observed v2 dataset.
Its dataset name and SHA256 distinguish it in reports. It has disjoint calibration
and evaluation family names, positives/negatives, explicit projections, native
counts/signatures and exact source hashes. It is frozen and independently
semantically/native reviewed before production implementation or model calls.
The reviewer may be the same context but must derive answers directly from NL,
raw annotations, slot containment/order and edge data, not the authored query.
This is fresh to the revised parser/model experiment, not unknown to its author;
benchmark-author knowledge and small sample limits must be disclosed.

## Preregistered whole-trajectory calibration/evaluation

Use only the new DEVELOPMENT partition for policies. Fixed candidates, with gates
listed as probability/margin:

- strict: every stage .8/.2 (default).
- exploratory: shape .9/.3, type .6/.3, feature .6/.3, others .8/.2.
- guarded: shape .9/.5, type .7/.3, feature .6/.3, others .8/.2.

Run each once on the complete calibration partition with its OWN predicted state;
no per-stage oracle/history. No outcome-driven prompt edits or repetition. A
policy is eligible only if it emits zero incorrect supported queries on supported
cases and zero supported queries on negative cases. Among eligible policies,
maximize supported native-equivalent successes, then choose strict over guarded
over exploratory on ties. If none qualifies, keep strict and report no-go; do not
search more thresholds after observing results.

Freeze selected policy and source head before a SINGLE complete heldout run. No
post-evaluation parser tuning on this dataset. Existing observed v2 may be used
for deterministic regression but no new calls or quality claims here. Metadata
includes dataset/source/schema/code/model versions and attempts, errors, returned
usage, latency and estimated cost, preserving unknown failures. Persist predicted
queries/projections privately for independent semantic inspection; public summaries
contain no raw prompts/queries/passages/credentials. Gold is passed only to scoring.

Usefulness gate is supported execution equivalence >=70%, emitted-supported
semantic precision >=95%, safe negatives >=95%, p95 parse latency <=10s and
returned-usage cost <=$0.01 per request. An undefined precision cannot pass. Also
inspect intent independently: coincidental result equality on this corpus does
not excuse a missing constraint or wrong role. These small-sample gates are a
research decision, not release readiness. Keep experimental/no-default status
unless a separately justified release decision passes all gates.

## Test/review and user-facing episode completion

Observe deterministic RED first for the public GroundedParser API, actual schema
context, predicted state, tagged DONE, fourth constraint refusal, per-stage gates,
full serialized budget, source isolation and legacy behavior. Run real tiny TF,
opt-in BHSA, SDK MockTransport, full suite/lint/types on exact final head. A
logically independent review must attack prompt/state omission, symbol injection,
role swaps, unsupported/ambiguous acceptance, unknown schema/value, loops and
benchmark leakage. Behavior-changing review fixes repeat RED/fix/GREEN/re-review.

Finish with autonomous user-facing smoke: install the built wheel in a fresh
environment, run the documented typed CLI against native corpus and the new opt-in
Python parser with a live bounded request, plus a negative request. This is not a
new benchmark score or a release claim. If it exposes a production defect after
heldout evaluation, fix through gates and declare that heldout observed rather
than quietly reusing it as untouched quality evidence.
