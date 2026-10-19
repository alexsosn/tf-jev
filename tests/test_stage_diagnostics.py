"""Diagnostic observation must not alter the parser or disclose request data."""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.diagnose_abstention import TraceBackend, summarize
from tests.conformance.tf_harness import run_template
from tests.test_parser import ChoosingBackend, choices
from tf_jev.decisions import (
    BackendError,
    Capabilities,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBatch,
    DecisionRequest,
    Option,
    Receipt,
)
from tf_jev.parser import SemanticParser
from tf_jev.schema import extract_schema


def test_trace_is_transparent_and_native_results_unchanged(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    plain = SemanticParser(schema, ChoosingBackend(choices())).parse("Return verbs.")
    trace = TraceBackend(ChoosingBackend(choices()))
    observed = SemanticParser(schema, trace).parse("Return verbs.")
    assert observed == plain
    assert observed.query and run_template(tiny_api, observed.query).results == ((3,), (6,), (8,))
    assert len(trace.calls) == len(observed.evidence) == 8
    assert all(c["input_tokens"] == 10 for c in trace.calls)
    assert trace.calls[0]["questions"][0]["probabilities"] == pytest.approx(
        [0.98, 0.005, 0.005, 0.005, 0.005]
    )
    assert trace.calls[0]["questions"][0]["selected_index"] == 0
    text = json.dumps(trace.calls)
    assert "Return verbs" not in text and "word" not in text and "verb" not in text
    assert summarize(observed, trace.calls)["stopping_question"] is None


@pytest.mark.parametrize("stage", ["shape", "atom0.type", "atom0.pred0.feature"])
def test_low_confidence_stop_identifies_exact_stage(tiny_api: Any, stage: str) -> None:
    trace = TraceBackend(ChoosingBackend(choices(), weak=stage))
    result = SemanticParser(extract_schema(tiny_api), trace).parse("Return verbs.")
    report = summarize(result, trace.calls)
    assert report["stopping_question"] == stage
    assert report["last_observed_question"] == stage
    assert report["calls"][-1]["questions"][0]["top_probability"] == 0.6
    assert report["calls"][-1]["questions"][0]["margin"] < 0.8


def test_failed_attempt_does_not_leak_exception_or_look_free(tiny_api: Any) -> None:
    class Broken:
        capabilities = Capabilities()

        def decide(self, request: Any) -> Any:
            raise BackendError("secret_private_body")

    trace = TraceBackend(Broken())
    result = SemanticParser(extract_schema(tiny_api), trace).parse("secret user request")
    assert len(trace.calls) == 1
    row = trace.calls[0]
    assert row["error_kind"] == "other"
    assert row["input_tokens"] is None and row["output_tokens"] is None
    assert row["questions"] == []
    assert "secret" not in json.dumps(summarize(result, trace.calls))


def test_batch_usage_once_and_no_raw_labels_names_or_descriptions() -> None:
    class Backend:
        capabilities = Capabilities()

        def decide(self, request: DecisionRequest) -> DecisionBatch:
            return DecisionBatch(
                {
                    name: ChoiceDecision("private_label", {"private_label": 1.0})
                    for name in request.questions
                },
                Receipt("fake", "fake", 0.0, 13, 7),
            )

    request = DecisionRequest(
        {"request": "private_request"},
        {
            name: ChoiceQuestion(
                "private_prompt", (Option("private_label", "private_description"),)
            )
            for name in ("private_question", "probe0")
        },
    )
    trace = TraceBackend(Backend())
    result = trace.decide(request)
    assert result.receipt.input_tokens == 13
    assert len(trace.calls) == 1 and trace.calls[0]["input_tokens"] == 13
    assert len(trace.calls[0]["questions"]) == 2
    assert trace.calls[0]["questions"][0]["question"] == "redacted"
    assert "private" not in json.dumps(trace.calls)


def test_malformed_backend_distribution_is_not_exported(tiny_api: Any) -> None:
    class Forged:
        capabilities = Capabilities()

        def decide(self, request: Any) -> DecisionBatch:
            return DecisionBatch(
                {"shape": ChoiceDecision("secret", {"secret": 1.0})},
                Receipt("fake", "fake", 0.0, 10, 2),
            )

    trace = TraceBackend(Forged())
    result = SemanticParser(extract_schema(tiny_api), trace).parse("Return verbs.")
    assert result.status.value == "error"
    assert trace.calls[0]["error_kind"] == "contract"
    assert trace.calls[0]["questions"] == []
    assert "secret" not in json.dumps(trace.calls)


def test_nondecision_stop_does_not_blame_last_question(tiny_api: Any) -> None:
    from dataclasses import replace

    trace = TraceBackend(ChoosingBackend(choices(), weak="atom0.type"))
    result = SemanticParser(extract_schema(tiny_api), trace).parse("Return verbs.")
    report = summarize(replace(result, reason="retrieval_miss"), trace.calls)
    assert report["stopping_question"] is None
    assert report["last_observed_question"] == "atom0.type"


def test_cli_saved_tiny_tf_trace_handles_mixed_stop_outcomes(
    tmp_path: Any, monkeypatch: Any
) -> None:
    import hashlib

    from scripts import diagnose_abstention as diagnostic
    from scripts import diagnostic_probes
    from tests.test_live_evaluation import fixture
    from tf_jev import jev

    directory, benchmark = fixture(tmp_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.glob("*.tf")
                if p.is_file()
            }
        )
    )
    monkeypatch.setattr(diagnostic, "SOURCE_MANIFEST", manifest)
    monkeypatch.setattr(diagnostic, "load_benchmark", lambda: benchmark)

    class Backend(ChoosingBackend):
        def __init__(self) -> None:
            super().__init__(choices())

        def __enter__(self) -> Any:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def decide(self, request: DecisionRequest) -> DecisionBatch:
            self.weak = "shape" if "translation" in request.context["request"] else None
            return super().decide(request)

    monkeypatch.setattr(jev, "JevBackend", Backend)
    monkeypatch.setattr(diagnostic_probes, "run_probes", lambda *args: [])
    monkeypatch.setenv("TF_JEV_LIVE", "1")
    output = tmp_path / "diagnostic"
    assert (
        diagnostic.main([str(directory), "--output", str(output), "--max-cases", "2", "--live"])
        == 0
    )
    report = json.loads((output / "trace.json").read_text())
    assert report["trace_complete"] and report["complete"]
    assert len(report["cases"]) == 2
    assert report["cases"][0]["status"] == "supported"
    assert report["cases"][1]["stopping_question"] == "shape"
    assert report["stopping_questions"] == {"non_decision_stop": 1, "shape": 1}
    assert "private gold" not in json.dumps(report)


