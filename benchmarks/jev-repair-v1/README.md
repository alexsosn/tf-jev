# Jev repair development witnesses

Four DEVELOPMENT requests frozen before new model inference for #56. Serialization
reuses nl-tf-v2; dataset identity is jev-repair-v1. No heldout/generalization claim.
Use alongside the already observed grounded-v1 development set, not as a replacement
for its failures. Native TF 13.1.0 / BHSA 2021 source gates remain mandatory.

The two positives specify ordered adjacent word pairs and returned parent phrases
with verb witnesses. Independent raw sp annotations restricted to word slot nodes,
slot-successor arithmetic and oslots intersections produce counts/signatures equal
to native compiled execution: 15,336 ordered pairs and 73,459 distinct phrases.
The first raw-oracle draft failed because sp also annotates lexeme nodes; restricting
BOTH sides to the requested word node type reconciled it before gold freeze. No
model was called and no gold observation replaced during that correction.

The two negatives explicitly name an absent feature (checked against full schema)
and a regex outside the typed compiler subset. No query should be emitted for them.
Data file SHA256:
2a7e8faca965ae7ece61f4097f4b5c472d88d9682c0fc717cc2b4edf709bf9ec.

Independent same-context semantic/native review: adjacency returns (verb, substantive)
in that order; containment returns phrases only, not word witnesses. Raw oracle
construction uses native annotations/slots without compiler/search for derivation.
No passage or model gold is involved. All four become observed development evidence
when inferred; fresh reviewed heldout evaluation is still required before a default.
