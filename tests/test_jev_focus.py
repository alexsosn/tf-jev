"""Research-only ablations preserve corpus choices, native semantics and gates."""

from typing import Any

import pytest

from scripts.jev_focus import FocusedParser
from tests.conformance.tf_harness import run_template
from tests.test_grounded_parser import PlanBackend, plan
from tf_jev.decisions import ChoiceQuestion
from tf_jev.grounded import GroundedParser
from tf_jev.parser import ParseStatus
from tf_jev.schema import extract_schema


@pytest.mark.parametrize("variant", ["control", "focused", "literal"])
def test_research_variants_preserve_native_plan_and_choice_ids(tiny_api: Any, variant: str) -> None:
    schema = extract_schema(tiny_api)
    base_backend = PlanBackend(plan())
    base = GroundedParser(schema, base_backend).parse("Return verbs.")
    backend = PlanBackend(plan())
    result = FocusedParser(schema, backend, variant=variant).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert result.ir == base.ir and result.projection == base.projection
    assert run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    for old, new in zip(base_backend.requests, backend.requests, strict=True):
        assert set(old.questions) == set(new.questions)
        name = next(iter(old.questions))
        assert old.questions[name].labels == new.questions[name].labels
        if variant == "control":
            assert old == new
        else:
            assert "corpus" not in new.context
            assert new.context["request"] == "Return verbs."
            assert "untrusted" in new.context["contract"]
            if name == "shape":
                assert "regex" in new.context["grammar"]
            if name.endswith(".feature"):
                assert old.questions[name] == new.questions[name]
            if name == "verify":
                assert new.context["candidate"] == old.context["candidate"]
            if variant == "literal" and name.endswith(".operator"):
                assert "sp" in new.questions[name].prompt
                assert "equal" in new.questions[name].options[0].description


