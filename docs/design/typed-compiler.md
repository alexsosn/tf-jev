# Typed compiler contract (#3)

Research/design, 2026-10-11. Authority: Text-Fabric 13.1.0 `search/syntax.py`,
`search/semantics.py`, `search/spin.py`, and the existing native conformance
suite. The corpus-schema research establishes empty alternatives and exact,
per-type value membership. No external service is used by this compiler.

## Boundary

`compile_query(Query, SymbolSchema) -> str` is pure. `SymbolSchema` exposes
`object_types`, `node_feature_type(feature, object_type)`,
`validate_value(feature, object_type, value)`, and `validate_edge(feature)`.
The latter methods raise ValueError for unavailable symbols/values. #5 owns
extraction and immutable snapshots; tests here implement this protocol directly
against loaded TF feature dictionaries. Compiler checks grammar expressibility
as well as consulting the schema, including in quantifier bodies.

Frozen dataclasses carry tuples: Query(atoms, relations, without),
Atom(object_type, predicates), Predicate(feature, operator, values),
Relation(source, operator, target, edge, distance), Without(parent, body).
References are integer positions within that query, or Parent.REF only in a
without body. Names are generated globally, avoiding every corpus type.
Predicates and relation lines are sorted; atom order determines output columns.
Values are exact str/int data, never syntax; booleans are not integers.

Closed enums expose equality/inequality sets, presence/absence, strict integer
bounds; embedding, slot-set/boundary/order relations, bounded near relations
(K_MAX=1000), and valueless forward/backward/either edge traversals.
The edge may carry values in the corpus but its values cannot be constrained.
Exactly one nonempty, connected without body per parent is permitted. It must
connect all its atoms to Parent.REF through relations. Nested quantifiers,
regexes, arbitrary relation strings, named sets, duplicate feature predicates,
empty queries, disconnected graphs, and two-sided bounds on one atom are
explicit errors. Set alternatives use one predicate; callers cannot rely on
TF's silent last-condition-wins behavior. Identity is deferred per #2.

## Native hazards

Values containing C0 controls, DEL, other whitespace except ASCII space, or
surrogates are rejected: Python's `split()` recognizes Unicode whitespace and
would silently alter tokens. Values are never Unicode-normalized. Backslashes,
spaces and pipes are escaped in that order. A singleton empty string emits `|`.
Escaped predicates on quantified parents use a continuation line beginning
with equality/inequality; other predicates remain on the atom line. Bodies
remain at indent zero and refer to the parent only in relation lines.

The compiler executes no TF search. Integration tests are the authoritative
native oracle and use explicit limits. A production TF validation/execution
wrapper, including diagnostic and overflow classification, belongs with the
public/evaluation API (#11/#13), rather than introducing TF private calls into
a pure deterministic renderer. Successful compilation establishes structural
validation, not execution or result-size guarantees.

## Test gates

RED: tests import the intended API before it exists. Unit/error tests cover all
operators, symbol/value mismatches, runtime type attacks, deterministic output,
connectivity, references and quantifier scope. Native tests compare exact tiny
corpus results and selected BHSA 2021 gold queries, including escaped parents.
Full lint/types/unit/conformance tests run on a frozen commit, followed by a
separate skeptical review with independently constructed adversarial cases.