def test_cli_fails_closed_before_network_or_source_loading(tmp_path: Any, monkeypatch: Any) -> None:
    from scripts.diagnose_abstention import main

    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    output = tmp_path / "never"
    with pytest.raises(ValueError, match="TF_JEV_LIVE"):
        main([str(tmp_path / "2021"), "--output", str(output), "--max-cases", "1", "--live"])
    monkeypatch.setenv("TF_JEV_LIVE", "1")
    with pytest.raises(ValueError, match="max-cases"):
        main([str(tmp_path / "2021"), "--output", str(output), "--max-cases", "53", "--live"])
    assert not output.exists()


def test_failed_attempt_keeps_stage_and_prior_validated_question(tiny_api: Any) -> None:
    class BrokenAfterShape(ChoosingBackend):
        def decide(self, request: DecisionRequest) -> DecisionBatch:
            if "atom0.type" in request.questions:
                raise BackendError("timeout")
            return super().decide(request)

    trace = TraceBackend(BrokenAfterShape(choices()))
    result = SemanticParser(extract_schema(tiny_api), trace).parse("Return verbs.")
    report = summarize(result, trace.calls)
    assert report["last_observed_question"] == "shape"
    assert report["last_attempted_question"] == "atom0.type"
    assert report["stopping_question"] is None  # no validated decision at the failed call
    assert report["calls"][-1]["requested_questions"] == ["atom0.type"]
