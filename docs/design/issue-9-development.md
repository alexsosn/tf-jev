# Issue #9 development record

Read entry documents in order, issue #9 and prerequisite contracts. Fetched remote;
no parser PR overlaps this ticket (the separate #29 concerns historical v1 gold).
Actual BHSA metadata probe: TF 13.1.0, 109 node features and six edge features.
Persisted research/design before production behavior.

Observed RED: new parser tests failed collection with missing `tf_jev.parser`.
Implemented the bounded orchestration, then observed a deterministic integer
punctuation failure (`rank greater than 5.` yielded no candidates). Corrected
literal retrieval while keeping decimals, embedded numbers and scientific notation
out of the integer constant domain. Focused tiny native-TF tests GREEN.

Additional tests cover three supported shapes, disjunction and multiple predicates,
minimum probability and margin, immutable evidence/receipts, explicit ambiguity and
unsupported intent, failed candidate verification, malicious typed responses,
sanitary backend errors, per-parse isolation, hard budgets and large-domain retrieval
before value selection. Native TF large-domain fixture independently exercises
complete exact narrowing; no vocabulary fallback occurs on retrieval miss.

Opt-in BHSA integration uses scripted decisions, an actual extracted schema, native
query execution and raw containment/lexeme/edge oracles. It is not a semantic model
quality measurement. No benchmark fixture or heldout request enters production
code or prompt examples. Model evaluation remains #11 and must use an explicitly
frozen designated evaluation partition without tuning on its outcomes.

Freeze the final head, run full relevant tests (including opt-in BHSA), CI on Python
3.11–3.13 and core wheel, then record logically independent adversarial review of the
actual code and native paths on that same head before merge. Production review fixes
must repeat RED → fix → GREEN and require new-head review.
