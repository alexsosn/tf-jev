"""Backend-neutral bounded-decision contract.

A decision backend answers *bounded* questions only: a choice among option labels
that tf-jev itself supplied, or a yes/no probability. Every backend response passes
through :func:`validate_answers`, so a selected label is always one of the labels
in the request. Nothing a backend returns can become free text, let alone query
syntax.

See docs/research/jev-decision-backend.md for the research behind this contract.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# Jev 1.13 returns probabilities rounded to two decimals, so a sum may drift by up
# to 0.005 per option. The tolerance is absolute and deliberately loose for small
# option sets; anything further off is a malformed response.
_SUM_TOLERANCE_PER_OPTION = 0.005
_MIN_SUM_TOLERANCE = 0.02


class DecisionContractError(ValueError):
    """A question, request or backend answer violates the decision contract."""


def _check_text(value: str, what: str) -> None:
    if not value.strip():
        raise DecisionContractError(f"{what} must be non-empty")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise DecisionContractError(f"{what} must not contain control characters: {value!r}")


def _check_probability(value: float, where: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise DecisionContractError(f"{where}: probability must be a finite number")
    if not 0.0 <= value <= 1.0:
        raise DecisionContractError(f"{where}: probability {value} outside [0, 1]")


# --- questions --------------------------------------------------------------


@dataclass(frozen=True)
class Option:
    """One selectable option. ``label`` is an opaque id chosen by tf-jev."""

    label: str
    description: str | None = None

    def __post_init__(self) -> None:
        _check_text(self.label, "option label")


@dataclass(frozen=True)
class ChoiceQuestion:
    prompt: str
    options: tuple[Option, ...]

    def __post_init__(self) -> None:
        _check_text(self.prompt, "question prompt")
        if not self.options:
            raise DecisionContractError("a choice needs at least one option")
        seen: set[str] = set()
        for option in self.options:
            if option.label in seen:
                raise DecisionContractError(f"duplicate option label: {option.label!r}")
            seen.add(option.label)

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(option.label for option in self.options)


@dataclass(frozen=True)
class BinaryQuestion:
    prompt: str

    def __post_init__(self) -> None:
        _check_text(self.prompt, "question prompt")


Question = ChoiceQuestion | BinaryQuestion


@dataclass(frozen=True)
class DecisionRequest:
    """Questions evaluated against one shared context.

    ``context`` is the only free text a backend sees besides prompts and option
    descriptions; callers decide what goes in it (see the data-flow notes in the
    research document).
    """

    context: Mapping[str, str]
    questions: Mapping[str, Question]

    def __post_init__(self) -> None:
        if not self.questions:
            raise DecisionContractError("a request needs at least one question")
        for name in self.questions:
            _check_text(name, "question id")


# --- raw answers (what a backend adapter produces) ---------------------------


@dataclass(frozen=True)
class RawChoice:
    selected: str
    probabilities: Mapping[str, float]


@dataclass(frozen=True)
class RawBinary:
    probability: float


RawAnswer = RawChoice | RawBinary


# --- validated decisions -----------------------------------------------------


@dataclass(frozen=True)
class ChoiceDecision:
    selected: str
    probabilities: Mapping[str, float]

    @property
    def top_probability(self) -> float:
        return self.probabilities[self.selected]

    @property
    def margin(self) -> float:
        """Top probability minus the runner-up (1.0 for a single option)."""
        ranked = sorted(self.probabilities.values(), reverse=True)
        return ranked[0] - (ranked[1] if len(ranked) > 1 else 0.0)

    @property
    def confidence(self) -> float:
        """Distance of the top probability above an even split, in [0, 1].

        Same formula Jev documents for Choice confidence, computed locally so every
        backend is judged on one scale.
        """
        n = len(self.probabilities)
        if n == 1:
            return 1.0
        uniform = 1.0 / n
        return max(0.0, (self.top_probability - uniform) / (1.0 - uniform))


@dataclass(frozen=True)
class BinaryDecision:
    probability: float

    @property
    def confidence(self) -> float:
        """Distance from 0.5, scaled to [0, 1] (the two-option choice formula)."""
        return abs(2.0 * self.probability - 1.0)


Decision = ChoiceDecision | BinaryDecision


def validate_answers(
    request: DecisionRequest, answers: Mapping[str, RawAnswer]
) -> dict[str, Decision]:
    """Turn raw backend answers into typed decisions or fail loudly."""
    missing = sorted(set(request.questions) - set(answers))
    if missing:
        raise DecisionContractError(f"missing answer(s): {', '.join(missing)}")
    extra = sorted(set(answers) - set(request.questions))
    if extra:
        raise DecisionContractError(f"unrequested answer(s): {', '.join(extra)}")

    decisions: dict[str, Decision] = {}
    for name, question in request.questions.items():
        answer = answers[name]
        if isinstance(question, ChoiceQuestion):
            if not isinstance(answer, RawChoice):
                raise DecisionContractError(f"{name}: expected a choice answer")
            decisions[name] = _validate_choice(name, question, answer)
        else:
            if not isinstance(answer, RawBinary):
                raise DecisionContractError(f"{name}: expected a binary answer")
            _check_probability(answer.probability, name)
            decisions[name] = BinaryDecision(probability=float(answer.probability))
    return decisions


def _validate_choice(name: str, question: ChoiceQuestion, answer: RawChoice) -> ChoiceDecision:
    labels = question.labels
    if answer.selected not in labels:
        raise DecisionContractError(f"{name}: {answer.selected!r} is not a requested option")
    if set(answer.probabilities) != set(labels):
        raise DecisionContractError(f"{name}: probabilities do not cover exactly the options")
    for label, value in answer.probabilities.items():
        _check_probability(value, f"{name}[{label}]")
    total = sum(answer.probabilities.values())
    tolerance = max(_MIN_SUM_TOLERANCE, _SUM_TOLERANCE_PER_OPTION * len(labels))
    if abs(total - 1.0) > tolerance:
        raise DecisionContractError(f"{name}: probabilities sum to {total:.4f}, not 1")
    if answer.probabilities[answer.selected] < max(answer.probabilities.values()):
        raise DecisionContractError(f"{name}: selected option is not a highest-probability one")
    # Keep request order so downstream code never depends on backend dict order.
    ordered = {label: float(answer.probabilities[label]) for label in labels}
    return ChoiceDecision(selected=answer.selected, probabilities=ordered)


# --- backends ----------------------------------------------------------------


@dataclass(frozen=True)
class Capabilities:
    """Hard request limits a backend accepts; checked before any call."""

    max_options: int | None = None
    max_questions: int | None = None


@dataclass(frozen=True)
class Receipt:
    """Per-call accounting. Never carries credentials, context or prompts."""

    backend: str
    model: str
    latency_s: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class DecisionBatch:
    decisions: Mapping[str, Decision]
    receipt: Receipt


def check_capabilities(request: DecisionRequest, capabilities: Capabilities) -> None:
    limit = capabilities.max_questions
    if limit is not None and len(request.questions) > limit:
        raise DecisionContractError(f"backend accepts at most {limit} questions per request")
    limit = capabilities.max_options
    if limit is not None:
        for name, question in request.questions.items():
            if isinstance(question, ChoiceQuestion) and len(question.options) > limit:
                raise DecisionContractError(f"{name}: backend accepts at most {limit} options")


@runtime_checkable
class DecisionBackend(Protocol):
    @property
    def capabilities(self) -> Capabilities: ...

    def decide(self, request: DecisionRequest) -> DecisionBatch: ...


@dataclass
class ScriptedBackend:
    """Deterministic backend for TDD: replays fixed raw answers by question id.

    It goes through the same capability check and answer validation as a real
    backend, so tests exercise the production boundary.
    """

    answers: Mapping[str, RawAnswer]
    max_options: int | None = None
    max_questions: int | None = None
    requests: list[DecisionRequest] = field(default_factory=list)

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(max_options=self.max_options, max_questions=self.max_questions)

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        check_capabilities(request, self.capabilities)
        self.requests.append(request)
        raw = {name: self.answers[name] for name in request.questions if name in self.answers}
        return DecisionBatch(
            decisions=validate_answers(request, raw),
            receipt=Receipt(backend="scripted", model="scripted"),
        )
