"""Compiler contract tested with symbols/values from actual loaded Text-Fabric."""

from __future__ import annotations

from typing import Any, Literal

import pytest

from tests.conformance.tf_harness import run_template
from tf_jev.compiler import K_MAX, CompileError, compile_query
from tf_jev.ir import Atom, Parent, Predicate, Query, Relation, Without
from tf_jev.ir import PredicateOp as P
from tf_jev.ir import RelationOp as R


class NativeSymbols:
    """Test-only protocol adapter; production extraction is issue #5."""

    def __init__(self, api: Any) -> None:
        self.api = api
        self.object_types = tuple(level[0] for level in api.C.levels.data)

    def node_feature_type(self, feature: str, object_type: str) -> Literal["str", "int"]:
        if feature not in self.api.Fall():
            raise ValueError("unknown feature")
        if not self.api.Fs(feature).freqList({object_type}):
            raise ValueError("feature unavailable on type")
        dtype = self.api.TF.features[feature].dataType
        assert dtype in ("str", "int")
        return dtype  # type: ignore[no-any-return]

    def validate_value(self, feature: str, object_type: str, value: str | int) -> None:
        if value not in dict(self.api.Fs(feature).freqList({object_type})):
            raise ValueError("unknown value")

    def validate_edge(self, feature: str) -> None:
        if feature not in self.api.Eall():
            raise ValueError("unknown edge")


def pred(feature: str, op: P, *values: str | int) -> Predicate:
    return Predicate(feature, op, values)


def execute(api: Any, query: Query) -> tuple[tuple[int, ...], ...]:
    outcome = run_template(api, compile_query(query, NativeSymbols(api)), limit=500000)
    assert outcome.ok, outcome.error_text()
    assert outcome.results is not None
    return outcome.results


@pytest.mark.parametrize(
    "feature,value,expected",
    [
        ("lex", "a b", 5),
        ("lex", "a|b", 6),
        ("lex", "a\\b", 7),
        ("lex", "בָּרָא", 8),
        ("suffix", "", 1),
        ("rank", 3, 3),
    ],
)
def test_literal_native_membership(
    tiny_api: Any, feature: str, value: str | int, expected: int
) -> None:
    rows = execute(tiny_api, Query((Atom("word", (pred(feature, P.EQ, value),)),)))
    assert (expected,) in rows
    if value != "":
        assert rows == ((expected,),)
    else:
        assert rows == ((1,), (3,))


@pytest.mark.parametrize(
    "op,values,gold",
    [
        (P.EQ, ("", "H"), "word suffix=|H"),
        (P.NE, ("",), "word suffix#|"),
        (P.PRESENT, (), "word suffix"),
        (P.ABSENT, (), "word suffix#"),
        (P.GT, (2,), "word rank>2"),
        (P.LT, (5,), "word rank<5"),
    ],
)
def test_predicates_native(tiny_api: Any, op: P, values: tuple[str | int, ...], gold: str) -> None:
    feature = "rank" if op in (P.GT, P.LT) else "suffix"
    assert (
        execute(tiny_api, Query((Atom("word", (Predicate(feature, op, values),)),)))
        == run_template(tiny_api, gold, limit=100).results
    )


@pytest.mark.parametrize(
    "op",
    [
        r
        for r in R
        if r not in (R.EDGE_FORWARD, R.EDGE_BACKWARD, R.EDGE_EITHER, R.NEAR_BEFORE, R.NEAR_AFTER)
    ],
)
def test_relations_native(tiny_api: Any, op: R) -> None:
    query = Query((Atom("phrase"), Atom("word")), (Relation(0, op, 1),))
    assert (
        execute(tiny_api, query)
        == run_template(tiny_api, f"a:phrase\nb:word\na {op.value} b", limit=100).results
    )


@pytest.mark.parametrize("op", [R.EDGE_FORWARD, R.EDGE_BACKWARD, R.EDGE_EITHER])
@pytest.mark.parametrize("edge,otype", [("mother", "clause"), ("dist", "word")])
def test_edge_traversal(tiny_api: Any, op: R, edge: str, otype: str) -> None:
    query = Query((Atom(otype), Atom(otype)), (Relation(0, op, 1, edge=edge),))
    rows = execute(tiny_api, query)
    assert rows


