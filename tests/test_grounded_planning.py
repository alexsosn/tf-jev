"""Research helpers: real schema, hostile responses, honest selective calibration."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from scripts.grounded_planning import build_probe, calibrate, measure, select_cases
from scripts.nl_benchmark_v2 import load_benchmark
from tf_jev.decisions import (
    Capabilities,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBatch,
    Receipt,
)
from tf_jev.schema import extract_schema


def test_selection_is_first_and_last_development_per_family() -> None:
    cases = select_cases()
    assert len(cases) == 16
    assert {c["partition"] for c in cases} == {"development"}
    all_cases = load_benchmark().selected("development")
    for family in {c["family"] for c in cases}:
        family_cases = [c for c in all_cases if c["family"] == family]
        assert [c["id"] for c in cases if c["family"] == family] == [
            family_cases[0]["id"],
            family_cases[-1]["id"],
        ]


def test_payload_is_actual_schema_and_explicit_grammar_without_values(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    request, keys = build_probe(schema, "private request", "support")
    assert keys == ("atom", "relation", "without", "ambiguous", "unsupported")
    corpus = json.loads(request.context["corpus"])
    assert [t["name"] for t in corpus["types"]] == list(schema.object_types)
    assert {f["name"] for f in corpus["features"]} == {f.name for f in schema.node_features}
    assert "rows" not in corpus and "values" not in request.context["corpus"]
    assert "regex" in request.context["grammar"] and "top-N" in request.context["grammar"]
    assert "private request" == request.context["request"]
    question = request.questions["support"]
    assert isinstance(question, ChoiceQuestion)
    assert all(o.label.startswith("o") for o in question.options)


def test_type_roles_and_next_feature_done_are_not_counting(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    request, keys = build_probe(schema, "Return feminine nouns.", "type")
    question = request.questions["type"]
    assert isinstance(question, ChoiceQuestion)
    opts = question.options
    assert "slot" in (opts[keys.index("word")].description or "")
    assert "non-slot" in (opts[keys.index("phrase")].description or "")
    request, keys = build_probe(schema, "Return feminine nouns.", "feature", "word", ("sp",))
    assert "sp" not in keys and "gn" in keys and "function" in keys and keys[-1] == "DONE"
    assert json.loads(request.context["selected_features"]) == ["sp"]
    assert "How many" not in request.questions["feature"].prompt
    assert "count" not in request.questions


def test_partial_or_over_budget_or_invalid_history_refuses(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    with pytest.raises(ValueError):
        build_probe(extract_schema(tiny_api, node_features=("sp",)), "request", "support")
    with pytest.raises(ValueError):
        build_probe(schema, "x" * 70000, "support")
    for kind, history in [("invented", ()), ("word", ("invented",)), ("word", ("sp", "sp"))]:
        with pytest.raises(ValueError):
            build_probe(schema, "request", "feature", kind, history)
    with pytest.raises(ValueError):
        build_probe(replace(schema, node_features=schema.node_features * 30), "r", "support")


class First:
    capabilities = Capabilities()

    def decide(self, request: Any) -> DecisionBatch:
        name, q = next(iter(request.questions.items()))
        return DecisionBatch(
            {
                name: ChoiceDecision(
                    q.options[0].label, {o.label: float(i == 0) for i, o in enumerate(q.options)}
                )
            },
            Receipt("fake", "test", 0.1, 10, 2),
        )


def test_measure_validates_bounds_and_keeps_errors_private(tiny_api: Any) -> None:
    request, keys = build_probe(extract_schema(tiny_api), "secret prose", "support")
    result = measure(First(), request, keys, {"atom"})
    assert result["correct"] is True and result["selected_index"] == 0
    assert result["input_tokens"] == 10 and result["error_kind"] is None
    assert "secret" not in json.dumps(result)

    class Hostile(First):
        def decide(self, request: Any) -> Any:
            raise RuntimeError("credential-bearing private server error")

    failed = measure(Hostile(), request, keys, {"atom"})
    assert failed["correct"] is None and failed["input_tokens"] is None
    assert failed["error_kind"] == "contract" and "credential" not in json.dumps(failed)
    with pytest.raises(ValueError):
        measure(First(), request, keys, {"invented"})


def row(case: str, family: str, p: float, correct: bool) -> dict[str, Any]:
    return dict(
        id=case,
        family=family,
        top_probability=p,
        margin=2 * p - 1,
        correct=correct,
        error_kind=None,
    )


def test_calibration_holds_entire_family_out_and_requires_distinct_cases() -> None:
    rows = [row("a", "A", 0.9, True), row("b", "B", 0.9, True), row("c", "C", 0.95, False)]
    result = calibrate(rows)
    fold = next(f for f in result["folds"] if f["family"] == "C")
    assert fold["policy"] is not None and fold["accepted"] == 1 and fold["wrong"] == 1
    assert all(f["policy"] is None for f in result["folds"] if f["family"] != "C")
    assert result["cross_validated_wrong"] == 1
    repeated = [row("a", "A", 0.9, True), row("a", "A", 0.9, True), row("b", "B", 0.9, True)]
    assert all(f["policy"] is None for f in calibrate(repeated)["folds"])


def test_errors_remain_in_denominator_and_invalid_metrics_refuse() -> None:
    rows = [
        row("a", "A", 0.9, True),
        row("b", "B", 0.9, True),
        dict(
            id="c",
            family="C",
            top_probability=None,
            margin=None,
            correct=None,
            error_kind="timeout",
        ),
    ]
    assert calibrate(rows)["total"] == 3
    for bad in [True, float("nan"), float("inf"), -0.1, 1.1]:
        changed = [dict(rows[0], top_probability=bad)]
        with pytest.raises(ValueError):
            calibrate(changed)


def test_real_native_references_and_all_oracle_prefixes(tiny_api: Any) -> None:
    from scripts.grounded_planning import probes
    from tests.conformance.tf_harness import run_template

    schema = extract_schema(tiny_api)
    case: dict[str, Any] = dict(
        id="test",
        family="gender-number",
        expected="supported",
        request="Return feminine plural verbs.",
        gold=dict(query="word sp=verb gn=f nu=pl"),
    )
    rows = probes(schema, case)
    assert [r[2] for r in rows if r[1] == "feature"] == [0, 1, 2, 3]
    assert [r[-1] for r in rows if r[1] == "feature"] == [
        {"sp", "gn", "nu"},
        {"gn", "nu"},
        {"nu"},
        {"DONE"},
    ]
    assert run_template(tiny_api, case["gold"]["query"]).results == ((6,),)
    control = rows[0][3]
    assert "corpus" not in control.context
    assert all("gold" not in r[3].context for r in rows)


def test_forged_response_cannot_score_correct(tiny_api: Any) -> None:
    request, keys = build_probe(extract_schema(tiny_api), "request", "support")

    class Forged(First):
        def decide(self, request: Any) -> DecisionBatch:
            return DecisionBatch(
                {"support": ChoiceDecision("invented", {"invented": 1.0})},
                Receipt("fake", "test", 0.0, 11, 3),
            )

    row = measure(Forged(), request, keys, {"atom"})
    assert row["error_kind"] == "contract" and row["correct"] is None
    assert row["input_tokens"] == 11  # returned usage remains known despite invalid decision


def test_live_gates_precede_source_and_client(tmp_path: Any, monkeypatch: Any) -> None:
    from scripts import grounded_planning as study

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("source gate or client reached before opt-in/output checks")

    monkeypatch.setattr(study, "verify_sources", forbidden)
    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    with pytest.raises(ValueError, match="requires"):
        study.main([str(tmp_path), "--output", str(tmp_path / "new"), "--live"])
    monkeypatch.setenv("TF_JEV_LIVE", "1")
    with pytest.raises(ValueError, match="new"):
        study.main([str(tmp_path), "--output", str(tmp_path), "--live"])


def test_all_stages_use_real_sdk_and_once_per_call_accounting(tiny_api: Any) -> None:
    http = pytest.importorskip("httpx2")
    sdk = pytest.importorskip("typesafe_sdk")
    from tf_jev.jev import JevBackend

    calls = []

    def handle(request: Any) -> Any:
        body = json.loads(request.content)
        calls.append(body)
        answers = {}
        for name, q in body["questions"].items():
            labels = list(q["criteria"])
            answers[name] = dict(
                type="choice",
                choice=labels[0],
                confidence=1.0,
                probabilities={k: float(i == 0) for i, k in enumerate(labels)},
            )
        return http.Response(
            200,
            json=dict(
                model="jev-1.13.0", answers=answers, usage=dict(input_tokens=13, output_tokens=7)
            ),
            request=request,
        )

    schema = extract_schema(tiny_api)
    with sdk.TypeSafeClient(
        api_key="test-only",
        transport=http.MockTransport(handle),
        retry=sdk.RetryPolicy(max_retries=0),
    ) as client:
        with JevBackend(client=client) as backend:
            for stage in ("support", "type", "feature"):
                request, keys = build_probe(schema, "request", stage, "word")
                row = measure(backend, request, keys, {keys[0]})
                assert row["correct"] and row["input_tokens"] == 13
                assert row["error_kind"] is None
    assert len(calls) == 3


def test_calibration_rejects_same_case_in_multiple_families() -> None:
    with pytest.raises(ValueError, match="family"):
        calibrate([row("same", "A", 0.9, True), row("same", "B", 0.9, True)])


def test_done_sentinel_cannot_collide_with_a_real_feature(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    original = schema.node_features[0]
    schema = replace(
        schema, node_features=(replace(original, name="DONE"), *schema.node_features[1:])
    )
    with pytest.raises(ValueError, match="sentinel"):
        build_probe(schema, "request", "feature", "word")


def test_cli_runs_saved_native_corpus_before_constructing_backend(
    tmp_path: Any,
    monkeypatch: Any,
) -> None:
    import tf_jev.jev as adapter
    from scripts import grounded_planning as study
    from scripts.nl_benchmark_v2 import execute
    from tests.conformance.tf_harness import build_tiny_corpus, load_api

    corpus = tmp_path / "corpus"
    corpus.mkdir()
    build_tiny_corpus(corpus)
    api = load_api(corpus)
    count, digest = execute(api, "word sp=verb", (0,))
    case: dict[str, Any] = dict(
        id="test",
        family="part-of-speech",
        expected="supported",
        request="Return verbs.",
        gold=dict(query="word sp=verb", projection=[0], count=count, signature=digest),
    )
    source_checked = []

    def check_sources(path: Any) -> dict[str, str]:
        source_checked.append(path)
        return {}

    monkeypatch.setattr(study, "verify_sources", check_sources)
    monkeypatch.setattr(study, "select_cases", lambda: [case])
    monkeypatch.setenv("TF_JEV_LIVE", "1")
    created = []

    class Client(First):
        def __init__(self) -> None:
            assert source_checked == [corpus]
            created.append(True)

        def __enter__(self) -> Any:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

    monkeypatch.setattr(adapter, "JevBackend", Client)
    output = tmp_path / "report"
    assert study.main([str(corpus), "--output", str(output), "--live"]) == 0
    report = json.loads((output / "observations.json").read_text())
    assert report["complete"] is True and report["scheduled_calls"] == len(report["rows"]) == 10
    assert sum(r["input_tokens"] for r in report["rows"]) == 100
    assert all("Return verbs" not in json.dumps(r) for r in report["rows"])
    assert len(created) == 1
    case["gold"]["signature"] = "0" * 64
    with pytest.raises(ValueError, match="gold mismatch"):
        study.main([str(corpus), "--output", str(tmp_path / "bad"), "--live"])
    assert len(created) == 1  # corrupt native evidence cannot cause an API call


def test_review_fixes_preserve_frozen_study_analysis() -> None:
    from pathlib import Path

    from scripts.grounded_planning import analyze

    root = Path(__file__).resolve().parents[1] / "reports/grounded-planning-2026-10-20/live"
    observed = json.loads((root / "observations.json").read_text())
    recorded = json.loads((root / "analysis.json").read_text())
    assert observed["complete"] and len(observed["rows"]) == observed["scheduled_calls"] == 138
    assert analyze(observed["rows"]) == recorded
    assert {r["model"] for r in observed["rows"]} == {"jev-1.13.0"}
    assert sum(r["input_tokens"] for r in observed["rows"]) == 1_141_174
    assert sum(r["output_tokens"] for r in observed["rows"]) == 63_200
