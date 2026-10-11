# Deterministic candidate retrieval — issue #7

`RetrievalIndex.from_schema(schema, handle, normalization=Normalization.EXACT)`
accepts only an existing Large string-domain handle. It snapshots a sorted local
index. NFC and NFC_CASEFOLD are explicit alternatives. No corpus-specific symbols,
labels, gloss relationships or frequencies influence ranking. Schema provenance
is retained in the handle; mismatched/stale handles fail through SchemaError.

`lookup(text, match=Match.EXACT, limit=32)` returns an immutable RetrievalResult:
`candidates` (opaque label, original string, attestation count), `total_matches`,
`truncated`, and the source handle. Limit is a plain integer in [1,32]. Prefix
lookup rejects an empty normalized key so it cannot accidentally enumerate the
entire domain; exact empty lookup remains valid. Results order by normalized key,
then original string, independent of TF item insertion order. Counts never select
a winner. All equal normalized keys remain distinct exact corpus values.

The result stores at most the limit, while counting all matches. Overflow is
explicit even when the retained list contains a gold value. `as_question(prompt)`
refuses overflow/no-match before constructing backend-neutral ChoiceQuestion;
its options contain only the bounded retained values, with opaque ASCII ids.
`resolve(label)` refuses incomplete/no-match results and unrequested labels.
Descriptions are validated by the existing decision contract, so corpus controls
are rejected before a backend sees them. Schema membership does not guarantee
compiler expressibility; the compiler still validates a resolved literal.

The caller chooses the lookup strategy and normalization based on its researched
feature contract. These are local retrieval operations, not semantic decisions.
Ambiguity is the retained alternative set; confidence/abstention belong to the
parser (#9). There is no automatic winner, fuzzy fallback, translation or network.
Full local vocabularies never become choice options. Internal immutable entries
are not a serialization/model payload. Re-extract/rebuild after corpus changes.

Gates: deterministic API tests first, real TF synthetic large domains and
compiler execution, frozen BHSA lookup benchmark with raw-feature gold oracles,
then exact-head checks and separate adversarial review using raw TF data.

Runtime construction checks also enforce the result budget, unique labels/values,
positive attestation counts, integer totals and copied immutable candidate tuples.
This prevents manually constructed results bypassing the bounded handoff contract.
