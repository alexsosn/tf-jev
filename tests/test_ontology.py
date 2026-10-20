"""Public ontology context remains optional, corpus-bound and bounded as catalogs grow."""

from pathlib import Path
from typing import Any

import pytest

from tests.conformance.tf_harness import run_template
from tests.test_grounded_parser import PlanBackend, plan
from tf_jev.ontology import OntologyParser, load_catalog
from tf_jev.schema import extract_schema


def write_catalog(path: Path, rows: str) -> Path:
    path.write_text(
        '<mappings corpus="tiny" source="synthetic" corpusVersion="1">' + rows + "</mappings>"
    )
    return path


def mapping(
    value: str = "verb", target: str = "Verb", feature: str = "sp", relation: str = "exact"
) -> str:
    iri = "" if relation == "native-only" else f' target="http://example.org#{target}"'
    return (
        f'<map kind="value" node="word" feature="{feature}" value="{value}" '
        f'relation="{relation}"{iri}/>'
    )


def test_public_native_results_and_identity(tiny_api: Any, tmp_path: Path) -> None:
    schema = extract_schema(tiny_api)
    p = write_catalog(
        tmp_path / "tiny.xml",
        mapping() + mapping("subs", "Noun") + mapping("adjv", relation="native-only"),
    )
    catalog = load_catalog(p, schema, corpus="tiny", version="1", revision="test-rev")
    backend = PlanBackend(plan())
    result = OntologyParser(schema, backend, catalog=catalog).parse("Return verbs.")
    assert result.query and run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    assert (
        result.catalog.revision == "test-rev" and result.catalog.schema_key == schema.identity.key
    )
    assert result.catalog.ignored_records == 1 and len(result.catalog.sha256) == 64
    assert result.ontology_context and "ontology" in backend.requests[-1].context


def test_catalog_updates_are_data_and_old_snapshot_is_immutable(
    tiny_api: Any, tmp_path: Path
) -> None:
    schema = extract_schema(tiny_api)
    p = write_catalog(tmp_path / "tiny.xml", mapping())
    old = load_catalog(p, schema, corpus="tiny", version="1")
    write_catalog(p, mapping() + mapping("H", "NewSuffixConcept", "suffix"))
    new = load_catalog(p, schema, corpus="tiny", version="1")
    assert len(old.bindings) == 1 and len(new.bindings) == 2
    assert old.identity.sha256 != new.identity.sha256
    with pytest.raises(ValueError):
        load_catalog(p, schema, corpus="tiny", version="1", expected_sha256=old.identity.sha256)


@pytest.mark.parametrize(
    "content",
    [
        '<!DOCTYPE mappings [<!ENTITY x "bad">]>',
        (
            '<mappings corpus="tiny" source="synthetic" corpusVersion="1">'
            '<map kind="value" node="word" feature="sp" value="madeup" relation="exact" '
            'target="http://x#Verb"/></mappings>'
        ),
    ],
)
def test_hostile_or_missing_selectors_fail_closed(
    tiny_api: Any, tmp_path: Path, content: str
) -> None:
    p = tmp_path / "bad.xml"
    p.write_text(content)
    with pytest.raises(ValueError):
        load_catalog(p, extract_schema(tiny_api), corpus="tiny", version="1")


def test_growth_retrieves_complete_target_without_removing_native_choices(
    tiny_api: Any, tmp_path: Path
) -> None:
    import json

    schema = extract_schema(tiny_api)
    rows = mapping("subs", "Noun") + mapping("prep", "Noun")
    rows += "".join(mapping("verb", f"Distractor{i}") for i in range(120))
    catalog = load_catalog(
        write_catalog(tmp_path / "grow.xml", rows), schema, corpus="tiny", version="1"
    )
    backend = PlanBackend(plan())
    result = OntologyParser(schema, backend, catalog=catalog).parse("Find nouns.")
    first = next(r for r in backend.requests if next(iter(r.questions)).endswith(".feature"))
    descriptions = json.loads(first.context["ontology"])["bindings"]
    assert {b["value"] for b in descriptions} == {"subs", "prep"}
    assert any(s.mode == "retrieved" and s.selected == 2 for s in result.ontology_context)
    assert len(next(iter(first.questions.values())).options) == len(schema.node_features) + 1


