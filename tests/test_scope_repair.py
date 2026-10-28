"""Observed-stage scope adaptation must preserve bounded native choices."""

import json
from typing import Any, cast

from scripts.scope_repair import scoped
from tf_jev.decisions import ChoiceQuestion, DecisionRequest, Option


def test_operator_is_local_and_preserves_options() -> None:
    feature = dict(name="category", description="grammatical category")
    request = DecisionRequest(
        context=dict(
            request="Return nouns with reading present.",
            contract="untrusted",
            selected=json.dumps({"atom0.pred1.feature": json.dumps(feature)}),
            focus=json.dumps(dict(index=0, object_type="token", shape="atom", predicates=[])),
            ontology="native mappings",
        ),
        questions={
            "atom0.pred1.operator": ChoiceQuestion(
                "old", (Option("a", "="), Option("b", "present"))
            )
        },
    )
    result = scoped(request)
    q = cast(ChoiceQuestion, result.questions["atom0.pred1.operator"])
    assert q.options == cast(ChoiceQuestion, request.questions["atom0.pred1.operator"]).options
    assert "grammatical category" in q.prompt and "token" in q.prompt
    assert "selected" not in result.context
    assert result.context["ontology"] == "native mappings"
    assert result.context["property_id"] == "category"


def test_framing_retains_labels_and_attestation() -> None:
    from scripts.scope_repair import framed

    request = DecisionRequest(
        dict(
            request="Return containers without nouns.",
            contract="untrusted",
            focus=json.dumps(dict(index=1, object_type="token", shape="without", predicates=[])),
        ),
        {
            "atom1.pred0.feature": ChoiceQuestion(
                "old",
                (
                    Option(
                        "a",
                        json.dumps(
                            dict(
                                kind="feature",
                                name="category",
                                description="POS",
                                attested_on_type=False,
                            )
                        ),
                    ),
                    Option("b", json.dumps(dict(kind="stop"))),
                ),
            )
        },
    )
    result = framed(request, "polarity")
    assert cast(ChoiceQuestion, result.questions["decision"]).labels == ("a", "b")
    assert "False" in (
        cast(ChoiceQuestion, result.questions["decision"]).options[0].description or ""
    )
    assert "matching child" in cast(ChoiceQuestion, result.questions["decision"]).prompt


def test_joint_choices_preserve_native_pairs_and_missing_features() -> None:
    from scripts.scope_repair import joint_features, joint_types

    request = joint_types("request", ("container", "token"))
    assert len(cast(ChoiceQuestion, request.questions["types"]).options) == 4
    assert any(
        "container / container" in (o.description or "")
        for o in cast(ChoiceQuestion, request.questions["types"]).options
    )
    feature = dict(name="rare", description="rare annotation", dtype="str")
    result = joint_features("request", ("container", "token"), (feature,))
    assert len(cast(ChoiceQuestion, result.questions["features"]).options) == 3
    assert "container" in (
        cast(ChoiceQuestion, result.questions["features"]).options[0].description or ""
    )


def test_coordinator_native_witness_and_absent(tiny_api: Any) -> None:
    from scripts.scope_repair import CoordinatedParser
    from tests.conformance.tf_harness import run_template
    from tests.test_grounded_parser import PlanBackend
    from tf_jev.schema import extract_schema

    backend = PlanBackend(
        {
            "shape": "without",
            "nodes.types": "phrase / word",
            "atom0.pred0.feature": "sp",
            "atom0.pred0.role": "1",
            "atom0.pred0.operator": "=",
            "atom0.pred0.count": "1",
            "atom0.pred0.value0": "verb",
            "atom0.pred1.feature": "STOP",
            "verify": "yes",
        }
    )
    result = CoordinatedParser(extract_schema(tiny_api), backend).parse(
        "Return phrases without verb words."
    )
    assert result.query and result.projection == (0,)
    assert run_template(tiny_api, result.query).results == ((9,), (11,))


def test_global_context_bypasses_type_scoped_catalog(tiny_api: Any) -> None:
    from scripts.scope_repair import ScopeBackend
    from tests.test_grounded_parser import PlanBackend
    from tf_jev.schema import extract_schema

    base = PlanBackend({"atom0.pred0.feature": "STOP"})
    schema = extract_schema(tiny_api)
    from tf_jev.ontology import CatalogIdentity, OntologyCatalog

    catalog = OntologyCatalog(
        CatalogIdentity("tiny", "test", "1", None, "a" * 64, schema.identity.key, 0, 0, ()), ()
    )
    backend = ScopeBackend(base, catalog)
    request = DecisionRequest(
        dict(request="No conditions.", planned_nodes='["word"]'),
        {"atom0.pred0.feature": ChoiceQuestion("Select", (Option("a", '{"kind":"stop"}'),))},
    )
    backend.decide(request)
    assert base.requests == [request]


def test_scoped_relation_and_output_use_native_pair(tiny_api: Any) -> None:
    from scripts.scope_repair import CoordinatedV3Parser
    from tests.test_grounded_parser import PlanBackend
    from tf_jev.schema import extract_schema

    backend = PlanBackend(
        {
            "shape": "relation",
            "nodes.types": "phrase / word",
            "atom0.pred0.feature": "STOP",
            "relation": "]]",
            "output": "(0,)",
            "verify": "yes",
        }
    )
    result = CoordinatedV3Parser(extract_schema(tiny_api), backend).parse(
        "Return phrases containing words."
    )
    assert result.query
    relation = next(r for r in backend.requests if "relation" in r.questions)
    output = next(r for r in backend.requests if "output" in r.questions)
    assert any(
        "phrase" in (o.description or "") and "contains all slots of" in (o.description or "")
        for o in cast(ChoiceQuestion, relation.questions["relation"]).options
    )
    assert "phrase" in (
        cast(ChoiceQuestion, output.questions["output"]).options[0].description or ""
    )


def test_concrete_predicate_does_not_confuse_literal_and_absence(tiny_api: Any) -> None:
    from scripts.scope_repair import CoordinatedV4Parser
    from tests.conformance.tf_harness import run_template
    from tests.test_grounded_parser import PlanBackend
    from tf_jev.schema import extract_schema

    backend = PlanBackend(
        {
            "shape": "atom",
            "atom0.type": "word",
            "atom0.pred0.feature": "suffix",
            "atom0.pred0.condition": "PRESENT",
            "atom0.pred1.feature": "STOP",
            "verify": "yes",
        }
    )
    result = CoordinatedV4Parser(extract_schema(tiny_api), backend).parse(
        "Return words with suffix present."
    )
    assert result.query
    assert run_template(tiny_api, result.query).results == ((1,), (2,), (3,), (4,))


def test_concrete_absence_retains_unattested_native_feature(tiny_api: Any) -> None:
    from scripts.scope_repair import CoordinatedV4Parser
    from tests.conformance.tf_harness import run_template
    from tests.test_grounded_parser import PlanBackend
    from tf_jev.schema import extract_schema

    schema = extract_schema(tiny_api)
    domain = schema.domain("suffix", "phrase")
    assert domain.missing_count == domain.node_count
    backend = PlanBackend(
        {
            "shape": "atom",
            "atom0.type": "phrase",
            "atom0.pred0.feature": "suffix",
            "atom0.pred0.condition": "ABSENT",
            "atom0.pred1.feature": "STOP",
            "verify": "yes",
        }
    )
    result = CoordinatedV4Parser(schema, backend).parse(
        "Return phrases without a suffix annotation."
    )
    assert result.query and result.projection == (0,)
    assert run_template(tiny_api, result.query).results == ((9,), (10,), (11,), (12,), (13,))
