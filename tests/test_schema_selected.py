"""Test-first coverage contract: a partial schema is never an exhaustive corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from tests.conformance.tf_harness import build_tiny_corpus, run_template
from tf_jev.compiler import CompileError, compile_query
from tf_jev.decisions import DecisionBackend
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.parser import ParseStatus, SemanticParser
from tf_jev.schema import SchemaError, extract_schema


@pytest.fixture
def api(tmp_path: Path) -> Any:
    from tf.fabric import Fabric

    build_tiny_corpus(tmp_path)
    return Fabric(locations=str(tmp_path), silent="deep").load("", silent="deep")


def test_explicit_selected_manifest_and_untouched_full_digest(api: Any) -> None:
    full = extract_schema(api)
    assert full.coverage.mode == "full"
    assert full.coverage.omitted_node_features == ()
    assert full.coverage.omitted_edge_features == ()
    assert "coverage" not in json.loads(full.to_json())

    chosen = extract_schema(api, node_features=("sp", "gn"), edge_features=())
    assert chosen.coverage.mode == "selected"
    assert chosen.coverage.node_features == ("gn", "sp")
    assert chosen.coverage.edge_features == ()
    assert "lex" in chosen.coverage.omitted_node_features
    assert "mother" in chosen.coverage.omitted_edge_features
    assert {x.name for x in chosen.node_features} == {"sp", "gn"}
    assert not chosen.edge_features
    assert json.loads(chosen.to_json())["coverage"]["mode"] == "selected"
    assert chosen.identity.loaded_sha256 != full.identity.loaded_sha256
    assert chosen.identity.key != full.identity.key

    reordered = extract_schema(api, node_features=("gn", "sp"), edge_features=())
    assert chosen.identity.key == reordered.identity.key
    assert chosen.to_json() == reordered.to_json()
    assert full.identity.loaded_sha256 == extract_schema(api).identity.loaded_sha256


def test_selected_native_queries_work_and_omitted_features_fail_closed(api: Any) -> None:
    selected = extract_schema(api, node_features=("sp",), edge_features=("mother",))
    full = extract_schema(api)
    selected.domain("sp", "word")
    selected.validate_value("sp", "word", "verb")
    q = Query((Atom("word", (Predicate("sp", PredicateOp.EQ, ("verb",)),)),))
    native = compile_query(q, selected)
    assert native == compile_query(q, full)
    result = run_template(api, native, limit=100)
    assert result.ok and result.results == ((3,), (6,), (8,))
    selected.edge_feature("mother")
    with pytest.raises(SchemaError, match="omitted"):
        selected.domain("lex", "word")
    with pytest.raises(SchemaError, match="omitted"):
        selected.validate_edge("dist")
    with pytest.raises(CompileError):
        compile_query(Query((Atom("word", (Predicate("lex", PredicateOp.EQ, ("x",)),)),)), selected)
    with pytest.raises(SchemaError, match="unknown"):
        selected.domain("invented", "word")


@pytest.mark.parametrize(
    ("nodes", "edges"),
    [
        (("sp", "sp"), ()),
        (("bogus",), ()),
        (("otype",), ()),
        (("mother",), ()),
        ((1,), ()),
        ((), ("sp",)),
        ((), ("nonesuch",)),
    ],
)
def test_invalid_selected_manifests_rejected_before_loading(
    api: Any, nodes: tuple[Any, ...], edges: tuple[Any, ...]
) -> None:
    with pytest.raises(SchemaError, match="feature"):
        extract_schema(api, node_features=nodes, edge_features=edges)


def test_empty_explicit_scope_is_not_full_and_unknown_is_not_absent(api: Any) -> None:
    empty = extract_schema(api, node_features=())
    assert empty.coverage.mode == "selected"
    assert not empty.node_features and not empty.edge_features
    assert "sp" in empty.coverage.omitted_node_features
    with pytest.raises(SchemaError, match="omitted"):
        empty.validate_value("sp", "word", "verb")
    full = extract_schema(api)
    assert empty.identity.loaded_sha256 != full.identity.loaded_sha256
    assert extract_schema(api, edge_features=()).coverage.mode == "selected"


def test_coverage_selection_invalidates_large_retrieval_handles(tmp_path: Path) -> None:
    from tf.fabric import Fabric

    from tf_jev.schema import Large

    n = 38
    folder = tmp_path / "large"
    folder.mkdir()
    tf = Fabric(locations=str(folder), silent="deep")
    assert tf.save(
        nodeFeatures={
            "otype": {**dict.fromkeys(range(1, n + 1), "word"), n + 1: "sentence"},
            "label": {i: f"v{i}" for i in range(1, n + 1)},
            "noise": {i: "x" for i in range(1, n + 1)},
        },
        edgeFeatures={"oslots": {n + 1: set(range(1, n + 1))}},
        metaData={
            "otype": {"valueType": "str"}, "oslots": {"valueType": "str"},
            "label": {"valueType": "str"}, "noise": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{label}"},
        },
        silent="deep",
    )
    api = Fabric(locations=str(folder), silent="deep").load("", silent="deep")
    a = extract_schema(api, node_features=("label",))
    b = extract_schema(api, node_features=("label", "noise"))
    a_kind = a.domain("label", "word").kind
    b_kind = b.domain("label", "word").kind
    assert isinstance(a_kind, Large) and isinstance(b_kind, Large)
    assert a_kind.retrieval_handle != b_kind.retrieval_handle
    with pytest.raises(SchemaError, match="stale"):
        b.retrieval_values(a_kind.retrieval_handle)
    assert len(a.retrieval_values(a_kind.retrieval_handle)) == n


def test_parser_abstains_before_any_backend_calls_for_selected_schema(api: Any) -> None:
    class Backend:
        @property
        def capabilities(self) -> Any:
            raise AssertionError("backend should never be invoked")

        def decide(self, request: Any) -> Any:
            raise AssertionError("backend should never be invoked")

    selected = extract_schema(api, node_features=("sp",))
    result = SemanticParser(selected, cast(DecisionBackend, Backend())).parse("verbs")
    assert result.status is ParseStatus.UNSUPPORTED
    assert result.reason == "incomplete_schema_coverage"
    assert result.ir is None and result.query is None and result.evidence == ()
