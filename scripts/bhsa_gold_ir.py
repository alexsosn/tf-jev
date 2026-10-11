"""Reviewed typed-IR witnesses for six BHSA 2021 tutorial-derived gold pairs.

These are research fixtures, not semantic-parser rules, model examples or a
mechanism for turning untrusted text into native search queries.
"""

from __future__ import annotations

from typing import Any

from scripts.nl_benchmark import Catalog, equivalent
from tests.test_compiler import NativeSymbols
from tf_jev.compiler import compile_query
from tf_jev.ir import Atom, Predicate, PredicateOp, Query, Relation, RelationOp

P = PredicateOp
R = RelationOp


def eq(feature: str, value: str) -> Predicate:
    return Predicate(feature, P.EQ, (value,))


PROMOTED_IR: dict[str, Query] = {
    "words-all": Query((Atom("word"),)),
    "feminine-plural-substantives": Query(
        (Atom("word", (eq("sp", "subs"), eq("gn", "f"), eq("nu", "pl"))),)
    ),
    "qere-present": Query((Atom("word", (Predicate("qere", P.PRESENT),)),)),
    "qere-missing": Query((Atom("word", (Predicate("qere", P.ABSENT),)),)),
    "samuel-proper-noun-context": Query(
        (
            Atom("book", (eq("book", "Samuel_I"),)),
            Atom("clause"),
            Atom("word", (eq("sp", "nmpr"),)),
        ),
        (Relation(0, R.EMBEDS, 1), Relation(1, R.EMBEDS, 2)),
    ),
    "same-slots-verse-sentence": Query(
        (Atom("verse"), Atom("sentence")),
        (Relation(0, R.EMBEDS, 1), Relation(0, R.SAME_SLOTS, 1)),
    ),
}


def validate_promotions(api: Any, catalog: Catalog) -> int:
    """Fail closed unless each typed witness has identical full native tuple output."""
    indexed = {case.id: case for case in catalog.cases}
    for case_id in PROMOTED_IR:
        case = indexed.get(case_id)
        if (
            case is None
            or case.status != "supported"
            or case.split not in {"train", "development"}
            or case.gold_query is None
            or case.expected_count is None
        ):
            raise ValueError("promoted BHSA gold case is absent, sealed or malformed")
    schema = NativeSymbols(api)
    for case_id, query in PROMOTED_IR.items():
        compiled = compile_query(query, schema)
        gold = indexed[case_id].gold_query
        assert gold is not None
        if not equivalent(api, gold, compiled):
            raise ValueError(f"promoted BHSA gold tuple mismatch: {case_id}")
    return len(PROMOTED_IR)
