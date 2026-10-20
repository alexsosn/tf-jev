"""Fixed experiment selection, source/opt-in gates and accounting."""

from typing import Any

import pytest

from scripts.grounded_experiment import POLICIES, main, select_policy


def report(success: int, emitted: int, unsafe: int = 0) -> dict[str, Any]:
    return dict(
        result_equivalent=success,
        status_counts={"supported": emitted},
        unsafe_supported_on_negative=unsafe,
    )


def test_policy_selection_refuses_wrong_emissions_and_prefers_strict_ties() -> None:
    assert (
        select_policy(
            {"strict": report(1, 1), "exploratory": report(2, 3), "guarded": report(2, 2)}
        )
        == "guarded"
    )
    assert select_policy({k: report(1, 1) for k in POLICIES}) == "strict"
    assert select_policy({k: report(0, 1, 1) for k in POLICIES}) == "strict"


def test_live_and_existing_output_gates_precede_corpus(tmp_path: Any, monkeypatch: Any) -> None:
    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    argv = [
        str(tmp_path),
        "--output",
        str(tmp_path / "new"),
        "--private-review",
        str(tmp_path / "private"),
        "--phase",
        "calibration",
        "--live",
    ]
    with pytest.raises(ValueError, match="opt-in"):
        main(argv)
    monkeypatch.setenv("TF_JEV_LIVE", "1")
    argv[2] = str(tmp_path)
    with pytest.raises(ValueError, match="new"):
        main(argv)


def test_stages_preserve_proxy_and_failed_call_accounting() -> None:
    from scripts.grounded_experiment import StageMeter
    from tests.test_grounded_parser import PlanBackend
    from tf_jev.decisions import (
        BackendError,
        ChoiceQuestion,
        DecisionRequest,
        Option,
    )

    backend = PlanBackend({"shape": "atom"})
    meter = StageMeter(backend)
    request = DecisionRequest(
        {"private": "secret-context"},
        {"shape": ChoiceQuestion("private prose", (Option("o0", "atom"), Option("o1", "other")))},
    )
    result = meter.decide(request)
    assert result.receipt.input_tokens == 11
    assert backend.requests == [request]
    assert meter.attempts[0]["stages"] == ["shape"]

    assert "private" not in str(meter.attempts)

    class Failure(PlanBackend):
        def decide(self, request: Any) -> Any:
            raise BackendError("timeout")

    meter = StageMeter(Failure({}))
    with pytest.raises(BackendError):
        meter.decide(request)
    assert meter.attempts[0]["input_tokens"] is None
    assert meter.attempts[0]["stages"] == ["shape"]


def test_failed_usage_never_becomes_zero_cost() -> None:
    from types import SimpleNamespace

    from scripts.grounded_experiment import account
    from scripts.measure_comparison import RecordingParser

    data: dict[str, Any] = {"cases": [{}]}
    parser = RecordingParser(SimpleNamespace(schema=None), None)
    parser.attempts = [
        [dict(input_tokens=None, output_tokens=None, error_kind="timeout", stages=["shape"])]
    ]
    account(data, parser)
    assert data["estimated_cost_usd"] is None
    assert data["estimated_cost_usd_complete"] is False
    assert data["cases"][0]["input_tokens"] is None


def test_frozen_calibration_and_fresh_evaluation_remain_honest() -> None:
    import hashlib
    import json
    from pathlib import Path

    from scripts.grounded_experiment import BENCHMARK, DIGEST

    root = Path(__file__).resolve().parents[1] / "reports/grounded-parser-2026-10-20"
    assert hashlib.sha256(BENCHMARK.read_bytes()).hexdigest() == DIGEST
    freeze = json.loads((root / "calibration-freeze.json").read_text())
    reports = {
        name: json.loads((root / "calibration" / (name + ".json")).read_text()) for name in POLICIES
    }
    assert select_policy(reports) == freeze["selected_policy"] == "strict"
    for name, digest in freeze["artifacts_sha256"].items():
        assert hashlib.sha256((root / "calibration" / name).read_bytes()).hexdigest() == digest
    evaluation = json.loads((root / "evaluation/strict.json").read_text())
    assert evaluation["total"] == 21 and evaluation["supported_gold"] == 12
    assert evaluation["result_equivalent"] == 0 and evaluation["safe_negative"] == 9
    assert evaluation["emitted_query_native_valid_rate"] is None
    assert sum(r["attempted_backend_calls"] for r in evaluation["cases"]) == 52
    assert sum(r["input_tokens"] for r in evaluation["cases"]) == 457086
    assert all(r["dataset"] == "grounded-v1" for r in reports.values())
