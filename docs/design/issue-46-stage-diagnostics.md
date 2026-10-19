# Plan/design: development-only stage diagnosis (#46)

Research -> deterministic RED -> transparent tracing -> full development trace ->
frozen paired mechanism probes -> exact-head tests and independent review.
No production parser, confidence threshold or benchmark edits in this diagnostic
increment. A parser revision is conditional on evidence, with a separate design,
RED/calibration on development and a new independently frozen evaluation set.
V2 heldout cannot certify a revised parser after its results have been observed.

Implement checkout-only `scripts.diagnose_abstention`:
- TraceBackend proxy delegates unchanged requests and returns the identical batch.
  Revalidate a copy against the exact request before reporting distributions; a
  malformed response is recorded as a static contract error, never raw text.
  Preserve backend exceptions for the parser to sanitize, while recording safe
  error kind and unknown usage. Store one receipt per call, multiple questions
  nested within that call so batch usage is never multiplied.
- Diagnostic summaries contain development IDs/families/status/reason, a justified
  stopping question, last observed question and all call-level records. Candidate
  positions are numeric; names/descriptions/request text remain in memory only.
- Deterministic tests prove trace/nontrace ParseResult identity on real tiny TF,
  exact low-confidence stage identification, unknown usage on failed calls,
  raw-text/credential-like data exclusion, and no duplicated batched usage.
- Runner verifies all 116 source hashes from the frozen study plus the canonical
  source/TF gates before loading full schema/client. Requires --live and
  TF_JEV_LIVE=1, an explicit positive max-cases (<=52) and a new output path.
  No heldout option. Record source/benchmark/code/schema/model/version provenance
  and honest prefix completeness. Fresh output must not overwrite prior results.
- Full initial trace: all 52 development requests under unchanged ParsePolicy.
  Every failed attempt remains an outcome. Usage estimates use .042 USD/million
  input and free output as checked in #11/#12, not billed cost.
- Probes: first development case in each of 8 families, in canonical order,
  independent of observed success. Capture original shape question in memory;
  two controls then two replicates of each variant, fixed order. Variants:
  reverse choices preserving label-description pairs; semantic shape labels with
  explicit bijective position mapping; plain English equivalent shape wording;
  request-only context; and five separate yes/no class questions batched once.
  All five original alternatives remain represented, never truncate options.
  Decomposed probes are independent (not a five-way probability distribution);
  no forced winner on conflicting/uncertain outcomes. Report per-case distributions
  and variation, not apparent downstream accuracy or causal certainty from one run.

Follow-up decision: distinguish earliest blocking stages, probe effects versus
control variation, and what remains unidentifiable. No threshold lowering from
these traces and no default recommendation. If no bounded change is justified,
preserve the no-go and propose a specific next research gate instead of shipping
an unsupported parser rewrite.
