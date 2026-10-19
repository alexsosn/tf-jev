"""Research conclusions must fail closed on missing or mismatched evidence."""
from typing import Any

import pytest

from scripts.evaluation_report import compare, decision


def passing() -> dict[str, Any]:
    return dict(total=57, selection=dict(complete=True), partition='heldout',
                result_equivalent_rate=.9, safe_negative_rate=1.,
                unsafe_supported_on_negative=0, emitted_query_native_valid_rate=1.,
                error_rate=0., parse_latency_p95_s=2., estimated_cost_usd_complete=True,
                estimated_cost_usd=.01)


def test_default_recommendation_requires_every_gate() -> None:
    report = passing()
    assert decision(report)['recommend_default'] is True
    for key, value in [('result_equivalent_rate', .79), ('safe_negative_rate', .94),
                       ('unsafe_supported_on_negative', 1), ('error_rate', .06),
                       ('parse_latency_p95_s', 11.), ('estimated_cost_usd', None),
                       ('emitted_query_native_valid_rate', None)]:
        bad = report | {key: value}
        assert decision(bad)['recommend_default'] is False
    assert decision(report | {'partition': 'development'})['recommend_default'] is False
    assert decision(report | {'selection': {'complete': False}})['recommend_default'] is False


def test_pairing_is_by_case_and_refuses_other_benchmarks() -> None:
    def sample(rows: list[tuple[str, bool]]) -> dict[str, Any]:
        return {'partition': 'heldout', 'schema_key': 'same', 'benchmark_sha256': 'same',
                'cases': [{'id': k, 'expected': 'supported', 'result_equivalent': v}
                          for k, v in rows]}
    left = sample([('a', True), ('b', False), ('c', True)])
    right = sample([('c', True), ('a', False), ('b', True)])
    assert compare(left, right) == dict(both_success=1, left_only=1, right_only=1, both_fail=0)
    for bad in [right | {'schema_key': 'other'}, right | {'benchmark_sha256': 'other'},
                sample([('a', False)]), sample([('a', False), ('a', False)])]:
        with pytest.raises(ValueError):
            compare(left, bad)