def test_overflow_never_sends_partial_matching_concept_set(tiny_api: Any, tmp_path: Path) -> None:
    schema = extract_schema(tiny_api)
    rows = "".join(
        mapping().replace("http://example.org", f"http://example{i}.org") for i in range(120)
    )
    catalog = load_catalog(
        write_catalog(tmp_path / "grow.xml", rows), schema, corpus="tiny", version="1"
    )
    backend = PlanBackend(plan())
    result = OntologyParser(schema, backend, catalog=catalog).parse("Return verbs.")
    assert result.query and any(s.mode == "omitted_budget" for s in result.ontology_context)
    assert all("ontology" not in r.context for r in backend.requests)


def test_schema_mismatch_integer_and_relation_dispositions(tiny_api: Any, tmp_path: Path) -> None:
    from dataclasses import replace

    schema = extract_schema(tiny_api)
    p = write_catalog(
        tmp_path / "tiny.xml",
        mapping("2", "RankTwo", "rank") + mapping("subs", "Noun", relation="close"),
    )
    catalog = load_catalog(p, schema, corpus="tiny", version="1")
    assert catalog.bindings[0].value == "2" and catalog.identity.ignored_records == 1
    other = replace(schema, identity=replace(schema.identity, version_dir="other"))
    with pytest.raises(ValueError, match="mismatch"):
        OntologyParser(other, PlanBackend(plan()), catalog=catalog)
    for raw in [p.read_bytes().decode().encode("utf-16"), b"<!DOCTYPE x>" + p.read_bytes()]:
        p.write_bytes(raw)
        with pytest.raises(ValueError):
            load_catalog(p, schema, corpus="tiny", version="1")


def test_sdk_transport_and_witness_scopes(tiny_api: Any, tmp_path: Path, monkeypatch: Any) -> None:
    import tests.test_grounded_parser as contract

    schema = extract_schema(tiny_api)
    catalog = load_catalog(
        write_catalog(tmp_path / "tiny.xml", mapping()), schema, corpus="tiny", version="1"
    )

    def parser(schema: Any, backend: Any) -> OntologyParser:
        return OntologyParser(schema, backend, catalog=catalog)

    monkeypatch.setattr(contract, "GroundedParser", parser)
    contract.test_complete_parser_roundtrips_real_sdk(tiny_api)
    for shape in ("relation", "without"):
        contract.test_predicted_parent_child_scope(tiny_api, shape)
    contract.test_fidelity_and_backend_failures_emit_no_query(tiny_api)


def test_parse_history_is_local_and_weak_verdict_withholds(tiny_api: Any, tmp_path: Path) -> None:
    schema = extract_schema(tiny_api)
    catalog = load_catalog(
        write_catalog(tmp_path / "tiny.xml", mapping()), schema, corpus="tiny", version="1"
    )
    parser = OntologyParser(schema, PlanBackend(plan(), "verify"), catalog=catalog)
    first = parser.parse("Return verbs.")
    second = parser.parse("Return verbs.")
    assert first.query is None and first.ir is None and first.reason == "low_confidence"
    assert first.ontology_context == second.ontology_context
    weak_proposal = OntologyParser(
        schema, PlanBackend(plan(), "atom0.pred0.feature"), catalog=catalog
    ).parse("Return verbs.")
    assert weak_proposal.query and weak_proposal.confidence == pytest.approx(0.65)


def test_catalog_nonvalue_kinds_are_explicitly_skipped_and_errors_sanitized(
    tiny_api: Any, tmp_path: Path
) -> None:
    schema = extract_schema(tiny_api)
    p = write_catalog(
        tmp_path / "tiny.xml",
        mapping() + '<map kind="node" node="word" relation="exact" target="urn:example:Token"/>',
    )
    c = load_catalog(p, schema, corpus="tiny", version="1")
    assert ("node", "exact", 1) in c.identity.dispositions and c.identity.ignored_records == 1
    with pytest.raises(ValueError) as exc:
        load_catalog(tmp_path / "secret-api-key-missing.xml", schema, corpus="tiny", version="1")
    assert "secret" not in str(exc.value) and exc.value.__context__ is None


def test_catalog_and_context_resource_caps(tiny_api: Any, tmp_path: Path) -> None:
    from tf_jev.grounded import GroundedPolicy

    schema = extract_schema(tiny_api)
    p = write_catalog(tmp_path / "tiny.xml", mapping())
    c = load_catalog(p, schema, corpus="tiny", version="1")
    backend = PlanBackend(plan())
    result = OntologyParser(schema, backend, GroundedPolicy(max_context_chars=1), catalog=c).parse(
        "Return verbs."
    )
    assert result.query is None and not backend.requests
    p.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(ValueError):
        load_catalog(p, schema, corpus="tiny", version="1")
