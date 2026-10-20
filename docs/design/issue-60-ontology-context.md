# Optional growing-catalog context (#60)

## Research

#59 measured the small value-mapping context decorator: 7/10 versus 5/10 complete
positives, one imperative admission regression and 27% input-cost increase. The
pilot is observed; extraction replay is regression evidence, never fresh quality.
Current ontoTF 3b55d29a6435f2bfa98aa8be37ab6aeee57d09ac still uses the researcher-
first XML catalog (kinds node/feature/value/edge/entity; relation exact/close/
broader/narrower/related/ambiguous/native-only/unsupported). New corpus XML files
are discovered upstream. No need to import its legacy release/profile machinery.
Generic tf-jev must consume a caller-selected local XML file, not a fixed corpus,
concept/feature registry or a bundled stale copy. New value mappings are data;
new query structures still require compiler support. No graph HTTP fetch/executor.

## Public design before code

New tf_jev.ontology module, with no optional runtime dependency:
- load_catalog(path, schema, corpus=..., version=..., revision=None,
  expected_sha256=None) -> immutable OntologyCatalog.
- OntologyParser(schema, backend, catalog=catalog, policy=GroundedPolicy()) is an
  explicit CandidateParser wrapper. Old parser/model/defaults remain unchanged.
- OntologyParseResult extends ParseResult with catalog identity (XML SHA256,
  caller revision, root corpus/source/version, bound schema key, row/disposition
  counts) and per-stage context selections (scope count, selected count, mode).
  No raw paths, request prose or mapping values in diagnostics. A mismatched
  schema/catalog fails before model calls. XML labels cannot prove semantic
  applicability: caller selects the appropriate source/version; selector checks
  prove membership only, not cross-corpus meaning or identity.

Loader validates UTF-8 (DTD/entities refused), known XML structure/attributes,
absolute target IRIs, root/source/version, duplicate records and exact native
selectors including integer feature literals. Known non-exact relations and
non-value kinds are counted/skipped explicitly, never promoted to exact value
semantics. Empty labels/unknown structures fail closed with sanitized errors.
Read at most 2 MiB + 1; at most 10,000 local records, strings bounded to 1024
characters. These are resource caps, not hardcoded ontology coverage lists.
Catalog immutable snapshots don't change mid-query when the file is updated.
Expected digest is optional for ordinary use, explicit for reproducible evaluation.

Extract measured own-state relevance and context wording exactly for fitting
catalogs: feature stage uses native type; value/operator/count uses type+feature;
final candidate includes its own predicates and exclusion child scopes. No shape/
type/output/relation changes. All native options and receipts remain untouched.
Avoid a second query planner. New catalogs can be loaded with the same code.

Growing catalog policy: preserve the complete scoped context when <=8192 bytes
and within total request budget. Otherwise narrow metadata locally by lexical
overlap of original request and target labels (split CamelCase, lowercase words,
normalize a trailing s for simple plurals); include ALL scoped bindings of each
matched target so broad Noun's multiple native values cannot be partially sent.
No arbitrary top-K truncation, feature/ontology name allowlist or query generation.
If that complete relevant subset is empty/too large, omit optional ontology context
and record why; preserve the original request/choices rather than truncate or
invent ontology coverage. This is bounded retrieval of auxiliary descriptions,
not removal of native values or a completeness claim. Unmatched synonyms may lose
extra help; no default-quality claim for this unmeasured overflow path.
All complete requests still respect serialized byte limits. Base requests over
budget refuse before transport. Parser creates per-call adapter state so no
cross-request diagnostics/history leaks. Total budget follows parser policy.

## Gates

Production-import RED before source. Meaningful native/SDK regressions, exact
versus approximate/native-only, suffix/parent scope, mismatches, hostile UTF-16/
entities/unsafe text, integer values, updates/new labels without code edits,
overflow complete-target retrieval, immutable snapshots and diagnostic identity.
Replay every #59 ontology transcript through the production parser without model
calls, matching decisions/query/projection. Keep historical reports byte-identical.
Freeze source, full exact-head suite, adversarial native/data review, wheel build
and once-only installed-wheel live positive/safe-negative NL smoke with durable
per-call accounting before merge. New catalogs affect interpretations: evaluate
changes explicitly, never reuse the pilot as fresh evidence.

## Implementation gates recorded

Initial production tests failed collection before tf_jev.ontology existed.
Native loader/parser, snapshot update/new concept, exact versus skipped relation,
integer selectors, schema mismatch, UTF-16/DTD, growth retrieval/whole-target
omission, SDK/witness scopes, weak proposal/final verification, sanitized errors,
request-local history and size limits pass. The #59 ontology arm replays all 14
trajectories / 134 actual model requests identically through the public parser;
no inference or gold changes. The current ontoTF revision and the pilot revision
both load through the same generic loader. Neither catalog is bundled in the
package. Historical pilot remains immutable regression evidence.

Installed-wheel live smoke preregistration: use the existing synthetic native TF
fixture with honest part-of-speech/gender/number descriptions, plus a local tiny
XML catalog derived from those fixture meanings. Run once each: feminine-singular
noun words (node2), phrases containing verb words (10,12,13), ambiguous complements,
unsupported counting per phrase, and a named missing annotation. Jev 1.14.0,
SDK0.7.4, retries0, timeout30, known usage budget $.01 / max100 calls; save each
attempt's usage/error/latency atomically before a further call, save results per
case, never replace outcomes. Inputs/results are packaging regression, not fresh
quality evidence. Recheck official price before client creation. Native expected
sets derive directly from fixture annotations/slots, with no gold in model context.

## Live outcome

Once-only installed wheel smoke: morphology positive and all three negatives
pass; additional containment positive fails unsupported/no_candidates. Preserve
that failure without rerun. All containment stage diagnostics were unmapped, so
no ontology payload was added on that trajectory. Twenty-seven calls, all usage
known, no API errors, $.001012032. #57 owns further usefulness/structural coverage;
no default or complete-success claim. Exact historical production replay still
matches all 134 requests/results.
