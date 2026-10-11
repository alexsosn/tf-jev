"""Candidate narrowing over real TF inventories, without a model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric

from tests.conformance.tf_harness import run_template
from tf_jev.compiler import compile_query
from tf_jev.decisions import DecisionContractError, DecisionRequest, RawChoice, ScriptedBackend
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.retrieval import Match, Normalization, RetrievalError, RetrievalIndex
from tf_jev.schema import Large, SchemaError, extract_schema


@pytest.fixture
def large_schema(tmp_path: Path) -> tuple[Any, Any]:
    values = [
        "é",
        "e\u0301",
        "Straße",
        "STRASSE",
        "",
        "a|b",
        "a b",
        "a\\b",
        "tab\there",
        "bidi\u202e",
    ]
    values += [f"x{i:02}" for i in range(40)] + ["é"]
    tf = Fabric(locations=str(tmp_path), silent="deep")
    tf.save(
        nodeFeatures={
            "otype": {
                **{i: "word" for i in range(1, len(values) + 1)},
                len(values) + 1: "sentence",
            },
            "value": dict(enumerate(values, 1)),
        },
        edgeFeatures={"oslots": {len(values) + 1: set(range(1, len(values) + 1))}},
        metaData={
            "otype": {"valueType": "str"},
            "value": {"valueType": "str"},
            "oslots": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{value}"},
        },
        silent="deep",
    )
    api = Fabric(locations=str(tmp_path), silent="deep").load("value", silent="deep")
    return api, extract_schema(api)


def index(schema: Any, normalization: Normalization = Normalization.EXACT) -> RetrievalIndex:
    domain = schema.domain("value", "word").kind
    assert isinstance(domain, Large)
    return RetrievalIndex.from_schema(schema, domain.retrieval_handle, normalization=normalization)


def test_normalization_preserves_alternatives_and_counts(large_schema: tuple[Any, Any]) -> None:
    _, schema = large_schema
    exact = index(schema).lookup("é")
    assert [(c.value, c.count) for c in exact.candidates] == [("é", 2)]
    nfc = index(schema, Normalization.NFC).lookup("é")
    assert [c.value for c in nfc.candidates] == ["e\u0301", "é"]
    folded = index(schema, Normalization.NFC_CASEFOLD).lookup("strasse")
    assert {c.value for c in folded.candidates} == {"Straße", "STRASSE"}
    assert not index(schema).lookup("strasse").candidates
    assert nfc.total_matches == 2 and not nfc.truncated


def test_overflow_never_hands_partial_choices_to_backend(large_schema: tuple[Any, Any]) -> None:
    _, schema = large_schema
    result = index(schema).lookup("x", match=Match.PREFIX)
    assert len(result.candidates) == 32 and result.total_matches == 40 and result.truncated
    for operation in (lambda: result.as_question("Choose"), lambda: result.resolve("c0000")):
        with pytest.raises(RetrievalError):
            operation()
    for limit in (0, 33, True, 1.0):
        with pytest.raises(RetrievalError):
            index(schema).lookup("x", limit=limit)  # type: ignore[arg-type]
    with pytest.raises(RetrievalError):
        index(schema).lookup("", match=Match.PREFIX)


def test_empty_missing_and_stale_handles(large_schema: tuple[Any, Any]) -> None:
    _, schema = large_schema
    assert index(schema).lookup("").candidates[0].value == ""
    missing = index(schema).lookup("nonexistent")
    assert missing.total_matches == 0 and not missing.truncated
    with pytest.raises(RetrievalError):
        missing.as_question("Choose")
    with pytest.raises(SchemaError):
        RetrievalIndex.from_schema(schema, "stale")
    for mode in ("nfc", None):
        with pytest.raises(RetrievalError):
            RetrievalIndex.from_schema(schema, "stale", normalization=mode)  # type: ignore[arg-type]
    with pytest.raises(RetrievalError):
        index(schema).lookup("x", match="prefix")  # type: ignore[arg-type]
    with pytest.raises(RetrievalError):
        index(schema).lookup(None)  # type: ignore[arg-type]


def test_backend_boundary_and_native_compiler_round_trip(large_schema: tuple[Any, Any]) -> None:
    api, schema = large_schema
    for raw in ("é", "a|b", "a b", "a\\b", ""):
        result = index(schema).lookup(raw)
        question = result.as_question("Choose a value")
        label = question.labels[0]
        assert label.isascii() and question.options[0].description == raw
        backend = ScriptedBackend({"value": RawChoice(label, {label: 1.0})}, max_options=32)
        batch = backend.decide(DecisionRequest({}, {"value": question}))
        selected = batch.decisions["value"]
        assert selected.selected == label  # type: ignore[union-attr]
        value = result.resolve(label)
        query = Query((Atom("word", (Predicate("value", PredicateOp.EQ, (value,)),)),))
        outcome = run_template(api, compile_query(query, schema), limit=100)
        expected = tuple((n,) for n, v in api.F.value.items() if v == raw)
        assert outcome.ok and outcome.results == expected
        with pytest.raises(RetrievalError):
            result.resolve("invented")
    with pytest.raises(DecisionContractError):
        index(schema).lookup("bidi\u202e").as_question("Choose")


def test_prefix_is_explicit_and_limit_deterministic(large_schema: tuple[Any, Any]) -> None:
    _, schema = large_schema
    local = index(schema)
    assert not local.lookup("x").candidates
    a = local.lookup("x0", match=Match.PREFIX, limit=10)
    b = local.lookup("x0", match=Match.PREFIX, limit=10)
    assert a == b and a.total_matches == 10 and not a.truncated
    assert [c.value for c in a.candidates] == [f"x{i:02}" for i in range(10)]


def test_hand_built_results_cannot_bypass_budget_or_mutate() -> None:
    from tf_jev.retrieval import Candidate, RetrievalResult

    candidates = [Candidate(f"c{i:04}", f"x{i}", 1) for i in range(33)]
    with pytest.raises(RetrievalError):
        RetrievalResult("handle", tuple(candidates), 33)
    for total in (0, True, 1.0):
        with pytest.raises(RetrievalError):
            RetrievalResult("handle", (candidates[0],), total)  # type: ignore[arg-type]
    with pytest.raises(RetrievalError):
        RetrievalResult("handle", (candidates[0], candidates[0]), 2)
    for count in (0, -1, True):
        with pytest.raises(RetrievalError):
            Candidate("c0000", "value", count)
    mutable = candidates[:1]
    result = RetrievalResult("handle", mutable, 1)  # type: ignore[arg-type]
    mutable.clear()
    assert len(result.candidates) == 1


def test_large_normalization_collision_blocks_handoff_and_stale_snapshot(
    large_schema: tuple[Any, Any],
) -> None:
    import itertools
    import unicodedata

    api, schema = large_schema
    old = index(schema)
    values = [
        "e" + "".join(chars)
        for chars in list(itertools.permutations("\u0327\u0316\u0300\u0315\u0345"))[:33]
    ]
    assert len(set(values)) == 33
    keys = {unicodedata.normalize("NFC", v) for v in values}
    assert len(keys) == 1
    api.F.value.data.clear()
    api.F.value.data.update(dict(enumerate(values, 1)))
    changed = extract_schema(api)
    with pytest.raises(SchemaError):
        RetrievalIndex.from_schema(changed, old.handle)
    result = index(changed, Normalization.NFC).lookup(next(iter(keys)))
    assert result.total_matches == 33 and len(result.candidates) == 32 and result.truncated
    with pytest.raises(RetrievalError):
        result.as_question("Choose")
    assert old.lookup("é").candidates[0].count == 2
