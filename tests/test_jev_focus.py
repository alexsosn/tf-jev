"""Research-only ablations preserve corpus choices, native semantics and gates."""
from typing import Any

import pytest

from scripts.jev_focus import FocusedParser
from tests.conformance.tf_harness import run_template
from tests.test_grounded_parser import PlanBackend, plan
from tf_jev.grounded import GroundedParser
from tf_jev.parser import ParseStatus
from tf_jev.schema import extract_schema


@pytest.mark.parametrize('variant', ['control', 'focused', 'literal'])
def test_research_variants_preserve_native_plan_and_choice_ids(tiny_api: Any, variant: str) -> None:
    schema = extract_schema(tiny_api)
    base_backend = PlanBackend(plan())
    base = GroundedParser(schema, base_backend).parse('Return verbs.')
    backend = PlanBackend(plan())
    result = FocusedParser(schema, backend, variant=variant).parse('Return verbs.')
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert result.ir == base.ir and result.projection == base.projection
    assert run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    for old, new in zip(base_backend.requests, backend.requests, strict=True):
        assert set(old.questions) == set(new.questions)
        name = next(iter(old.questions))
        assert old.questions[name].labels == new.questions[name].labels
        if variant == 'control':
            assert old == new
        else:
            assert 'corpus' not in new.context
            assert new.context['request'] == 'Return verbs.'
            assert 'untrusted' in new.context['contract']
            if name == 'shape':
                assert 'regex' in new.context['grammar']
            if name.endswith('.feature'):
                assert old.questions[name] == new.questions[name]
            if name == 'verify':
                assert new.context['candidate'] == old.context['candidate']
            if variant == 'literal' and name.endswith('.operator'):
                assert 'sp' in new.questions[name].prompt
                assert 'equal' in new.questions[name].options[0].description


def test_focused_variant_retains_refusal_and_confidence_gate(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    for variant in ('focused', 'literal'):
        result = FocusedParser(schema, PlanBackend(plan(), 'atom0.type'), variant=variant).parse(
            'Return verbs.'
        )
        assert result.status is ParseStatus.ABSTAINED and result.reason == 'low_confidence'
        assert result.query is None and result.ir is None and not result.projection
        selected = plan() | {'shape': 'unsupported'}
        result = FocusedParser(schema, PlanBackend(selected), variant=variant).parse('Count verbs.')
        assert result.status is ParseStatus.UNSUPPORTED and result.query is None
    with pytest.raises(ValueError):
        FocusedParser(schema, PlanBackend(plan()), variant='unknown')


def test_literal_variant_roundtrips_actual_sdk(tiny_api: Any, monkeypatch: Any) -> None:
    # Reuse the real-SDK/native integration harness, changing only its parser.
    import tests.test_grounded_parser as integration

    monkeypatch.setattr(
        integration, 'GroundedParser',
        lambda schema, backend: FocusedParser(schema, backend, variant='literal'),
    )
    integration.test_complete_parser_roundtrips_real_sdk(tiny_api)
