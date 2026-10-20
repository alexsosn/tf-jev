# Initial research framing

This document records bootstrap hypotheses and open questions. It is not evidence that the proposed architecture works.

## Research question

Can a low-cost bounded-decision model such as TypeSafe Jev translate natural-language requests into native Text-Fabric search queries accurately enough to be useful, without free-form query generation?

## Working hypothesis

The problem can be decomposed into three mostly independent layers:

1. **corpus/schema understanding** — extract the symbols and value domains available in the loaded Text-Fabric corpus;
2. **semantic decoding** — map natural-language intent onto a bounded typed representation using schema-derived choices;
3. **query compilation** — deterministically render that representation into native TF search syntax and validate it.

This should make syntactic validity easier than direct LLM query generation, but semantic correctness remains an empirical question.

## Evidence required before freezing an IR

Research must inspect the current Text-Fabric search implementation/documentation and enumerate:

- atom/node syntax;
- node-feature constraints and supported comparison/value forms;
- edge features and directed/undirected edge constraints;
- spatial/structural relations;
- named sets if relevant;
- quantifiers and nested constructs;
- query variables/templates if relevant;
- parser diagnostics and ways to validate without expensive execution;
- corpus APIs for discovering node types, features, edge features and useful value domains.

The IR should cover a deliberately chosen prototype subset first. Do not claim complete TF grammar coverage without tests.

