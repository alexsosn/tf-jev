# Issue #7 development gates

Research and design were persisted before production behavior in
candidate-retrieval research/design documents. Actual TF/BHSA feature probes
established Unicode collisions, cardinalities and broad-prefix overflow.

RED: `pytest tests/test_retrieval.py -q` failed collection with
`ModuleNotFoundError: tf_jev.retrieval` before implementing the intended API.
The synthetic fixture was then corrected to include a non-slot node, otext and
native TF.save escaping, and to load a fresh Fabric after save. Tab is allowed
by the existing prose contract; a bidi override tests forbidden model prose.
GREEN: initial five API tests passed, including retrieved-literal native searches.

A separate constructor-boundary regression failed with “DID NOT RAISE” for a
33-candidate manually constructed result. Added runtime budget/type/uniqueness
checks and immutable copying; regression passed. A 33-way canonical combining
mark collision additionally verifies overflow cannot silently choose one variant.
Changed loaded feature data invalidates handles while old snapshots stay stable.

Frozen BHSA benchmark: 52 cases, 48/50 gold inclusion; both misses are explicit
prefix overflows, blocked at handoff. Complete sets include 48/48 eligible gold
values. Three absent cases remain no-match. No semantic-model quality claim.

Final commit, full tests, independent review and CI are recorded in the PR
because those observations follow the frozen commit.