def test_focused_variant_retains_refusal_and_confidence_gate(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    for variant in ("focused", "literal"):
        result = FocusedParser(schema, PlanBackend(plan(), "atom0.type"), variant=variant).parse(
            "Return verbs."
        )
        assert result.status is ParseStatus.ABSTAINED and result.reason == "low_confidence"
        assert result.query is None and result.ir is None and not result.projection
        selected = plan() | {"shape": "unsupported"}
        result = FocusedParser(schema, PlanBackend(selected), variant=variant).parse("Count verbs.")
        assert result.status is ParseStatus.UNSUPPORTED and result.query is None
    with pytest.raises(ValueError):
        FocusedParser(schema, PlanBackend(plan()), variant="unknown")


def test_literal_variant_roundtrips_actual_sdk(tiny_api: Any, monkeypatch: Any) -> None:
    # Reuse the real-SDK/native integration harness, changing only its parser.
    import tests.test_grounded_parser as integration

    monkeypatch.setattr(
        integration,
        "GroundedParser",
        lambda schema, backend: FocusedParser(schema, backend, variant="literal"),
    )
    integration.test_complete_parser_roundtrips_real_sdk(tiny_api)


@pytest.mark.parametrize("variant", ["control", "request_only", "plain", "reverse"])
def test_type_probe_keeps_all_corpus_types_and_local_labels(tiny_api: Any, variant: str) -> None:
    from scripts.jev_focus import type_probe

    backend = PlanBackend(plan())
    FocusedParser(extract_schema(tiny_api), backend).parse("Return verbs.")
    base = backend.requests[1]
    changed = type_probe(base, variant)
    question = next(iter(changed.questions.values()))
    original = next(iter(base.questions.values()))
    assert isinstance(question, ChoiceQuestion) and isinstance(original, ChoiceQuestion)
    assert set(question.labels) == set(original.labels)
    if variant == "control":
        assert changed == base
    else:
        assert set(changed.context) == {"request", "contract"}
        assert changed.context["request"] == "Return verbs."
        if variant in ("plain", "reverse"):
            import json

            mapping = {o.label: json.loads(o.description or "")["name"] for o in original.options}
            assert {o.label: o.description for o in question.options} == mapping
            assert "atom" not in question.prompt


def test_attested_type_context_uses_real_capabilities_without_shape_history(tiny_api: Any) -> None:
    import json

    schema = extract_schema(tiny_api)
    backend = PlanBackend(plan())
    result = FocusedParser(schema, backend, variant="attested").parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED
    request = backend.requests[1]
    assert set(request.context) == {"request", "contract", "types"}
    types = json.loads(request.context["types"])
    assert {t["name"] for t in types} == set(schema.object_types)
    for t in types:
        assert set(t["attested_features"]) == {
            f.name
            for f in schema.node_features
            if schema.domain(f.name, t["name"]).missing_count
            < schema.domain(f.name, t["name"]).node_count
        }
    assert "selected" not in request.context and "focus" not in request.context


def test_feature_set_is_independent_bounded_choices_on_every_native_feature(tiny_api: Any) -> None:
    from scripts.jev_focus import feature_request

    schema = extract_schema(tiny_api)
    request = feature_request(schema, "Return feminine plural verbs.", "word", "output")
    assert len(request.questions) == len(schema.node_features)
    for feature, question in zip(schema.node_features, request.questions.values(), strict=True):
        assert isinstance(question, ChoiceQuestion)
        assert question.labels == ("o000", "o001")
        assert feature.name in question.prompt
        assert "explicit" in question.prompt
    assert set(request.context) == {"request", "object_type", "role", "contract"}
    with pytest.raises(ValueError):
        feature_request(schema, "Return verbs.", "unknown-type", "output")


def test_ranked_feature_is_only_a_proposal_until_independent_acceptance(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    selected = plan() | {"atom0.pred0.feature_check": "yes", "atom0.pred1.feature_check": "yes"}
    good = FocusedParser(
        schema, PlanBackend(selected, "atom0.pred0.feature"), variant="ranked"
    ).parse("Return verbs.")
    assert good.status is ParseStatus.SUPPORTED and good.confidence == pytest.approx(0.65)
    selected["atom0.pred0.feature_check"] = "no"
    rejected = FocusedParser(schema, PlanBackend(selected), variant="ranked").parse("Return verbs.")
    assert rejected.query is None and rejected.ir is None and not rejected.projection
    selected["atom0.pred0.feature_check"] = "yes"
    uncertain = FocusedParser(
        schema, PlanBackend(selected, "atom0.pred0.feature_check"), variant="ranked"
    ).parse("Return verbs.")
    assert uncertain.query is None and uncertain.reason == "low_confidence"


def test_property_probe_names_meaning_without_planning_history(tiny_api: Any) -> None:
    from scripts.jev_focus import property_probe

    schema = extract_schema(tiny_api)
    feature = next(f for f in schema.node_features if f.name == "gn")
    request = property_probe("Return feminine verbs.", "word", "requested output node", feature)
    assert request.context["property_id"] == "gn"
    assert request.context["property_meaning"] == (feature.description or feature.name)
    assert "selected" not in request.context and "focus" not in request.context
    assert "need not appear" in next(iter(request.questions.values())).prompt


def test_predicate_probe_distinguishes_required_from_merely_related(tiny_api: Any) -> None:
    from scripts.jev_focus import predicate_probe
    from tf_jev.ir import Predicate, PredicateOp

    schema = extract_schema(tiny_api)
    feature = next(f for f in schema.node_features if f.name == "gn")
    request = predicate_probe(
        "Return feminine verbs.", "word", feature, Predicate("gn", PredicateOp.EQ, ("f",))
    )
    question = next(iter(request.questions.values()))
    assert isinstance(question, ChoiceQuestion) and len(question.options) == 3
    assert "not stated" in (question.options[2].description or "")
    assert "candidate" in request.context and "selected" not in request.context


def test_concrete_strategy_accepts_only_complete_required_predicates(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    selected = plan() | {
        "atom0.pred0.predicate_check": "required",
        "atom0.pred1.feature_check": "yes",
    }
    good = FocusedParser(
        schema, PlanBackend(selected, "atom0.pred0.feature"), variant="concrete"
    ).parse("Return verbs.")
    assert good.status is ParseStatus.SUPPORTED and good.confidence == pytest.approx(0.65)
    assert all(e.id != "atom0.pred0.feature_check" for e in good.evidence)
    selected["atom0.pred0.predicate_check"] = "not stated"
    no = FocusedParser(schema, PlanBackend(selected), variant="concrete").parse("Return verbs.")
    assert no.query is None and no.ir is None and not no.projection


def test_concrete_predicate_checks_preserve_parent_child_scope(tiny_api: Any) -> None:
    import json

    selected = plan() | {
        "shape": "without",
        "atom0.type": "phrase",
        "atom0.pred0.feature": "function",
        "atom0.pred0.value0": "Objc",
        "atom0.pred0.predicate_check": "required",
        "atom0.pred1.feature_check": "yes",
        "atom1.type": "word",
        "atom1.pred0.feature": "sp",
        "atom1.pred0.operator": "=",
        "atom1.pred0.count": "1",
        "atom1.pred0.value0": "adjv",
        "atom1.pred0.predicate_check": "required",
        "atom1.pred1.feature_check": "yes",
    }
    backend = PlanBackend(selected)
    result = FocusedParser(extract_schema(tiny_api), backend, variant="concrete").parse(
        "Select object phrases containing no adjective words."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(tiny_api, result.query).results == ((12,),)
    checks = [
        json.loads(r.context["candidate"])
        for r in backend.requests
        if next(iter(r.questions)).endswith(".predicate_check")
    ]
    assert checks[0]["role"] == "returned parent"
    assert checks[1]["role"] == "excluded child witness"
