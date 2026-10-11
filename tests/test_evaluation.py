"""Tests-first offline evaluation against real tiny Text-Fabric semantics.

Scripted parse results establish evaluator correctness, NOT Jev semantic quality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from scripts.nl_benchmark_v2 import Benchmark, execute
from tf_jev.compiler import compile_query
from tf_jev.decisions import ChoiceDecision, ChoiceQuestion, Option, Receipt
from scripts.semantic_evaluation import evaluate
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.parser import Evidence, ParseResult, ParseStatus
from tf_jev.schema import CorpusSchema, extract_schema


@dataclass
class ScriptedParser:
    schema: CorpusSchema
    responses: dict[str, ParseResult]
    seen: list[str] = field(default_factory=list)

    def parse(self, request: str) -> ParseResult:
        self.seen.append(request)
        return self.responses[request]


def prediction(
    schema: CorpusSchema,
    status: ParseStatus,
    *,
    feature_value: str = "verb",
    query_override: str | None = None,
    meter: bool = False,
) -> ParseResult:
    if status is ParseStatus.SUPPORTED:
        ir = Query((Atom("word", (Predicate("sp", PredicateOp.EQ, (feature_value,)),)),))
        query = compile_query(ir, schema) if query_override is None else query_override
        projection = (0,)
    else:
        ir, query, projection = None, None, ()
    evidence: tuple[Evidence, ...] = ()
    if meter:
        question = ChoiceQuestion("Choose a symbol", (Option("yes"),))
        evidence = (
            Evidence(
                "shape",
                question,
                ChoiceDecision("yes", {"yes": 1.0}),
                Receipt("scripted", "eval-test", 0.12, 100, 20),
            ),
        )
    return ParseResult(
        status, "scripted", ir, query, projection, 0.97, evidence, schema.identity.key
    )


def cases(api: Any) -> tuple[dict[str, Any], ...]:
    verb_count, verb_sig = execute(api, "word sp=verb", (0,))
    noun_count, noun_sig = execute(api, "word sp=subs", (0,))
    return (
        {"id": "a", "family": "verbs", "partition": "development",
         "request": "Return verbs.", "expected": "supported", "difficulty": "easy",
         "rationale": "private benchmark gold", "gold": {
             "query": "word sp=verb", "projection": [0],
             "count": verb_count, "signature": verb_sig}},
        {"id": "b", "family": "nouns", "partition": "development",
         "request": "Return nouns.", "expected": "supported", "difficulty": "hard",
         "rationale": "private benchmark gold", "gold": {
             "query": "word sp=subs", "projection": [0],
             "count": noun_count, "signature": noun_sig}},
        {"id": "c", "family": "amb", "partition": "development",
         "request": "Unknown meaning.", "expected": "ambiguous", "difficulty": "hard",
         "rationale": "private rationale", "interpretations": ["a", "b"]},
        {"id": "d", "family": "uns", "partition": "development",
         "request": "Impossible task.", "expected": "unsupported", "difficulty": "easy",
         "rationale": "private rationale"},
        {"id": "e", "family": "sealed", "partition": "heldout",
         "request": "Sealed.", "expected": "unsupported", "difficulty": "hard",
         "rationale": "private rationale"},
    )


def setup(api: Any) -> tuple[Benchmark, ScriptedParser]:
    schema = extract_schema(api)
    benchmark = Benchmark({"name": "BHSA", "version": "2021", "text_fabric": "13.1.0"},
                          ("sp",), {}, cases(api))
    outputs = {
        "Return verbs.": prediction(schema, ParseStatus.SUPPORTED, meter=True),
        "Return nouns.": prediction(schema, ParseStatus.SUPPORTED, meter=True),
        "Unknown meaning.": prediction(schema, ParseStatus.SUPPORTED),
        "Impossible task.": prediction(schema, ParseStatus.ABSTAINED),
        "Sealed.": prediction(schema, ParseStatus.UNSUPPORTED),
    }
    return benchmark, ScriptedParser(schema, outputs)


def test_projected_native_equivalence_and_safe_abstention(tiny_api: Any) -> None:
    benchmark, parser = setup(tiny_api)
    report = evaluate(benchmark, parser, tiny_api)
    assert parser.seen == [c["request"] for c in benchmark.selected()]
    assert report["partition"] == "development"
    assert report["total"] == 4
    assert report["strict_classification_correct"] == 2
    assert report["supported_gold"] == 2
    assert report["native_valid"] == 3
    assert report["result_equivalent"] == 1
    assert report["unsafe_supported_on_negative"] == 1
    assert report["safe_negative"] == 1
    assert report["by_difficulty"]["easy"]["total"] == 2
    assert report["by_difficulty"]["hard"]["total"] == 2
    assert report["cases"][0]["result_equivalent"] is True
    assert cases(tiny_api)[0]["gold"]["count"] == cases(tiny_api)[1]["gold"]["count"]
    assert cases(tiny_api)[0]["gold"]["signature"] != cases(tiny_api)[1]["gold"]["signature"]
    assert report["cases"][1]["native_valid"] is True
    assert report["cases"][1]["result_equivalent"] is False
    assert report["cases"][2]["result_equivalent"] is None
    assert report["cases"][3]["native_valid"] is None
    assert all("query" not in c and "request" not in c and "rationale" not in c
               for c in report["cases"])
    assert "private" not in str(report)
    assert report["wall_latency_p95_s"] >= report["wall_latency_median_s"] >= 0


def test_token_price_unknown_is_not_free(tiny_api: Any) -> None:
    benchmark, parser = setup(tiny_api)
    report = evaluate(benchmark, parser, tiny_api,
                      input_usd_per_million=2.0, output_usd_per_million=10.0)
    assert report["cases"][0]["estimated_cost_usd"] == pytest.approx(0.0004)
    assert report["cases"][0]["input_tokens"] == 100
    assert report["cases"][0]["output_tokens"] == 20
    assert report["cases"][0]["backend_models"] == ["scripted/eval-test"]
    assert report["cases"][2]["estimated_cost_usd"] is None
    assert report["estimated_cost_usd_complete"] is False
    assert report["estimated_cost_usd"] is None
    assert evaluate(benchmark, parser, tiny_api)["cases"][0]["estimated_cost_usd"] is None


def test_heldout_partition_only_sends_requests(tiny_api: Any) -> None:
    benchmark, parser = setup(tiny_api)
    report = evaluate(benchmark, parser, tiny_api, partition="heldout")
    assert parser.seen == ["Sealed."]
    assert report["total"] == 1
    assert report["supported_gold"] == 0
    assert report["result_equivalent_rate"] is None
    assert report["safe_negative"] == 1


def test_forged_compiler_output_and_schema_are_rejected(tiny_api: Any) -> None:
    benchmark, parser = setup(tiny_api)
    original = parser.responses["Return verbs."]
    parser.responses["Return verbs."] = ParseResult(
        original.status, original.reason, original.ir, "word sp=verb\nword sp=noun",
        original.projection, original.confidence, original.evidence, original.schema_key
    )
    report = evaluate(benchmark, parser, tiny_api)
    assert report["cases"][0]["valid_compilation"] is False
    assert report["cases"][0]["native_valid"] is False
    assert report["cases"][0]["result_equivalent"] is False
    assert report["result_equivalent"] == 0
    parser.responses["Return verbs."] = ParseResult(
        original.status, original.reason, original.ir, original.query,
        original.projection, original.confidence, original.evidence, "stale"
    )
    assert evaluate(benchmark, parser, tiny_api)["cases"][0]["valid_compilation"] is False


@pytest.mark.parametrize("prices", [(True, 1.0), (float("nan"), 2.0), (-1.0, 2.0),
                                      (1.0, None), (None, 1.0)])
def test_invalid_or_incomplete_pricing_fails_closed(tiny_api: Any, prices: tuple[Any, Any]) -> None:
    benchmark, parser = setup(tiny_api)
    with pytest.raises(ValueError):
        evaluate(benchmark, parser, tiny_api,
                 input_usd_per_million=prices[0], output_usd_per_million=prices[1])


def test_unknown_partition_fails_before_calling_parser(tiny_api: Any) -> None:
    benchmark, parser = setup(tiny_api)
    with pytest.raises(ValueError):
        evaluate(benchmark, parser, tiny_api, partition="all")
    assert parser.seen == []