@pytest.mark.parametrize("op", [R.NEAR_BEFORE, R.NEAR_AFTER])
@pytest.mark.parametrize("distance", [0, 1, K_MAX])
def test_near_native(tiny_api: Any, op: R, distance: int) -> None:
    query = Query((Atom("word"), Atom("word")), (Relation(0, op, 1, distance=distance),))
    native = f"<{distance}:" if op is R.NEAR_BEFORE else f":{distance}>"
    assert (
        execute(tiny_api, query)
        == run_template(tiny_api, f"a:word\nb:word\na {native} b", limit=100).results
    )


@pytest.mark.parametrize("value,expected", [("a b", ((5,),)), ("a|b", ()), ("a\\b", ((7,),))])
def test_quantified_escaped_parent(
    tiny_api: Any, value: str, expected: tuple[tuple[int, ...], ...]
) -> None:
    # Exclude words immediately followed by an adjective: only word 6 has this property.
    body = Query(
        (Atom("word", (pred("sp", P.EQ, "adjv"),)),), (Relation(Parent.REF, R.ADJACENT_BEFORE, 0),)
    )
    query = Query(
        (Atom("word", (pred("lex", P.EQ, value), pred("sp", P.PRESENT))),),
        without=(Without(0, body),),
    )
    assert execute(tiny_api, query) == expected
    rendered = compile_query(query, NativeSymbols(tiny_api))
    assert "\n  lex=" in rendered
    assert "\n/without/\n" in rendered


def test_clause_without_predicate_phrase(tiny_api: Any) -> None:
    body = Query(
        (Atom("phrase", (pred("function", P.EQ, "Pred"),)),),
        (Relation(0, R.EMBEDDED_IN, Parent.REF),),
    )
    assert execute(tiny_api, Query((Atom("clause"),), without=(Without(0, body),))) == ((15,),)


def test_deterministic_sets_and_order(tiny_api: Any) -> None:
    a = pred("sp", P.EQ, "verb", "subs", "verb")
    b = pred("gn", P.EQ, "f")
    symbols = NativeSymbols(tiny_api)
    assert (
        compile_query(Query((Atom("word", (a, b)),)), symbols)
        == compile_query(Query((Atom("word", (b, pred("sp", P.EQ, "subs", "verb"))),)), symbols)
        == "n0:word gn=f sp=subs|verb"
    )


@pytest.mark.parametrize(
    "predicate",
    [
        pred("unknown", P.PRESENT),
        pred("lex", P.EQ, "invented"),
        pred("lex", P.GT, 2),
        pred("rank", P.EQ, "3"),
        pred("rank", P.EQ, True),
        pred("sp", P.PRESENT, "verb"),
        pred("sp", P.EQ),
        pred("rank", P.GT, 1, 2),
        pred("otype", P.PRESENT),
        pred("lex\n/without/", P.PRESENT),
        pred("lex", P.EQ, "x\nword"),
        pred("gloss", P.EQ, "tab\there"),
        pred("lex", P.EQ, "x\u00a0y"),
        pred("lex", P.EQ, "\ud800"),
        Predicate("lex", "=", ("a b",)),  # type: ignore[arg-type]
    ],
)
def test_invalid_predicates(tiny_api: Any, predicate: Predicate) -> None:
    with pytest.raises(CompileError):
        compile_query(Query((Atom("word", (predicate,)),)), NativeSymbols(tiny_api))


@pytest.mark.parametrize(
    "query",
    [
        Query(()),
        Query((Atom("unknown"),)),
        Query((Atom("word\nword"),)),
        Query((Atom("word"), Atom("word"))),
        Query((Atom("word"),), (Relation(0, R.OVERLAP, 1),)),
        Query((Atom("word"),), (Relation(Parent.REF, R.OVERLAP, 0),)),
        Query((Atom("word"),), (Relation(True, R.OVERLAP, 0),)),
        Query((Atom("word"),), (Relation(0, "&&", 0),)),  # type: ignore[arg-type]
        Query((Atom("word"),), (Relation(0, R.NEAR_BEFORE, 0, distance=K_MAX + 1),)),
        Query((Atom("word"),), (Relation(0, R.NEAR_BEFORE, 0, distance=True),)),
        Query((Atom("word"),), (Relation(0, R.OVERLAP, 0, edge="mother"),)),
        Query((Atom("word"),), (Relation(0, R.EDGE_FORWARD, 0, edge="oslots"),)),
        Query((Atom("word"),), (Relation(0, R.EDGE_FORWARD, 0, edge="missing"),)),
        Query((Atom("word"),), (Relation(0, R.EDGE_FORWARD, 0, edge="mother>\nword"),)),
        Query((Atom("word", (pred("rank", P.GT, 1), pred("rank", P.LT, 5))),)),
        Query((Atom("word"),), without=(Without(0, Query(())),)),
        Query((Atom("word"),), without=(Without(0, Query((Atom("word"),))),)),
        Query((Atom("word"),), without=(Without(1, Query((Atom("word"),))),)),
    ],
)
def test_invalid_query(tiny_api: Any, query: Query) -> None:
    with pytest.raises(CompileError):
        compile_query(query, NativeSymbols(tiny_api))


