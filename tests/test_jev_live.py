"""Explicit opt-in synthetic Jev contract smoke; never sends corpus text."""

from __future__ import annotations

import os

import pytest


def test_live_jev_contract() -> None:
    if os.environ.get("TF_JEV_LIVE") != "1":
        pytest.skip("set TF_JEV_LIVE=1 and JEV_API_KEY or TYPESAFE_API_KEY to opt in")
    pytest.importorskip("typesafe_sdk")
    from tf_jev.decisions import (
        BinaryQuestion,
        ChoiceDecision,
        ChoiceQuestion,
        DecisionRequest,
        Option,
    )
    from tf_jev.jev import DEFAULT_MODEL, JevBackend

    request = DecisionRequest(
        {"text": "The square is red."},
        {
            "colour": ChoiceQuestion(
                "Which colour is explicitly stated?", (Option("c0", "red"), Option("c1", "blue"))
            ),
            "stated": BinaryQuestion("Does the text explicitly name a colour?"),
        },
    )
    with JevBackend() as adapter:
        result = adapter.decide(request)
    assert isinstance(result.decisions["colour"], ChoiceDecision)
    assert result.decisions["colour"].selected in request.questions["colour"].labels  # type: ignore[union-attr]
    assert result.receipt.model == DEFAULT_MODEL
    assert result.receipt.latency_s > 0
    assert result.receipt.input_tokens is None or result.receipt.input_tokens > 0