Findings (#2): [docs/research/tf-search-grammar.md](docs/research/tf-search-grammar.md) — grammar, escaping, validation surface and the chosen prototype subset, pinned by `tests/conformance/`.

## Jev questions to verify from the current API

Before implementing any Jev client/adapter, first survey maintained Python Jev clients/toolkits (including `docxology/daf-jev` as an identified candidate) and prefer reuse when their contract is adequate. Then verify:

- supported primitive output types and limits;
- maximum practical `choice` cardinality;
- whether multiple independent decisions can be evaluated efficiently in one request;
- probability/confidence semantics;
- model/version pinning;
- rate limits, timeout/retry semantics and pricing;
- data-retention/privacy behavior relevant to schema/value transmission;
- whether hierarchical choice materially improves high-cardinality decoding.

All API and pricing claims must be date/version grounded in the research ticket.

Findings (#6): [docs/research/jev-decision-backend.md](docs/research/jev-decision-backend.md). Decision: thin adapter over the official `typesafe-sdk` (optional extra), pinned to `jev-1.13.0`; backend-neutral contract in `src/tf_jev/decisions.py`.

## High-cardinality value problem

Some TF feature domains are small (for example grammatical categories), while others can contain thousands of lexemes, names or IDs. A bounded-choice backend should not receive an entire large vocabulary.

Candidate approaches to research:

- exact/normalized lookup;
- prefix/fuzzy retrieval;
- lexical aliases/gloss indexes;
- corpus-specific searchable labels;
- hierarchical narrowing;
- deterministic filters before model ranking.

Candidate retrieval must be measurable independently from the model.

Findings (#4): [docs/research/corpus-schema.md](docs/research/corpus-schema.md) gives per-(feature, object type) cardinalities on BHSA 2021, the missing-value and empty-string semantics, bounded-choice thresholds, corpus identity, and the proposed `CorpusSchema` contract.

## Evaluation hypothesis

Exact query-string match is insufficient because multiple native TF queries may be result-equivalent. The benchmark should therefore distinguish:

- exact compiler output for a fixed IR;
- parse/IR correctness;
- TF parser validity;
- execution/result equivalence against a gold expectation;
- unsupported/ambiguous-query detection;
- cost and latency.

## Candidate first corpus

BHSA is a strong candidate for the first benchmark because it exposes rich node/feature structure and supports realistic linguistic queries. This is a research preference, not yet a hard package dependency.

Pinned version: BHSA data version **2021** (latest; `ETCBC/bhsa` release v1.8.1). Older versions (`c`, `2017`, …) must not be mixed into benchmark or conformance evidence.

## Non-goals for the first prototype

- semantic interpretation of corpus text not represented in TF annotations;
- arbitrary natural-language question answering;
- generating or modifying corpus annotations;
- replacing Text-Fabric search execution;
- supporting every TF query construct before a smaller benchmarked subset works.

Compiler follow-through (#3): [typed compiler contract](docs/design/typed-compiler.md)
records the schema protocol, runtime validation and quantifier workaround. Source
inspection also found that TF tokenization uses Python `split()`: non-ASCII
whitespace is unrepresentable as a literal value, so it is rejected before rendering.

Schema implementation follow-through (#5): [extraction contract](docs/design/corpus-schema.md)
records location/module override identity, effective loaded-data hashing, exact
sparse-integer membership and all-missing per-type domains, verified against
Text-Fabric 13.1.0 source before implementation.

Candidate retrieval (#7): [real-domain findings](docs/research/candidate-retrieval.md)
show why normalization must be explicit and prefix overflow must block ranking.
The frozen [lookup benchmark](benchmarks/retrieval-v1/README.md) measures literal
retrieval separately from semantic parser quality.

Jev adapter follow-through (#8): [SDK boundary findings](docs/research/jev-adapter.md)
record strict custom-response decoding, scoped log suppression and model-drift
policy verified against typesafe-sdk 0.7.4 source and current official docs.

Semantic benchmark (#10): [annotation and projection findings](docs/research/bhsa-benchmark.md)
underpin the complete [v2 benchmark](benchmarks/nl-tf-v2/README.md). The v1 seed
remains historical evidence; parser work uses v2 with its heldout partition sealed.

Semantic orchestration (#9): [bounded parser findings](docs/research/semantic-parser.md)
separate structural symbol budgets from retrieved value budgets and make return
projection and conservative abstention explicit.

Empirical evaluation and comparison (#11/#12): the [frozen 2026-10-20 study](reports/jev-rules-2026-10-20/README.md)
found 0/86 supported Jev successes and 0/42 heldout supported successes for both
Jev and a conservative atomic rule baseline. The current pipeline is a measured
no-go for default use. Development-only diagnosis and fresh evaluation are #46.

Abstention diagnosis (#46): [development traces and controlled probes](reports/abstention-diagnosis-2026-10-20/README.md)
localize stops to shape, type and predicate count. Corpus-aware planning research
is #48; no production parser change or fresh quality claim is justified yet.

Corpus-aware planning (#48): [preregistered grounded-stage protocol](docs/research/issue-48-grounded-planning.md)
and [measured report](reports/grounded-planning-2026-10-20/README.md) find improved
selective support acceptance, 24/24 correct type winners and 46/50 correct
oracle-conditioned next-feature choices. Isolated stages are not parser success;
no production prompt/threshold change or fresh end-to-end quality claim is made.


Predicted grounded parser (#51): the [fresh whole-trajectory report](reports/grounded-parser-2026-10-20/README.md)
finds 0/8 supported calibration successes under each of three preregistered policies
and 0/12 fresh evaluation successes for the frozen strict tie winner. All negatives
are withheld. The opt-in implementation does not change the no-default decision;
local oracle-conditioned stage gains do not establish a working parser.


Explicit model versions (#50): [contract and development evidence](reports/model-versions-2026-10-20/README.md)
verify pinned 1.14 / preview response matching without default drift. Unchanged
strict grounded planning solves 1/8 observed development positives with 1.14,
versus 0/8 in its frozen 1.13 control; no new heldout or quality/default claim.
Backend replacement #54 is deferred by user direction. Jev repair #56 investigates
our integration before considering replacement.


Jev repair #56: focused native-type capability context, explicit witness scope,
property-local counts and whole-candidate semantic explanation recover complete
morphology and containment paths. CandidateParser is explicitly opt-in. The
[adaptive development report](reports/jev-focus-2026-10-20/README.md) preserves
failed experiments, uncertainty, costs and limits. Fresh evaluation precedes any
quality/default claim; Jev remains the target backend.


OntoTF context #59: [paired fresh-request pilot](reports/ontotf-context-2026-10-20/README.md)
finds 7/10 versus 5/10 complete positives with a 27% input-cost increase and one
regression. Exact native binding/target context helps selected decisions; no graph
reasoner or second executor is needed. #60 tracks minimal opt-in production
extraction; #57 remains the broader fresh usefulness/safety/default gate.

Optional catalog integration #60: [production contract](docs/design/issue-60-ontology-context.md)
accepts updated XML snapshots as data with no concept/feature registry edits,
records actual catalog/schema identity and skipped dispositions, and retrieves
bounded complete-target context when catalogs grow. All 134 historical ontology
requests replay identically. Installed-wheel morphology and three safe negatives
pass; additional containment fails and is preserved. [Evidence](reports/ontology-integration-2026-10-20/README.md).