def test_generated_names_avoid_all_types(tiny_api: Any) -> None:
    symbols = NativeSymbols(tiny_api)
    symbols.object_types += ("n0", "n1")
    assert compile_query(Query((Atom("word"),)), symbols) == "n2:word"


def test_bhsa_compilation_equivalence(bhsa_api: Any) -> None:
    symbols = NativeSymbols(bhsa_api)
    cases = [
        (
            Query(
                (
                    Atom(
                        "word",
                        (pred("sp", P.EQ, "verb"), pred("gn", P.EQ, "f"), pred("nu", P.EQ, "pl")),
                    ),
                )
            ),
            "word sp=verb gn=f nu=pl",
        ),
        (Query((Atom("word", (pred("prs", P.EQ, "absent"),)),)), "word prs=absent"),
        (Query((Atom("word", (pred("nme", P.EQ, ""),)),)), "word nme=|"),
        (
            Query(
                (Atom("clause"),),
                without=(
                    Without(
                        0,
                        Query(
                            (Atom("phrase", (pred("function", P.EQ, "Pred"),)),),
                            (Relation(0, R.EMBEDDED_IN, Parent.REF),),
                        ),
                    ),
                ),
            ),
            "c:clause\n/without/\np:phrase function=Pred\np ]] ..\n/-/",
        ),
    ]
    bhsa_api.TF.load("nme", add=True, silent="deep")
    for query, gold in cases:
        actual = run_template(bhsa_api, compile_query(query, symbols), limit=500000)
        expected = run_template(bhsa_api, gold, limit=500000)
        assert actual.ok and expected.ok
        assert actual.results == expected.results


def test_bound_need_not_be_observed_value(tiny_api: Any) -> None:
    assert execute(tiny_api, Query((Atom("word", (pred("rank", P.GT, -10),)),))) == tuple(
        (n,) for n in range(1, 9)
    )


def test_quantifier_scope_and_runtime_shapes(tiny_api: Any) -> None:
    body = Query((Atom("word"),), (Relation(Parent.REF, R.ADJACENT_BEFORE, 0),))
    for query in (
        Query((Atom("word"),), without=(Without(0, body), Without(0, body))),
        Query(
            (Atom("word"),),
            without=(Without(0, Query(body.atoms, body.relations, (Without(0, body),))),),
        ),
        Query(
            (Atom("word"),),
            without=(Without(0, Query((Atom("word"), Atom("word")), body.relations)),),
        ),
        Query([Atom("word")]),  # type: ignore[arg-type]
        Query((Atom("word", [pred("sp", P.PRESENT)]),)),  # type: ignore[arg-type]
        Query((Atom("word", (Predicate("sp", P.EQ, ["verb"]),)),)),  # type: ignore[arg-type]
        Query((None,)),  # type: ignore[arg-type]
        Query((Atom("word"),), (None,)),  # type: ignore[arg-type]
    ):
        with pytest.raises(CompileError):
            compile_query(query, NativeSymbols(tiny_api))


def test_body_symbols_are_validated(tiny_api: Any) -> None:
    body = Query(
        (Atom("word", (pred("sp", P.EQ, "invented"),)),), (Relation(0, R.OVERLAP, Parent.REF),)
    )
    with pytest.raises(CompileError):
        compile_query(Query((Atom("word"),), without=(Without(0, body),)), NativeSymbols(tiny_api))


def test_schema_errors_do_not_echo_corpus_text(tiny_api: Any) -> None:
    class RejectingSymbols(NativeSymbols):
        def validate_value(self, feature: str, object_type: str, value: str | int) -> None:
            raise ValueError("sensitive corpus text")

    with pytest.raises(CompileError) as caught:
        compile_query(
            Query((Atom("word", (pred("lex", P.EQ, "a b"),)),)), RejectingSymbols(tiny_api)
        )
    assert "sensitive" not in str(caught.value)
