"""Independent result oracle: attack native semantics from raw corpus data.

Derived during adversarial review, without relying on compiler rendering or
handwritten gold template strings. This caught whitespace-only exclusion.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

from tf.fabric import Fabric

from tests.conformance.tf_harness import run_template
from tests.test_compiler import NativeSymbols
from tf_jev.compiler import compile_query
from tf_jev.ir import Atom, Parent, Predicate, PredicateOp, Query, Relation, RelationOp, Without


def test_hostile_literal_membership_and_negation(tmp_path: Path) -> None:
    values = ["", " ", "  ", "/without/", "x\u0301", "x\u200e", "a=|#", "n0:word", "% comment"]
    values += ["".join(x) for x in product("\\ |tn=", repeat=3)]
    values = list(dict.fromkeys(values))
    data: dict[int, str] = {}
    for i, value in enumerate(values):
        data[2 * i + 1] = value
        data[2 * i + 2] = "marker" if i % 2 else "other"
    n = len(data)
    fabric = Fabric(locations=str(tmp_path), silent="deep")
    assert fabric.save(
        nodeFeatures={"otype": {**dict.fromkeys(data, "n0"), n + 1: "n1"}, "literal": data},
        edgeFeatures={"oslots": {n + 1: set(data)}},
        metaData={
            "otype": {"valueType": "str"},
            "oslots": {"valueType": "str"},
            "literal": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{literal} "},
        },
        silent="deep",
    )
    fabric = Fabric(locations=str(tmp_path), silent="deep")
    api = fabric.loadAll(silent="deep")
    assert api and api.Fs("literal").data == data
    schema = NativeSymbols(api)
    body = Query(
        (Atom("n0", (Predicate("literal", PredicateOp.EQ, ("marker",)),)),),
        (Relation(Parent.REF, RelationOp.ADJACENT_BEFORE, 0),),
    )
    for value in values:
        for op in (PredicateOp.EQ, PredicateOp.NE):
            atoms = (Atom("n0", (Predicate("literal", op, (value,)),)),)
            for quantified in (False, True):
                query = Query(atoms, without=(Without(0, body),) if quantified else ())
                rendered = compile_query(query, schema)
                assert rendered.startswith("n2:n0")  # n0/n1 are actual corpus types
                result = run_template(api, rendered, limit=n + 1)
                expected = {
                    node
                    for node, raw in data.items()
                    if (raw == value if op is PredicateOp.EQ else raw != value)
                    and (not quantified or data.get(node + 1) != "marker")
                }
                assert result.ok, result.error_text()
                assert result.results is not None
                assert {row[0] for row in result.results} == expected, (value, op, quantified)
