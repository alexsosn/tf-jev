"""Reviewed typed-IR witnesses for BHSA 2021 tutorial-derived gold pairs.

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
    "clauses-distance-one": Query((Atom("clause", (Predicate("dist", P.EQ, (1,)),)),)),
    "clauses-distance-less-minus-ten": Query(
        (Atom("clause", (Predicate("dist", P.LT, (-10,)),)),)
    ),
    "clause-adjacent-phrases": Query(
        (Atom("clause"), Atom("phrase"), Atom("phrase")),
        (
            Relation(0, R.EMBEDS, 1),
            Relation(0, R.EMBEDS, 2),
            Relation(1, R.ADJACENT_BEFORE, 2),
        ),
    ),
    "sentence-clause-phrase-order": Query(
        (Atom("sentence"), Atom("clause"), Atom("phrase"), Atom("clause")),
        (
            Relation(0, R.EMBEDS, 1),
            Relation(0, R.EMBEDS, 2),
            Relation(0, R.EMBEDS, 3),
            Relation(1, R.BEFORE, 2),
            Relation(3, R.AFTER, 2),
        ),
    ),
    "pp-prep-adj-noun": Query(
        (
            Atom("phrase", (eq("typ", "PP"),)),
            Atom("word", (eq("sp", "prep"),)),
            Atom("word", (eq("sp", "adjv"),)),
            Atom("word", (eq("sp", "subs"),)),
        ),
        (
            Relation(0, R.EMBEDS, 1),
            Relation(0, R.EMBEDS, 2),
            Relation(0, R.EMBEDS, 3),
            Relation(1, R.ADJACENT_BEFORE, 2),
            Relation(2, R.ADJACENT_BEFORE, 3),
        ),
    ),
    "complex-verbal-negations": Query(
        (
            Atom(
                "word",
                (
                    eq("sp", "verb"),
                    Predicate("vs", P.NE, ("qal",)),
                    Predicate("vt", P.NE, ("infc", "infa", "ptca", "ptcp")),
                    Predicate("ps", P.NE, ("p3",)),
                    Predicate("nu", P.NE, ("sg",)),
                    Predicate("gn", P.NE, ("m",)),
                ),
            ),
        )
    ),
    "object-clause-first-lexeme": Query(
        (
            Atom("verse"),
            Atom("clause", (eq("rela", "Objc"),)),
            Atom("word", (eq("lex", ">CR"),)),
        ),
        (
            Relation(0, R.EMBEDS, 1),
            Relation(1, R.EMBEDS, 2),
            Relation(1, R.SAME_START, 2),
        ),
    ),
    "complex-predicate-object-lexemes": Query(
        (
            Atom("clause"),
            Atom("phrase", (Predicate("function", P.EQ, ("Pred", "PreC")),)),
            Atom("word", (eq("sp", "verb"), eq("vs", "hif"), eq("lex", "QWM["))),
            Atom("phrase", (eq("function", "Objc"),)),
            Atom("word", (eq("lex", "BRJT/"),)),
        ),
        (
            Relation(0, R.EMBEDS, 1),
            Relation(1, R.EMBEDS, 2),
            Relation(0, R.EMBEDS, 3),
            Relation(3, R.EMBEDS, 4),
        ),
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
