"""Rule baseline must compile with the same schema and native TF semantics."""

from typing import Any

import pytest

from scripts.rule_baseline import BHSARuleParser
from tests.conformance.tf_harness import run_template
from tf_jev.parser import ParseStatus
from tf_jev.schema import extract_schema


@pytest.mark.parametrize(
    "text",
    [
        "Return all words annotated as verbs.",
        "Return words whose lex annotation is exactly 'BR>['.",
    ],
)
def test_atomic_rules_execute_native(tiny_api: Any, text: str) -> None:
    parser = BHSARuleParser(extract_schema(tiny_api))
    result = parser.parse(text)
    assert result.status is ParseStatus.SUPPORTED
    assert result.query and result.ir and result.projection == (0,)
    native = run_template(tiny_api, result.query, limit=100)
    assert native.ok
    assert native.results == (((3,), (6,), (8,)) if "verbs" in text else ((3,),))
    assert result.evidence == ()


@pytest.mark.parametrize(
    "text",
    [
        "Return clauses containing no words annotated as verbs.",
        "Return all words annotated as flying verbs.",
        "Return all words annotated as verbs. Then count them.",
        "Return words whose lex annotation is exactly 'NOT_ATTESTED'.",
        "Return only the first ten nouns.",
    ],
)
def test_rules_refuse_incomplete_or_unknown_semantics(tiny_api: Any, text: str) -> None:
    result = BHSARuleParser(extract_schema(tiny_api)).parse(text)
    assert result.status is ParseStatus.UNSUPPORTED
    assert result.ir is None and result.query is None and result.projection == ()


def test_morphology_rule_requires_all_conjuncts(tiny_api: Any) -> None:
    result = BHSARuleParser(extract_schema(tiny_api)).parse(
        "Return nouns annotated as feminine and plural."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(tiny_api, result.query, limit=100).results == ((5,),)
