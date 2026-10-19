"""Research conclusions must fail closed on missing or mismatched evidence."""

from typing import Any

import pytest

from scripts.evaluation_report import compare, decision


def passing() -> dict[str, Any]:
    return dict(
        total=57,
        selection=dict(complete=True),
        partition="heldout",
        result_equivalent_rate=0.9,
        safe_negative_rate=1.0,
        unsafe_supported_on_negative=0,
        emitted_query_native_valid_rate=1.0,
        error_rate=0.0,
        parse_latency_p95_s=2.0,
        estimated_cost_usd_complete=True,
        estimated_cost_usd=0.01,
    )


def test_default_recommendation_requires_every_gate() -> None:
    report = passing()
    assert decision(report)["recommend_default"] is True
    for key, value in [
        ("result_equivalent_rate", 0.79),
        ("safe_negative_rate", 0.94),
        ("unsafe_supported_on_negative", 1),
        ("error_rate", 0.06),
        ("parse_latency_p95_s", 11.0),
        ("estimated_cost_usd", None),
        ("emitted_query_native_valid_rate", None),
    ]:
        bad = report | {key: value}
        assert decision(bad)["recommend_default"] is False
    assert decision(report | {"partition": "development"})["recommend_default"] is False
    assert decision(report | {"selection": {"complete": False}})["recommend_default"] is False


def test_pairing_is_by_case_and_refuses_other_benchmarks() -> None:
    def sample(rows: list[tuple[str, bool]]) -> dict[str, Any]:
        return {
            "partition": "heldout",
            "schema_key": "same",
            "benchmark_sha256": "same",
            "cases": [{"id": k, "expected": "supported", "result_equivalent": v} for k, v in rows],
        }

    left = sample([("a", True), ("b", False), ("c", True)])
    right = sample([("c", True), ("a", False), ("b", True)])
    assert compare(left, right) == dict(both_success=1, left_only=1, right_only=1, both_fail=0)
    for bad in [
        right | {"schema_key": "other"},
        right | {"benchmark_sha256": "other"},
        sample([("a", False)]),
        sample([("a", False), ("a", False)]),
    ]:
        with pytest.raises(ValueError):
            compare(left, bad)


def test_literal_retrieval_audit_uses_candidate_inventory_not_final_success(tiny_api: Any) -> None:
    from scripts.evaluation_report import retrieval_audit
    from tests.test_evaluation import setup

    benchmark, parser = setup(tiny_api)
    rows = []
    for ident, value in [("found", "BR>["), ("miss", "NO_SUCH_VALUE")]:
        rows.append(
            dict(
                id=ident,
                family="literal-lexeme",
                partition="development",
                request=f"Return words whose lex annotation is exactly '{value}'.",
                expected="supported",
                gold={"query": f"word lex={value}"},
            )
        )
    from scripts.nl_benchmark_v2 import Benchmark

    sample = Benchmark(benchmark.corpus, benchmark.features, {}, tuple(rows))
    audit = retrieval_audit(sample, parser.schema, "development")
    assert audit["eligible"] == 2 and audit["recalled"] == 1
    assert audit["recall"] == 0.5
    assert audit["cases"] == [
        {"id": "found", "candidate_contains_gold": True},
        {"id": "miss", "candidate_contains_gold": False},
    ]


def test_paired_negative_requires_integrity_checked_safe_flag() -> None:
    report = {
        "partition": "heldout",
        "schema_key": "s",
        "benchmark_sha256": "b",
        "cases": [
            {"id": "x", "expected": "ambiguous", "predicted": "unsupported", "safe_negative": False}
        ],
    }
    assert compare(report, report)["both_success"] == 0


def test_candidate_audit_also_covers_heldout_literal_annotation_families(tiny_api: Any) -> None:
    from scripts.evaluation_report import retrieval_audit
    from scripts.nl_benchmark_v2 import Benchmark
    from tf_jev.schema import extract_schema

    sample = Benchmark(
        {},
        (),
        {},
        (
            dict(
                id="a",
                family="literal-gloss",
                partition="heldout",
                request="Return words whose lex annotation is exactly 'BR>['.",
                expected="supported",
                gold={"query": "word lex=BR>["},
            ),
            dict(
                id="b",
                family="pointed-lexeme",
                partition="heldout",
                request="Return words whose lex annotation is exactly 'a\\b'.",
                expected="supported",
                gold={"query": "word lex=a\\b"},
            ),
        ),
    )
    result = retrieval_audit(sample, extract_schema(tiny_api), "heldout")
    assert result["eligible"] == result["recalled"] == 2
