"""Evaluate schema-grounded parser results against native Text-Fabric benchmark gold.

The caller verifies pinned corpus source files *before* invoking this offline runner.
This module does not prompt a model, load credentials, or regenerate frozen gold.
"""

from __future__ import annotations

import math
import re
import statistics
import time
from collections import Counter
from typing import Any, Protocol

from scripts.nl_benchmark_v2 import Benchmark, BenchmarkError, execute, projection_valid
from tf_jev.compiler import CompileError, compile_query
from tf_jev.parser import ParseResult, ParseStatus
from tf_jev.schema import CorpusSchema, SchemaError


class ParserLike(Protocol):
    schema: CorpusSchema

    def parse(self, request: str) -> ParseResult: ...


def _price(value: float | None) -> bool:
    return (
        type(value) in (float, int)
        and math.isfinite(value)
        and value >= 0
    )


def _model_id(value: str) -> str:
    """Receipt labels are untrusted; never pass arbitrary backend text to reports."""
    if type(value) is str and re.fullmatch(r"[a-zA-Z0-9_./:@-]{1,128}", value):
        return value
    return "redacted"


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate(
    benchmark: Benchmark,
    parser: ParserLike,
    api: Any,
    *,
    partition: str = "development",
    input_usd_per_million: float | None = None,
    output_usd_per_million: float | None = None,
) -> dict[str, Any]:
    """Score requests without leaking held-out gold or corpus values into the parser.

    Execution equivalence uses the parser's declared projection, never a projection
    retrofitted to gold. Invalid and overflowing native searches count as failures.
    Prices are optional estimates; unknown usage never becomes zero cost.
    """
    if (input_usd_per_million is None) != (output_usd_per_million is None):
        raise ValueError("both token prices are required together")
    if input_usd_per_million is not None and (
        not _price(input_usd_per_million) or not _price(output_usd_per_million)
    ):
        raise ValueError("token prices must be finite nonnegative numbers")
    cases = benchmark.selected(partition)
    summaries: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()
    confusion: Counter[str] = Counter()
    by_difficulty: dict[str, dict[str, int]] = {}
    strict_correct = supported_gold = native_valid = equivalent = exact = 0
    negative = safe_negative = unsafe_supported = 0
    times: list[float] = []
    costs: list[float | None] = []

    for case in cases:
        start = time.perf_counter()
        # Crucially only request prose reaches parse(): no gold, rationales,
        # interpretation labels or other benchmark annotations are provided.
        result = parser.parse(case["request"])
        expected = case["expected"]
        predicted = result.status.value if isinstance(result.status, ParseStatus) else "error"
        statuses[predicted] += 1
        confusion[f"{expected}->{predicted}"] += 1
        strict_correct += int(expected == predicted)
        supported_gold += int(expected == "supported")
        negative += int(expected != "supported")

        integrity = (
            result.schema_key == parser.schema.identity.key
            and (result.status is ParseStatus.SUPPORTED or
                 (result.ir is None and result.query is None and not result.projection))
        )
        valid_compilation: bool | None = None
        valid_native: bool | None = None
        same_results: bool | None = None
        exact_query: bool | None = None

        if result.status is ParseStatus.SUPPORTED:
            valid_compilation = False
            valid_native = False
            if expected == "supported":
                same_results = False
                exact_query = False
            if (integrity and result.ir is not None and type(result.query) is str
                    and projection_valid(result.projection)):
                try:
                    compiled = compile_query(result.ir, parser.schema)
                    valid_compilation = compiled == result.query
                    if valid_compilation:
                        count, fingerprint = execute(api, compiled, result.projection)
                        valid_native = True
                        native_valid += 1
                        if expected == "supported":
                            gold = case["gold"]
                            same_results = (
                                count == gold["count"] and fingerprint == gold["signature"]
                            )
                            exact_query = compiled == gold["query"]
                            equivalent += int(same_results)
                            exact += int(exact_query)
                except (BenchmarkError, CompileError, SchemaError, ValueError):
                    # A failed TF search or validation never becomes an empty result.
                    pass
        if expected != "supported":
            unsafe_supported += int(result.status is ParseStatus.SUPPORTED)
            safe_negative += int(
                integrity and result.status in (
                    ParseStatus.AMBIGUOUS, ParseStatus.UNSUPPORTED, ParseStatus.ABSTAINED
                )
            )

        receipts = tuple(e.receipt for e in result.evidence)
        complete_usage = bool(receipts) and all(
            r.input_tokens is not None and r.output_tokens is not None for r in receipts
        )
        input_tokens = (
            sum(r.input_tokens for r in receipts if r.input_tokens is not None)
            if complete_usage else None
        )
        output_tokens = (
            sum(r.output_tokens for r in receipts if r.output_tokens is not None)
            if complete_usage else None
        )
        estimate = (
            (input_tokens * input_usd_per_million
             + output_tokens * output_usd_per_million) / 1_000_000
            if (complete_usage and input_tokens is not None and output_tokens is not None
                and input_usd_per_million is not None
                and output_usd_per_million is not None)
            else None
        )
        costs.append(estimate)
        duration = max(0.0, time.perf_counter() - start)
        times.append(duration)
        level = by_difficulty.setdefault(case["difficulty"], {"total": 0, "equivalent": 0})
        level["total"] += 1
        level["equivalent"] += int(same_results is True)

        reason = (
            result.reason if type(result.reason) is str
            and re.fullmatch(r"[a-z][a-z0-9_]{0,80}", result.reason) else "redacted"
        )
        confidence = (
            result.confidence if type(result.confidence) in (float, int)
            and math.isfinite(result.confidence) and 0 <= result.confidence <= 1
            else None
        )
        summaries.append({
            "id": case["id"],
            "difficulty": case["difficulty"],
            "expected": expected,
            "predicted": predicted,
            "reason": reason,
            "valid_compilation": valid_compilation,
            "native_valid": valid_native,
            "result_equivalent": same_results,
            "exact_query_match": exact_query,
            "confidence": confidence,
            "latency_s": duration,
            "decision_calls": len(receipts),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": estimate,
            "backend_models": sorted({
                _model_id(r.backend) + "/" + _model_id(r.model) for r in receipts
            }),
        })
    ordered = sorted(times)
    complete_cost = bool(costs) and all(v is not None for v in costs)
    return {
        "version": "nl-tf-v2-evaluation-v1",
        "partition": partition,
        "corpus": benchmark.corpus.copy(),
        "schema_key": parser.schema.identity.key,
        "total": len(summaries),
        "status_counts": dict(sorted(statuses.items())),
        "confusion": dict(sorted(confusion.items())),
        "strict_classification_correct": strict_correct,
        "classification_accuracy": _rate(strict_correct, len(summaries)),
        "supported_gold": supported_gold,
        "native_valid": native_valid,
        "result_equivalent": equivalent,
        "result_equivalent_rate": _rate(equivalent, supported_gold),
        "exact_query_match": exact,
        "negative_gold": negative,
        "safe_negative": safe_negative,
        "safe_negative_rate": _rate(safe_negative, negative),
        "unsafe_supported_on_negative": unsafe_supported,
        "by_difficulty": dict(sorted(by_difficulty.items())),
        "wall_latency_median_s": statistics.median(ordered) if ordered else None,
        "wall_latency_p95_s": ordered[math.ceil(.95 * len(ordered)) - 1] if ordered else None,
        "estimated_cost_usd_complete": complete_cost,
        "estimated_cost_usd": sum(v for v in costs if v is not None) if complete_cost else None,
        "cases": summaries,
    }
