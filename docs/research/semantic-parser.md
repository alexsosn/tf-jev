# Bounded semantic orchestration research (#9)

Read the compiler, CorpusSchema, retrieval and DecisionBackend implementations,
including actual TF 13.1.0 execution/diagnostic conformance tests. Native TF owns
execution. Query atoms fix native result columns; benchmark v2 shows that returning
parents requires explicit projection, separate from existential witness atoms.

JevBackend currently advertises 255 options; retrieval deliberately caps values
at 32. These are different limits. BHSA has substantially more than 32 feature
names; never truncate symbol choices to satisfy an undersized backend. Derive
names, types, descriptions and value domains from the actual schema snapshot.
Use opaque option labels; original corpus strings remain descriptions/local values.

The initial compositional grammar can support one atom, two atoms with a closed
relation, and one parent without a matching embedded child. Each atom can have
up to three different feature predicates and each equality/inequality up to three
alternative values. Unsupported shapes must abstain rather than drop constraints.
This is a bounded prototype, not full coverage of every representable QueryIR.

Integer constants can be retrieved from explicitly written request numbers.
Large string values require deterministic exact lookup of quoted literals or
request tokens before semantic value selection. No fuzzy/translation fallback,
prefix guessing, frequency winner or full vocabulary payload is justified by #7.
If narrowing is empty or exceeds the complete 32-value budget, stop explicitly.
This deliberately limits unquoted multiword/high-cardinality semantic requests.

Ask for support/ambiguity first, then structural/schema decisions, and verify the
whole typed candidate against the original request before compiling. Verification
is a model decision, not proof of semantic correctness. Preserve distributions,
receipts and the weakest selected probability; apply probability and margin gates
to every choice. A custom backend must be revalidated against each actual question,
even if it returns already-constructed Decision objects.

Data flow: the backend sees the user request, selected structure, schema symbol
names/descriptions, small categorical domains and only locally retrieved literal
values for large domains. These values may themselves be text-bearing annotations
when explicitly selected as predicates; that bounded disclosure is needed to choose
an annotation value. No TF text rendering, node passages, full inventories or source
paths are sent. Schema and user prose are untrusted and pass the decision contract.

No benchmark fixture is imported by production code. Synthetic orchestration tests
and actual BHSA execution prove boundaries, not model accuracy. Keep v2 heldout out
of examples/tuning; #11 must measure parser quality and replace a holdout after tuning
informed by evaluation. Do not claim semantic quality from scripted decisions.

BHSA integration observation: `lex` is populated on both `word` and `lex` nodes
(8,769 distinct values each). Raw feature-value lookup alone does not establish
requested node type. Corpus oracles must explicitly retain object-type constraints;
BR>[ has 48 word nodes plus a separate lexeme node. This is why parser choices
and validation retain per-(feature, object type) domains.
