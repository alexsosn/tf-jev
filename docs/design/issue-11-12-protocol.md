# Frozen evaluation protocol (#11, #12)

Freeze before live measurement or heldout inspection. No parser/policy/prompt
changes in this work. Benchmark v2 stays byte-identical. Record package commit,
benchmark hash, source hashes, schema identity, TF/SDK/Python versions, pinned
model, selection completeness, date and explicit price provenance.

Run a one-case development connectivity probe, then full development (52) and
full heldout (57) on Jev 1.13; errors remain outcomes, not cherry-picked retries.
If service/auth is unavailable, preserve the failed attempt and report the model
comparison blocked rather than inventing accuracy. Use default ParsePolicy and
maximum 64 decision calls per request. Bounded full run: at most 6976 decisions
across 109 cases, with default context bound 32768 characters per decision.
No key or .env is copied into artifacts. Only bounded annotation symbols/values
and requests go to the service; no rendered corpus passages.

Heldout go/no-go (all mandatory for a default-backend recommendation):
- supported result equivalence >= 0.80;
- safe negative decisions >= 0.95, zero unsafe supported negative predictions;
- every emitted supported query compiles and executes natively;
- parser/backend error fraction <= 0.05;
- parse latency p95 <= 10 seconds;
- complete known estimated token cost mean <= $0.001 per request.
Unknown/incomplete metrics mean NOT ESTABLISHED, never a pass. Thresholds are
engineering targets, not statistically validated production guarantees.

TDD scope: add missing scorer metrics and conservative baseline with deterministic
real tiny-TF tests before implementation. Baseline supports only full anchored
atomic patterns: POS (with optional gender+number) and exact quoted lex feature
values. BHSA lexical/POS mapping is explicit; other forms return UNSUPPORTED.
No feature candidate is inferred from gold. Baseline has zero model calls/cost;
execution and schema costs still count in wall timing.

Report strict classification, native validity, exact text, projected result
identity, operational safe-negative precision/recall (abstention includes explicit
AMBIGUOUS/UNSUPPORTED/ABSTAINED but excludes ERROR), end-to-end success
(equivalent supported + safe negative)/all, parse and wall latency, receipt
latency, usage/cost completeness, error causes and family breakdowns. IR intent
accuracy remains unadjudicated; result equivalence is clearly a proxy.

Separate per-case reports for each system/partition plus a concise comparison
with paired outcome counts. Same cases/schema/IR/compiler/native scorer. Freeze
baseline and scoring code before heldout execution; do not tune after results.
Exact-head tests, real BHSA replay and logically independent adversarial review
are merge gates. Comparison can establish a no-go; lack of Jev advantage is an
acceptable research result. One canonical PR for the coherent #11/#12 report.

## Independent intent adjudication

After inference is frozen, review every emitted candidate's compiled structure
against the request, gold annotation semantics and requested output roles. Since
the compiler deterministically preserves the validated typed structure, this is
an audit of IR intent rather than a string-equality score. Record manual
correct/incorrect/absent labels, reasons for errors and conditional emitted-IR
precision separately from supported-gold end-to-end IR recall. Non-emission is
not an incorrect IR construction, but earns no supported request success. Do not
substitute result equivalence for this audit, especially for empty results.
Manual single-reviewer adjudication is evidence, not a formal equivalence proof
or an independent human annotation campaign. It must not change parser/rules.
