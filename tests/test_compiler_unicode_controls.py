"""Real native TF oracle for invisible Unicode corpus feature values (#32)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric

from tests.conformance.tf_harness import run_template
from tf_jev.compiler import CompileError, compile_query
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.schema import extract_schema

ALLOWED = (
    "plain",
    "e\u0301",  # non-NFC remains byte-exact
    "a\u200cb",  # zero-width non-joiner
    "a\u200db",  # zero-width joiner
    "a\u200eb",  # left-to-right mark, already native-tested elsewhere
    "a\u200fb",  # right-to-left mark
    "a|b",  # native grammar separator must be escaped
    "a b",  # native space must be escaped
)
FORBIDDEN = (
    "a\u00adb",  # soft hyphen
    "a\u200bb",  # zero-width space
    "a\u202eb",  # right-to-left override
    "a\u202ab",  # left-to-right embedding
    "a\u2060b",  # word joiner
    "a\u2062b",  # invisible times operator
    "a\u206ab",  # inhibit symmetric swapping
    "a\u2066b",  # left-to-right isolate
    "a\u2069b",  # pop directional isolate
    "a\ufeffb",  # zero-width no-break space
)


@pytest.fixture
def unicode_corpus(tmp_path: Path) -> tuple[Any, dict[int, str]]:
    data = {n: v for n, v in enumerate((*ALLOWED, *FORBIDDEN), start=1)}
    end = len(data) + 1
    fabric = Fabric(locations=str(tmp_path), silent="deep")
    assert fabric.save(
        nodeFeatures={
            "otype": {**dict.fromkeys(data, "word"), end: "sentence"},
            "lit": data,
        },
        edgeFeatures={"oslots": {end: set(data)}},
        metaData={
            "otype": {"valueType": "str"},
            "lit": {
                "valueType": "str",
                "description": "unselected metadata\u202e still cannot poison ordinary literal",
            },
            "oslots": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{lit} "},
        },
        silent="deep",
    )
    api = Fabric(locations=str(tmp_path), silent="deep").load("lit", silent="deep")
    assert api and dict(api.Fs("lit").data) == data
    return api, data


def query_for(value: str, op: PredicateOp = PredicateOp.EQ) -> Query:
    return Query((Atom("word", (Predicate("lit", op, (value,)),)),))


@pytest.mark.parametrize("value", ALLOWED)
@pytest.mark.parametrize("op", [PredicateOp.EQ, PredicateOp.NE])
def test_allowed_unicode_literals_match_raw_feature_data(
    unicode_corpus: tuple[Any, dict[int, str]], value: str, op: PredicateOp
) -> None:
    api, data = unicode_corpus
    schema = extract_schema(api)
    native = compile_query(query_for(value, op), schema)
    # Native Text-Fabric metacharacters must be escaped, not copied literally.
    # Non-NFC and approved script formatting code points must stay byte-exact.
    marks = tuple(chr(code) for code in (0x200C, 0x200D, 0x200E, 0x200F))
    if value == "e" + chr(0x0301) or any(mark in value for mark in marks):
        assert value in native
    result = run_template(api, native, limit=len(data) + 1)
    assert result.ok, result.error_text()
    expected = tuple(
        (n,) for n, observed in data.items()
        if (observed == value if op is PredicateOp.EQ else observed != value)
    )
    assert result.results == expected


@pytest.mark.parametrize("value", FORBIDDEN)
@pytest.mark.parametrize("op", [PredicateOp.EQ, PredicateOp.NE])
def test_auditor_hostile_format_controls_fail_closed(
    unicode_corpus: tuple[Any, dict[int, str]], value: str, op: PredicateOp
) -> None:
    api, _data = unicode_corpus
    schema = extract_schema(api)
    with pytest.raises(CompileError, match="unrepresentable literal value") as caught:
        compile_query(query_for(value, op), schema)
    assert value not in str(caught.value)


def test_rejected_alternative_never_silently_dropped(
    unicode_corpus: tuple[Any, dict[int, str]]
) -> None:
    api, _data = unicode_corpus
    schema = extract_schema(api)
    for op in (PredicateOp.EQ, PredicateOp.NE):
        query = Query((Atom("word", (Predicate("lit", op, ("plain", "a\u202eb")),)),))
        with pytest.raises(CompileError, match="unrepresentable literal value"):
            compile_query(query, schema)


def test_safe_literal_unaffected_by_attested_hostile_values(
    unicode_corpus: tuple[Any, dict[int, str]]
) -> None:
    api, _data = unicode_corpus
    schema = extract_schema(api)
    native = compile_query(query_for("plain"), schema)
    result = run_template(api, native, limit=32)
    assert result.ok and result.results == ((1,),)
