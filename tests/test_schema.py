"""Schema contract grounded in actual TF data and native search."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric

from tests.conformance.tf_harness import build_tiny_corpus, run_template
from tf_jev.compiler import CompileError, SymbolSchema, compile_query
from tf_jev.ir import Atom, Predicate, Query
from tf_jev.ir import PredicateOp as P
from tf_jev.schema import ENUM_LIMIT, Enumerated, IntRange, Large, SchemaError, extract_schema


def dataset(path: Path) -> Any:
    build_tiny_corpus(path)
    (path / "sparse.tf").write_text("@node\n@valueType=int\n\n1\t-2\n2\t4\n")
    (path / "unicode.tf").write_text("@node\n@valueType=str\n\n1\te\u0301\n2\tNA\n")
    (path / "empty.tf").write_text("@node\n@valueType=int\n\n")
    (path / "not.expressible.tf").write_text("@node\n@valueType=str\n\n1\tx\n")
    (path / "omap@test.tf").write_text("@edge\n@valueType=str\n\n1\t2\n")
    tf = Fabric(locations=str(path), silent="deep")
    return tf.load("", silent="deep")


@pytest.fixture
def api(tmp_path: Path) -> Any:
    return dataset(tmp_path)


def test_snapshot_protocol_and_per_type_domains(api: Any) -> None:
    schema = extract_schema(api)
    protocol: SymbolSchema = schema
    assert protocol.object_types == ("sentence", "clause", "phrase", "word")
    assert schema.object_type("word").slot
    suffix = schema.domain("suffix", "word")
    assert suffix.node_count == 8 and suffix.missing_count == 4
    assert suffix.has_empty_string and suffix.distinct == 3
    assert suffix.kind == Enumerated((("", 2), ("H", 1), ("JM", 1)))
    assert schema.domain("typ", "phrase").distinct == 4
    assert schema.domain("typ", "clause").distinct == 2
    assert schema.domain("unicode", "word").non_nfc_count == 1
    assert schema.domain("unicode", "word").kind == Enumerated((("NA", 1), ("e\u0301", 1)))
    assert schema.reserved_names == frozenset(schema.object_types)
    assert schema.type_named_features == frozenset()


def test_sparse_integer_membership_and_all_missing_domains(api: Any) -> None:
    schema = extract_schema(api)
    assert schema.domain("sparse", "word").kind == IntRange(-2, 4, 2)
    assert schema.domain("empty", "word").kind == IntRange(None, None, 0)
    assert schema.domain("suffix", "phrase").kind == Enumerated(())
    schema.validate_value("sparse", "word", -2)
    schema.validate_value("unicode", "word", "NA")
    bad_values: list[tuple[str, str, str | int]] = [
        ("sparse", "word", 0),
        ("sparse", "word", True),
        ("empty", "word", 0),
        ("suffix", "phrase", ""),
        ("unicode", "word", "é"),
    ]
    for feature, otype, value in bad_values:
        with pytest.raises(SchemaError):
            schema.validate_value(feature, otype, value)
    # Native TF absence is meaningful even if every node lacks the feature.
    q = Query((Atom("phrase", (Predicate("suffix", P.ABSENT),)),))
    result = run_template(api, compile_query(q, schema), limit=100)
    assert result.ok and result.results == tuple((n,) for n in range(9, 14))


def test_edges_and_exclusions(api: Any) -> None:
    schema = extract_schema(api)
    assert {f.name for f in schema.edge_features} == {"mother", "dist"}
    assert schema.edge_feature("mother").endpoints == (("clause", "clause", 1),)
    assert schema.edge_feature("dist").has_values
    assert schema.edge_feature("dist").endpoints == (("word", "word", 2),)
    assert {"otype", "oslots", "omap@test", "not.expressible"} <= set(schema.excluded_features)
    assert "omap@test" not in api.Eall()
    assert "not.expressible" not in api.Fall()
    for name in ("oslots", "omap@test", "lex", "unknown"):
        with pytest.raises(SchemaError):
            schema.validate_edge(name)
    with pytest.raises(SchemaError):
        schema.node_feature_type("mother", "clause")
    with pytest.raises(SchemaError):
        schema.node_feature_type("not.expressible", "word")
    with pytest.raises(SchemaError):
        schema.object_type("unknown")


def test_determinism_and_deep_snapshot_isolation(api: Any) -> None:
    a = extract_schema(api)
    b = extract_schema(api)
    assert a.to_json() == b.to_json()
    assert json.loads(a.to_json())["identity"]["tf_version"] == version("text-fabric")
    with pytest.raises(FrozenInstanceError):
        a.node_features = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        a.domain("suffix", "word").missing_count = 100  # type: ignore[misc]
    before = a.to_json()
    api.Fs("suffix").data[1] = "invented"
    assert a.to_json() == before
    a.validate_value("suffix", "word", "")
    with pytest.raises(SchemaError):
        a.validate_value("suffix", "word", "invented")
    updated = extract_schema(api)
    assert updated.identity.loaded_sha256 != a.identity.loaded_sha256
    # Node-value swaps preserve frequency counts but must invalidate identity.
    api.Fs("rank").data[1], api.Fs("rank").data[2] = api.Fs("rank").data[2], api.Fs("rank").data[1]
    assert extract_schema(api).identity.loaded_sha256 != updated.identity.loaded_sha256


def test_loaded_and_source_identity_both_matter(api: Any, tmp_path: Path) -> None:
    a = extract_schema(api)
    (tmp_path / "unloaded-config.tf").write_text("@config\n@hello=world\n\n")
    b = extract_schema(api)
    assert a.identity.locations != b.identity.locations
    assert a.identity.loaded_sha256 == b.identity.loaded_sha256
    assert a.identity.key != b.identity.key


def test_module_override_order_and_effective_domain(tmp_path: Path) -> None:
    base, overlay = tmp_path / "base", tmp_path / "overlay"
    base.mkdir()
    overlay.mkdir()
    build_tiny_corpus(base)
    (overlay / "sp.tf").write_text("@node\n@valueType=str\n\n1\toverridden\n")
    tf = Fabric(locations=str(tmp_path), modules=["base", "overlay"], silent="deep")
    schema = extract_schema(tf.load("", silent="deep"))
    assert tuple(p for p, _ in schema.identity.locations) == (str(base), str(overlay))
    assert schema.domain("sp", "word").kind == Enumerated((("overridden", 1),))
    tf2 = Fabric(locations=str(tmp_path), modules=["overlay", "base"], silent="deep")
    reversed_schema = extract_schema(tf2.load("", silent="deep"))
    assert schema.identity.key != reversed_schema.identity.key
    assert reversed_schema.domain("sp", "word").distinct == 4


def test_large_domains_are_local_exact_and_scoped(tmp_path: Path) -> None:
    big = tmp_path / "big"
    big.mkdir()
    n = ENUM_LIMIT + 1
    tf = Fabric(locations=str(big), silent="deep")
    assert tf.save(
        nodeFeatures={
            "otype": {**dict.fromkeys(range(1, n + 1), "token"), n + 1: "group"},
            "label": {i: f"value{i}" for i in range(1, n + 1)},
        },
        edgeFeatures={"oslots": {n + 1: set(range(1, n + 1))}},
        metaData={
            "otype": {"valueType": "str"},
            "oslots": {"valueType": "str"},
            "label": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{label} "},
        },
        silent="deep",
    )
    tf = Fabric(locations=str(big), silent="deep")
    api = tf.load("", silent="deep")
    schema = extract_schema(api)
    domain = schema.domain("label", "token")
    assert isinstance(domain.kind, Large) and domain.distinct == n
    handle = domain.kind.retrieval_handle
    assert len(schema.retrieval_values(handle)) == n
    assert schema.retrieval_values(handle) == tuple(
        sorted((f"value{i}", 1) for i in range(1, n + 1))
    )
    schema.validate_value("label", "token", "value33")
    assert "value33" not in schema.to_json()
    assert "value33" not in repr(schema)
    with pytest.raises(SchemaError):
        schema.validate_value("label", "token", "absent")
    with pytest.raises(SchemaError):
        schema.retrieval_values("invented")
    api.Fs("label").data[1] = "changed"
    updated = extract_schema(api)
    with pytest.raises(SchemaError):
        updated.retrieval_values(handle)


def test_failures_are_explicit(api: Any) -> None:
    with pytest.raises(SchemaError):
        extract_schema(False)
    api.Fs("lex")  # loaded via otext
    api.Fs("lex").data[1000] = "secret data outside node extent"
    with pytest.raises(SchemaError) as caught:
        extract_schema(api)
    assert "secret" not in str(caught.value)


def test_compiler_rejects_unknown_values(api: Any) -> None:
    schema = extract_schema(api)
    with pytest.raises(CompileError):
        compile_query(Query((Atom("word", (Predicate("lex", P.EQ, ("invented",)),)),)), schema)
    outcome = run_template(
        api,
        compile_query(Query((Atom("word", (Predicate("lex", P.EQ, ("a|b",)),)),)), schema),
        limit=100,
    )
    assert outcome.ok and outcome.results == ((6,),)


def test_bhsa_schema_and_native_query(bhsa_api: Any) -> None:
    schema = extract_schema(bhsa_api)
    assert schema.identity.dataset == "BHSA"
    assert schema.identity.version_dir == "2021"
    assert schema.domain("lex", "word").distinct == 8769
    assert isinstance(schema.domain("lex", "word").kind, Large)
    assert schema.domain("number", "word").kind == IntRange(1, 29736, 29736)
    assert schema.domain("nametype", "word").missing_count == 391084
    assert schema.domain("nme", "word").has_empty_string
    assert schema.domain("voc_lex_utf8", "word").non_nfc_count == 3287
    assert schema.type_named_features == frozenset({"book", "chapter", "lex", "verse"})
    assert ("phrase", "word", 8) in schema.edge_feature("mother").endpoints
    assert all(not e.name.startswith("omap@") for e in schema.edge_features)
    q = Query((Atom("word", (Predicate("nme", P.EQ, ("",)),)),))
    result = run_template(bhsa_api, compile_query(q, schema), limit=500000)
    assert result.ok and result.results is not None and len(result.results) == 121983


@pytest.mark.parametrize("name,key", [("lex", "description"), ("dist", "description")])
def test_mutable_metadata_cannot_break_snapshot_immutability(api: Any, name: str, key: str) -> None:
    extract_schema(api)
    api.TF.features[name].metaData[key] = ["mutable"]
    with pytest.raises(SchemaError):
        extract_schema(api)


def test_invalid_edge_endpoints_and_feature_load_failure(api: Any, tmp_path: Path) -> None:
    extract_schema(api)
    api.Es("mother").data[15] = api.Es("mother").data[15] | {1000}
    with pytest.raises(SchemaError, match="target"):
        extract_schema(api)
    other = tmp_path / "broken"
    other.mkdir()
    broken_api = dataset(other)
    (other / "broken-int.tf").write_text("@node\n@valueType=int\n\n1\tnot-an-integer\n")
    # Refresh discovery so TF sees the new file. No mocked load behavior.
    tf = Fabric(locations=str(other), silent="deep")
    broken_api = tf.load("", silent="deep")
    with pytest.raises(SchemaError, match="load"):
        extract_schema(broken_api)


def test_noncontiguous_types_are_rejected_before_compilation(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    (tmp_path / "otype.tf").write_text(
        "@node\n@valueType=str\n\n1-8\tword\n9\tphrase\n10\tclause\n11-13\tphrase\n14-15\tclause\n16\tsentence\n"
    )
    tf = Fabric(locations=str(tmp_path), silent="deep")
    api = tf.load("", silent="deep")
    assert api
    raw = {n for n, t in api.F.otype.items() if t == "clause"}
    outcome = run_template(api, "clause", limit=100)
    assert outcome.ok and outcome.results is not None
    assert {row[0] for row in outcome.results} != raw  # real native hazard
    with pytest.raises(SchemaError, match="interval"):
        extract_schema(api)


def test_extraction_borrows_existing_tf_otype_mapping_without_copy(
    api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TF 13.1 stores non-slot types compactly; .items() expands them."""
    native_otype = api.F.otype
    assert len(native_otype.data) == native_otype.maxNode - native_otype.maxSlot
    assert native_otype.maxNode > native_otype.maxSlot
    before = extract_schema(api)
    expected_query = compile_query(
        Query((Atom("word", (Predicate("sp", P.EQ, ("verb",)),)),)), before
    )
    expected_native = run_template(api, expected_query, limit=100)
    assert expected_native.ok and expected_native.results == ((3,), (6,), (8,))

    def forbidden_items() -> Any:
        raise AssertionError("duplicated authoritative otype map through .items()")

    # Force the extractor to work from native compact storage, not
    # materialize a giant node-to-type dict via the accessor.
    with monkeypatch.context() as patch:
        patch.setattr(api.F.otype, "items", forbidden_items)
        after = extract_schema(api)
    assert after.identity == before.identity
    assert after.to_json() == before.to_json()
    assert after._inventories == before._inventories
    actual_query = compile_query(
        Query((Atom("word", (Predicate("sp", P.EQ, ("verb",)),)),)), after
    )
    assert actual_query == expected_query
    assert run_template(api, actual_query, limit=100) == expected_native
