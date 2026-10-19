# Completing empirical evaluation and baseline comparison (#11, #12)

Research date: 2026-10-20. Read both issues and all reviews of #39/#40, actual
`semantic_evaluation.py`, `run_jev_evaluation.py`, parser, compiler, SDK adapter,
and canonical benchmark loader. Inspected development requests only; heldout
requests/gold are not baseline design inputs. Existing scorer verifies native
projected result fingerprints, not merely counts. It lacks decision-time/parse-time
separation, end-to-end success and explicit abstention precision/recall metrics.
Model failures can consume unreported calls: evidence counts only completed
validated decisions. Do not claim complete billed cost on error outcomes.

Official TypeSafe sources rechecked: https://typesafe.ai/ lists $0.042 per million
input tokens, free output; https://typesafe.ai/blog/jev-1-14 announces 1.14 while
saying versioned 1.13 remains available. Retain the researched 1.13 pin; do not
silently compare an alias. Markdown docs were unavailable through the browser.
Installed SDK 0.7.4 and TF 13.1.0 match the researched contracts. An environment
credential is present (value never inspected or written).

Baseline choice: deterministic English single-atom BHSA annotation adapter, an
explicitly allowed #12 comparator. It shares the full CorpusSchema, QueryIR,
compiler, native oracle and frozen partitions. Rules cover the development
single-atom POS/morphology and exact quoted lexeme forms; complex syntax abstains.
POS mappings are a named BHSA adapter, not generic compiler semantics. Every
mapped symbol/value must validate against the supplied schema. This baseline
measures cheap narrow coverage; it cannot support a claim of superiority over a
generative model. No lookup table keyed by benchmark request/ID or native gold.

IR correctness: native execution equivalence is an observable semantic proxy,
not a proof that two IR structures express identical intent on other corpora.
Report it under its real name; never relabel it as adjudicated IR accuracy.
Retrieval recall: separately audit exact literal `lex` constraints in canonical
single-atom gold using the unchanged parser's local candidate routine; report
eligibility, matches, misses and scope. Gold only enters this post-parse audit,
never model context. Unvisited retrieval due to an earlier abstention is distinct
from a deterministic candidate miss. Other semantic candidate recall is unknown.
