"""Metering counts failed attempts even when SemanticParser drops receipts."""

from typing import Any

import pytest

from scripts.measure_comparison import MeteredBackend
from tf_jev.decisions import BackendError, Capabilities, ChoiceQuestion, DecisionRequest, Option


def test_meter_does_not_hide_failed_network_attempts() -> None:
    class Broken:
        capabilities = Capabilities()

        def decide(self, request: Any) -> Any:
            raise BackendError("authentication", 401)

    meter = MeteredBackend(Broken())
    with pytest.raises(BackendError):
        meter.decide(
            DecisionRequest(
                {"request": "secret"}, {"q": ChoiceQuestion("choose", (Option("one"),))}
            )
        )
    assert len(meter.attempts) == 1
    assert meter.attempts[0]["error_kind"] == "authentication"
    assert meter.attempts[0]["input_tokens"] is None
    assert "secret" not in str(meter.attempts)


def test_cli_refuses_network_without_double_opt_in(monkeypatch: Any, tmp_path: Any) -> None:
    from scripts.measure_comparison import main

    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    with pytest.raises(ValueError, match="TF_JEV_LIVE=1"):
        main(
            [
                str(tmp_path / "2021"),
                "--output",
                str(tmp_path / "out"),
                "--private-review",
                str(tmp_path / "review"),
                "--live",
            ]
        )
    assert not (tmp_path / "out").exists()
