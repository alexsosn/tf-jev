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
