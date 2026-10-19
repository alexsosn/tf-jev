# Research: localizing complete Jev abstention (#46)

2026-10-20. Read the mandatory entry documents, #46, all PR #44 review discussion,
actual parser `_Run.choose/build/atom`, SDK adapter and measurement code. No open
implementation overlaps. The previous study did not preserve stage IDs or full
distributions, so its low-confidence outcome cannot by itself identify the cause.

Current parser asks shape -> atom type -> predicate count -> feature/operator/
value -> relation/output -> whole-candidate verification. Each completed question
already has a validated distribution and receipt in ParseResult.evidence. Weak
probability (<.80) or margin (<.20) stops immediately. Context holds request,
JSON selected descriptions and a generic untrusted-data contract. The first
shape question has no corpus inventory, and uses atom/predicate jargon. A broad
unsupported-semantics classification at that stage is inherently under-informed.
This is a hypothesis to investigate, not a proven explanation.

Official docs rechecked against SDK 0.7.4:
- https://docs.typesafe.ai/primitives/choice : question IDs are not model input;
  option names AND descriptions are. Descriptions should distinguish categories;
  Choice supports 255 options. Multiple questions are independent against state.
- https://docs.typesafe.ai/model-jaggedness/jev-1.13 : documented jaggedness is a
  reason for controlled tests, not a substitute for observing our own failures.
- Adapter still pins jev-1.13.0 and validates responses; keep that pin and default
  policy to isolate orchestration from backend/version drift.

A checkout-only proxy can observe requests/responses without changing production
parser behavior or adding logging to generic schema/compiler/backend layers.
Store only static stage IDs, option counts, selected POSITION, numeric validated
probabilities/margins, attempt/error/usage timing. No descriptions/labels/contexts,
requests, query text, raw exceptions or credential-bearing objects in reports.
Do not pretend the last backend question caused a non-decision retrieval/budget
stop; mark it as the last observed question and name a stopping question only
when that is justified by low_confidence/intent/verification semantics.

Only DEVELOPMENT cases enter new inference. Canonical first-per-development-
family representatives provide 8 diagnostic probes without selecting favorable
cases after seeing traces. Observe exact controls twice and compare option order,
semantic labels, plain shape wording, context ablation and five independent
binary shape decisions (cardinality/decomposition). These are mechanism probes,
not a new model-quality score. Gold never goes to a backend. No automatic query
execution from a probe; the real parser alone constructs any typed IR.
