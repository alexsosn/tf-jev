"""Ontology is bounded metadata; native symbols and parser decisions stay authoritative."""

from pathlib import Path
from typing import Any

import pytest

from scripts.ontotf_context import OntologyBackend, load_catalog
from tests.test_grounded_parser import PlanBackend, plan
from tf_jev.candidate import CandidateParser
from tf_jev.schema import extract_schema


def xml(rows: str) -> str:
    return '<mappings corpus="tiny" corpusVersion="1">' + rows + "</mappings>"


def row(feature: str = "sp", value: str = "verb", relation: str = "exact") -> str:
    target = "" if relation == "native-only" else ' target="http://example.org#Verb"'
    return (
        f'<map kind="value" node="word" feature="{feature}" value="{value}" '
        f'relation="{relation}"{target}/>'
    )


def test_only_exact_validated_bindings(tiny_api: Any, tmp_path: Path) -> None:
    p = tmp_path / "catalog.xml"
    p.write_text(
        xml(row() + row(value="subs", relation="close") + row(value="adjv", relation="native-only"))
    )
    schema = extract_schema(tiny_api)
    catalog = load_catalog(p, schema, corpus="tiny", version="1")
    assert len(catalog) == 1 and catalog[0].feature == "sp"
    for content in (
        xml(row(feature="invented")),
        xml(row(value="invented")),
        '<!DOCTYPE a [<!ENTITY x "oops">]>' + xml(row()),
        xml(row(relation="made-up")),
    ):
        p.write_text(content)
        with pytest.raises(ValueError):
            load_catalog(p, schema, corpus="tiny", version="1")
    p.write_text(xml(row()))
    with pytest.raises(ValueError):
        load_catalog(p, schema, corpus="other", version="1")


def test_decisions_unchanged_and_context_scoped_to_own_plan(tiny_api: Any, tmp_path: Path) -> None:
    p = tmp_path / "catalog.xml"
    p.write_text(xml(row()))
    schema = extract_schema(tiny_api)
    base = PlanBackend(plan())
    with_ontology = PlanBackend(plan())
    original = CandidateParser(schema, base).parse("Return verbs.")
    catalog = load_catalog(p, schema, corpus="tiny", version="1")
    changed = CandidateParser(schema, OntologyBackend(with_ontology, catalog)).parse(
        "Return verbs."
    )
    assert original.ir == changed.ir and original.query == changed.query
    for before, after in zip(base.requests, with_ontology.requests, strict=True):
        assert before.questions == after.questions
        assert {k: v for k, v in after.context.items() if k != "ontology"} == before.context
        stage = next(iter(before.questions))
        if (
            stage.endswith(".feature")
            or stage.endswith(".operator")
            or stage.endswith(".count")
            or stage.endswith(".value0")
            or stage == "verify"
        ):
            assert "Verb" in after.context["ontology"]
        else:
            assert "ontology" not in after.context


def test_scope_does_not_transfer_person_to_suffix_or_parent(tiny_api: Any) -> None:
    import json

    from scripts.ontotf_context import Binding, relevant
    from tf_jev.decisions import ChoiceQuestion, DecisionRequest, Option

    question = {"verify": ChoiceQuestion("Exact?", (Option("yes", "yes"),))}
    catalog = (
        Binding("word", "ps", "p3", "http://example.org#Third", "Third"),
        Binding("word", "sp", "verb", "http://example.org#Verb", "Verb"),
        Binding("phrase", "sp", "verb", "http://example.org#WrongScope", "WrongScope"),
    )
    request = DecisionRequest(
        {
            "candidate": json.dumps(
                {
                    "query": {
                        "atoms": [{"object_type": "phrase", "predicates": []}],
                        "without": [
                            {
                                "body": {
                                    "atoms": [
                                        {
                                            "object_type": "word",
                                            "predicates": [
                                                {"feature": "sp"},
                                                {"feature": "prs_ps"},
                                            ],
                                        }
                                    ],
                                    "without": [],
                                }
                            }
                        ],
                    }
                }
            )
        },
        question,
    )
    assert relevant(request, catalog) == (catalog[1],)


def test_augmented_total_budget_refuses_before_transport(tiny_api: Any, tmp_path: Path) -> None:
    p = tmp_path / "catalog.xml"
    p.write_text(xml(row()))
    schema = extract_schema(tiny_api)
    backend = PlanBackend(plan())
    wrapped = OntologyBackend(
        backend, load_catalog(p, schema, corpus="tiny", version="1"), max_context_bytes=1
    )
    result = CandidateParser(schema, wrapped).parse("Return verbs.")
    assert result.query is None and result.status.value == "error"
    assert [next(iter(r.questions)) for r in backend.requests] == ["shape", "atom0.type"]


def test_real_sdk_and_native_path(tiny_api: Any, tmp_path: Path, monkeypatch: Any) -> None:
    import tests.test_grounded_parser as integration

    p = tmp_path / "catalog.xml"
    p.write_text(xml(row()))

    def parser(schema: Any, backend: Any) -> CandidateParser:
        return CandidateParser(
            schema, OntologyBackend(backend, load_catalog(p, schema, corpus="tiny", version="1"))
        )

    monkeypatch.setattr(integration, "GroundedParser", parser)
    integration.test_complete_parser_roundtrips_real_sdk(tiny_api)


def test_study_observation_is_durable_before_next_call(tmp_path: Path, tiny_api: Any) -> None:
    import json

    from scripts.ontotf_experiment import Budget, DurableTrace

    backend = PlanBackend(plan())
    budget = Budget(backend)
    public, private = tmp_path / "calls.json", tmp_path / "private.json"
    trace = DurableTrace(budget, public, private)
    result = CandidateParser(extract_schema(tiny_api), trace).parse("Return verbs.")
    assert result.query
    assert len(json.loads(public.read_text())) == len(result.evidence)
    assert len(json.loads(private.read_text())) == len(result.evidence)
    assert budget.calls == len(result.evidence) and budget.input_tokens == 11 * budget.calls
    budget.failed = True
    with pytest.raises(ValueError):
        budget.decide(backend.requests[0])


def test_study_requires_explicit_network_opt_in(tmp_path: Path, monkeypatch: Any) -> None:
    from scripts.ontotf_experiment import main

    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    with pytest.raises(ValueError, match="requires"):
        main(
            [
                str(tmp_path),
                "--output",
                str(tmp_path / "out"),
                "--private-review",
                str(tmp_path / "private"),
            ]
        )
    assert not (tmp_path / "out").exists()


def test_non_utf8_xml_cannot_bypass_declaration_guard(tiny_api: Any, tmp_path: Path) -> None:
    p = tmp_path / "catalog.xml"
    p.write_bytes(('<!DOCTYPE mappings [<!ENTITY x "ignored">]>' + xml(row())).encode("utf-16"))
    with pytest.raises(ValueError):
        load_catalog(p, extract_schema(tiny_api), corpus="tiny", version="1")
