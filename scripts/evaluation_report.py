"""Frozen engineering decision gates and paired evaluation outcomes."""

from __future__ import annotations

from typing import Any


def decision(report: dict[str, Any]) -> dict[str, Any]:
    def at_least(key: str, limit: float) -> bool:
        value = report.get(key)
        return (
            isinstance(value, (int, float)) and not isinstance(value, bool) and limit <= value <= 1
        )

    def at_most(key: str, limit: float) -> bool:
        value = report.get(key)
        return (
            isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= limit
        )

    total = report.get("total", 0)
    gates = {
        "complete_heldout": report.get("partition") == "heldout"
        and report.get("selection", {}).get("complete") is True
        and total > 0,
        "supported_equivalence": at_least("result_equivalent_rate", 0.8),
        "safe_negatives": at_least("safe_negative_rate", 0.95)
        and report.get("unsafe_supported_on_negative") == 0,
        "native_validity": report.get("emitted_query_native_valid_rate") == 1.0,
        "error_rate": at_most("error_rate", 0.05),
        "parse_p95": at_most("parse_latency_p95_s", 10.0),
        "mean_estimated_cost": report.get("estimated_cost_usd_complete") is True
        and total > 0
        and at_most("estimated_cost_usd", total * 0.001),
    }
    return {"gates": gates, "recommend_default": all(gates.values())}


def compare(left: dict[str, Any], right: dict[str, Any]) -> dict[str, int]:
    for key in ("partition", "schema_key", "benchmark_sha256"):
        if not left.get(key) or left.get(key) != right.get(key):
            raise ValueError("comparison identity mismatch")

    def outcomes(report: dict[str, Any]) -> dict[str, tuple[str, bool]]:
        rows = report["cases"]
        result = {}
        for row in rows:
            positive = row["expected"] == "supported"
            success = (
                row.get("result_equivalent") is True
                if positive
                else row.get("safe_negative") is True
            )
            result[row["id"]] = (row["expected"], success)
        if len(result) != len(rows):
            raise ValueError("duplicate cases")
        return result

    a, b = outcomes(left), outcomes(right)
    if a.keys() != b.keys() or any(a[k][0] != b[k][0] for k in a):
        raise ValueError("comparison case mismatch")
    counts = dict(both_success=0, left_only=0, right_only=0, both_fail=0)
    for key in a:
        x, y = a[key][1], b[key][1]
        counts[
            "both_success" if x and y else "left_only" if x else "right_only" if y else "both_fail"
        ] += 1
    return counts


def retrieval_audit(benchmark: Any, schema: Any, partition: str) -> dict[str, Any]:
    """Post-parse coverage of canonical atomic literal annotations, not semantic recall.

    Reuse the exact unchanged parser candidate routine (including its budgets).
    Gold is only the independent comparison target; it never enters seed creation.
    """
    import re

    from tf_jev.decisions import ScriptedBackend
    from tf_jev.parser import SemanticParser, _Run, _Stop

    cases = []
    for case in benchmark.selected(partition):
        if case["expected"] != "supported" or case["family"] not in (
            "literal-lexeme",
            "literal-gloss",
            "pointed-lexeme",
        ):
            continue
        match = re.fullmatch(r"word ([A-Za-z_][A-Za-z_0-9]*)=([^\s|]+)", case["gold"]["query"])
        if not match:
            continue
        run = _Run(SemanticParser(schema, ScriptedBackend({})), case["request"])
        try:
            feature = schema.node_feature(match[1], "word")
            candidates = run.string_values(feature, "word")
        except _Stop:
            candidates = []
        cases.append({"id": case["id"], "candidate_contains_gold": match[2] in candidates})
    recalled = sum(c["candidate_contains_gold"] for c in cases)
    return {
        "scope": "single_atom_exact_literal_annotation_families",
        "eligible": len(cases),
        "recalled": recalled,
        "recall": recalled / len(cases) if cases else None,
        "cases": cases,
    }
