# First semantic parser contract (#9)

`SemanticParser(schema, backend, policy=ParsePolicy()).parse(request)` returns a
frozen ParseResult with status, static reason, QueryIR/native text only on success,
ordered output atom columns (distinct tuples), aggregate confidence, immutable
per-question evidence and backend receipts. No native execution occurs here.
The compiler is the sole renderer; selected symbols are schema-derived or validated.

Statuses: supported, ambiguous, unsupported, abstained, error. Low probability or
small winning margin produces abstained; recognized unsupported shapes/intent and
retrieval miss/budget failures produce unsupported. Backend/contract/schema failures
produce sanitized error reasons. Every non-supported result clears query, IR and
projection. Backend exceptions never become result/error text.

Stages: choose shape or abstention; choose atom types; choose predicate counts;
choose distinct features and compatible operators; choose value counts and bounded
values; choose a relation (and attested edge / explicit integer distance as needed);
choose output atom order; verify candidate fidelity; compile. Without's child is a
body atom, not an output column. All field choices use opaque local labels and are
revalidated against the questions before resolving them. Per-call contexts identify
the current atom/feature and prior choices, never complete schema inventories.

Defaults: probability >=0.8, margin >=0.2, <=255 symbol choices, <=32 retrieved
values/seeds, <=64 calls, <=8192 request characters. Limits never truncate a choice
domain silently. The minimum selected probability is conservative evidence, not a
calibrated probability of whole-query correctness. Singleton decisions still remain
in evidence; binary candidate verification is represented as a bounded choice.

Test gates: fake backend with actual tiny-schema compilation/native execution;
low confidence on an early structural decision; no query on unsupported/ambiguous
or failed verification; forged typed responses, transport errors, invalid inputs,
bounded retrieval, integer bounds, output role order and without arity. Opt-in BHSA
integration exercises a real schema and native result oracle. No heldout cases or
live model calls enter deterministic tests. #11 owns model quality/cost evaluation.
