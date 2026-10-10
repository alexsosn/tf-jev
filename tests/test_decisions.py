from __future__ import annotations

import math

import pytest

from tf_jev.decisions import (
    BinaryDecision,
    BinaryQuestion,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBackend,
    DecisionContractError,
    DecisionRequest,
    Option,
    RawAnswer,
    RawBinary,
    RawChoice,
    ScriptedBackend,
    validate_answers,
)


def gender() -> ChoiceQuestion:
    return ChoiceQuestion(
        prompt="Which grammatical gender is required?",
        options=(Option("m", "masculine"), Option("f", "feminine"), Option("none", None)),
    )


def request() -> DecisionRequest:
    return DecisionRequest(
        context={"request": "feminine plural verbs"},
        questions={"gn": gender(), "neg": BinaryQuestion(prompt="Is something excluded?")},
    )


# --- question construction -------------------------------------------------


def test_choice_requires_at_least_one_option() -> None:
    with pytest.raises(DecisionContractError, match="at least one option"):
        ChoiceQuestion(prompt="?", options=())


def test_choice_rejects_duplicate_labels() -> None:
    with pytest.raises(DecisionContractError, match="duplicate option label"):
        ChoiceQuestion(prompt="?", options=(Option("a", None), Option("a", "again")))


@pytest.mark.parametrize("label", ["", " ", "a\nb", "\x00"])
def test_option_rejects_empty_or_control_labels(label: str) -> None:
    with pytest.raises(DecisionContractError, match="option label"):
        Option(label, None)


def test_request_requires_questions() -> None:
    with pytest.raises(DecisionContractError, match="at least one question"):
        DecisionRequest(context={"request": "x"}, questions={})


# --- response validation: the boundary that keeps model output bounded -----


def test_valid_answers_become_typed_decisions() -> None:
    decisions = validate_answers(
        request(),
        {
            "gn": RawChoice(selected="f", probabilities={"m": 0.0, "f": 0.98, "none": 0.02}),
            "neg": RawBinary(probability=0.1),
        },
    )

    gn = decisions["gn"]
    assert isinstance(gn, ChoiceDecision)
    assert gn.selected == "f"
    assert gn.top_probability == 0.98
    assert gn.margin == pytest.approx(0.96)
    assert gn.confidence == pytest.approx((0.98 - 1 / 3) / (1 - 1 / 3))
    neg = decisions["neg"]
    assert isinstance(neg, BinaryDecision)
    assert neg.probability == 0.1


def test_selected_label_outside_request_is_rejected() -> None:
    with pytest.raises(DecisionContractError, match="not a requested option"):
        validate_answers(
            request(),
            {
                "gn": RawChoice(selected="word sp=verb", probabilities={"m": 0.0, "f": 0.0}),
                "neg": RawBinary(probability=0.1),
            },
        )


def test_probability_labels_must_match_requested_options() -> None:
    with pytest.raises(DecisionContractError, match="probabilities"):
        validate_answers(
            request(),
            {
                "gn": RawChoice(selected="f", probabilities={"f": 1.0, "extra": 0.0}),
                "neg": RawBinary(probability=0.1),
            },
        )


def test_missing_answer_is_rejected() -> None:
    with pytest.raises(DecisionContractError, match="missing answer"):
        validate_answers(request(), {"gn": RawChoice("f", {"m": 0.0, "f": 1.0, "none": 0.0})})


def test_unrequested_answer_is_rejected() -> None:
    answers: dict[str, RawAnswer] = {
        "gn": RawChoice("f", {"m": 0.0, "f": 1.0, "none": 0.0}),
        "neg": RawBinary(0.1),
        "extra": RawBinary(0.5),
    }
    with pytest.raises(DecisionContractError, match="unrequested answer"):
        validate_answers(request(), answers)


def test_answer_kind_must_match_question_kind() -> None:
    with pytest.raises(DecisionContractError, match="expected a choice"):
        validate_answers(request(), {"gn": RawBinary(0.9), "neg": RawBinary(0.1)})


@pytest.mark.parametrize("bad", [-0.01, 1.01, math.nan, math.inf])
def test_probabilities_must_be_finite_unit_interval(bad: float) -> None:
    with pytest.raises(DecisionContractError, match="probability"):
        validate_answers(
            request(),
            {"gn": RawChoice("f", {"m": 0.0, "f": 1.0, "none": 0.0}), "neg": RawBinary(bad)},
        )


def test_choice_probabilities_must_sum_to_one_within_rounding() -> None:
    with pytest.raises(DecisionContractError, match="sum"):
        validate_answers(
            request(),
            {"gn": RawChoice("f", {"m": 0.3, "f": 0.3, "none": 0.0}), "neg": RawBinary(0.1)},
        )


def test_two_decimal_rounding_drift_is_tolerated() -> None:
    decisions = validate_answers(
        request(),
        {"gn": RawChoice("f", {"m": 0.33, "f": 0.34, "none": 0.34}), "neg": RawBinary(0.1)},
    )

    assert isinstance(decisions["gn"], ChoiceDecision)


def test_selected_must_be_a_highest_probability_option() -> None:
    with pytest.raises(DecisionContractError, match="highest"):
        validate_answers(
            request(),
            {"gn": RawChoice("m", {"m": 0.1, "f": 0.9, "none": 0.0}), "neg": RawBinary(0.1)},
        )


def test_single_option_choice_has_full_confidence() -> None:
    question = ChoiceQuestion(prompt="?", options=(Option("only", None),))
    req = DecisionRequest(context={"request": "x"}, questions={"q": question})

    decision = validate_answers(req, {"q": RawChoice("only", {"only": 1.0})})["q"]

    assert isinstance(decision, ChoiceDecision)
    assert decision.confidence == 1.0
    assert decision.margin == 1.0


# --- deterministic fake backend ---------------------------------------------


def test_scripted_backend_is_a_decision_backend_and_validates() -> None:
    backend = ScriptedBackend(
        {
            "gn": RawChoice("f", {"m": 0.0, "f": 1.0, "none": 0.0}),
            "neg": RawBinary(0.05),
        }
    )
    assert isinstance(backend, DecisionBackend)

    batch = backend.decide(request())

    assert batch.receipt.backend == "scripted"
    assert batch.receipt.model == "scripted"
    assert set(batch.decisions) == {"gn", "neg"}
    assert backend.requests == [request()]


def test_scripted_backend_cannot_smuggle_unrequested_labels() -> None:
    backend = ScriptedBackend({"gn": RawChoice("clause", {"clause": 1.0}), "neg": RawBinary(0.05)})

    with pytest.raises(DecisionContractError):
        backend.decide(request())


def test_capabilities_are_enforced_before_calling_backend() -> None:
    wide = ChoiceQuestion(prompt="?", options=tuple(Option(f"o{i}", None) for i in range(4)))
    backend = ScriptedBackend({}, max_options=3)

    with pytest.raises(DecisionContractError, match="at most 3 options"):
        backend.decide(DecisionRequest(context={"request": "x"}, questions={"q": wide}))
    assert backend.requests == []
