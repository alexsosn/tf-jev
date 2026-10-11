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
import numbers
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Protocol, TypeVar, runtime_checkable

# Absolute slack for float arithmetic when checking probability sums.
_EPS = 1e-6

# Unicode categories that are invisible, reorder text, or separate lines:
# controls, format (zero-width, bidi), line/paragraph separators, surrogates,
# private use and unassigned code points.
_FORBIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp", "Cs", "Co", "Cn"})

# Prose (user requests, descriptions, prompts) may contain what real pasted text
# contains: tab, LF, CR, and the joiners/marks used by RTL and Indic scripts
# (ZWNJ, ZWJ, LRM, RLM). Bidi embeddings, overrides and isolates stay forbidden.
_PROSE_ALLOWED = frozenset("\t\n\r\u200c\u200d\u200e\u200f")

K = TypeVar("K")
V = TypeVar("V")


class _FrozenMap(Mapping[K, V]):
    """Read-only mapping that, unlike ``MappingProxyType``, pickles and deep-copies."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[K, V]) -> None:
        self._data = dict(data)

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._data!r})"

    def __reduce__(self) -> tuple[type[_FrozenMap[K, V]], tuple[dict[K, V]]]:
        return (type(self), (self._data,))


class DecisionContractError(ValueError):
    """A question, request or backend answer violates the decision contract."""


class BackendError(RuntimeError):
    """Sanitized backend failure, without server messages or credential-bearing objects."""

    def __init__(self, kind: str, status: int | None = None) -> None:
        self.kind = kind
        self.status = status
        super().__init__(f"backend failure: {kind}" + (f" (HTTP {status})" if status else ""))


def _check_symbol(value: object, what: str) -> str:
    """Strict check for labels and ids: visible, NFC, no invisible or bidi characters."""
    if type(value) is not str:
        raise DecisionContractError(f"{what} must be a str, got {type(value).__name__}")
    for ch in value:
        category = unicodedata.category(ch)
        if category in _FORBIDDEN_CATEGORIES or (category == "Zs" and ch != " "):
            raise DecisionContractError(f"{what} contains forbidden character {ch!r}: {value!r}")
    if not any(not unicodedata.category(ch).startswith("Z") for ch in value):
        raise DecisionContractError(f"{what} must contain a visible character: {value!r}")
    if unicodedata.normalize("NFC", value) != value:
        raise DecisionContractError(f"{what} must be in Unicode NFC form: {value!r}")
    return value


def _check_prose(value: object, what: str, *, visible: bool = False) -> str:
    """Lenient check for free text sent to a backend (see ``_PROSE_ALLOWED``).

    Prose is passed on byte-for-byte; it is never normalized.
    """
    if type(value) is not str:
        raise DecisionContractError(f"{what} must be a str, got {type(value).__name__}")
    for ch in value:
        if ch in _PROSE_ALLOWED:
            continue
        if unicodedata.category(ch) in _FORBIDDEN_CATEGORIES:
            raise DecisionContractError(f"{what} contains forbidden character {ch!r}")
    if visible and not any(not unicodedata.category(ch).startswith(("Z", "C")) for ch in value):
        raise DecisionContractError(f"{what} must contain a visible character")
    return value


def _check_resolution(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise DecisionContractError("probability resolution must be a real number")
    number = float(value)
    if not (math.isfinite(number) and 0.0 <= number < 1.0):
        raise DecisionContractError(f"probability resolution {value} must be in [0, 1)")
    return number


def _check_probability(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise DecisionContractError(f"{where}: probability must be a real number")
    try:
        number = float(value)
    except OverflowError as error:
        raise DecisionContractError(f"{where}: probability is not finite") from error
    if not math.isfinite(number):
        raise DecisionContractError(f"{where}: probability must be a finite number")
    if not 0.0 <= number <= 1.0:
        raise DecisionContractError(f"{where}: probability {number} outside [0, 1]")
    return number


# --- questions --------------------------------------------------------------


@dataclass(frozen=True)
class Option:
    """One selectable option.

    ``label`` is an opaque tf-jev id, never a corpus value: corpus values may be
    non-NFC (BHSA ``voc_lex_utf8``, ``g_word_utf8``) and must reach the compiler
    byte-for-byte, so they belong in ``description`` and in the caller's own
    id → value table, and are never normalized.
    """

    label: str
    description: str | None = None

    def __post_init__(self) -> None:
        _check_symbol(self.label, "option label")
        if self.description is not None:
            _check_prose(self.description, "option description")


@dataclass(frozen=True)
class ChoiceQuestion:
    prompt: str
    options: tuple[Option, ...]

    def __post_init__(self) -> None:
        _check_prose(self.prompt, "question prompt", visible=True)
        object.__setattr__(self, "options", tuple(self.options))
        if not self.options:
            raise DecisionContractError("a choice needs at least one option")
        seen: set[str] = set()
        for option in self.options:
            if not isinstance(option, Option):
                raise DecisionContractError("choice options must be Option instances")
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
        _check_prose(self.prompt, "question prompt", visible=True)


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
        context = {
            _check_symbol(key, "context key"): _check_prose(value, f"context value {key!r}")
            for (key, value) in self.context.items()
        }
        questions = {}
        for name, question in self.questions.items():
            _check_symbol(name, "question id")
            if not isinstance(question, ChoiceQuestion | BinaryQuestion):
                raise DecisionContractError(f"{name}: not a question: {type(question).__name__}")
            questions[name] = question
        if not questions:
            raise DecisionContractError("a request needs at least one question")
        # Copy into read-only views so later mutation of the caller's dicts
        # cannot change a request that has already been checked.
        object.__setattr__(self, "context", _FrozenMap(context))
        object.__setattr__(self, "questions", _FrozenMap(questions))


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
    """A selected option with its distribution.

    Construction enforces the whole answer invariant, so a hand-built decision is
    held to the same rules as a validated backend answer: plain-str labels,
    probabilities in [0, 1], sums explainable by ``resolution`` rounding, and a
    selected option of highest probability.
    """

    selected: str
    probabilities: Mapping[str, float]
    resolution: float = 0.0

    def __post_init__(self) -> None:
        resolution = _check_resolution(self.resolution)
        probabilities = {
            _check_symbol(label, "option label"): _check_probability(value, label)
            for (label, value) in self.probabilities.items()
        }
        if type(self.selected) is not str or self.selected not in probabilities:
            raise DecisionContractError(f"selected {self.selected!r} has no probability")
        _check_sums(probabilities.values(), resolution)
        if probabilities[self.selected] < max(probabilities.values()):
            raise DecisionContractError("selected option is not a highest-probability one")
        object.__setattr__(self, "resolution", resolution)
        object.__setattr__(self, "probabilities", _FrozenMap(probabilities))

    @property
    def top_probability(self) -> float:
        return self.probabilities[self.selected]

    @property
    def margin(self) -> float:
        """Selected probability minus the best other option (1.0 for a single option)."""
        others = [p for (label, p) in self.probabilities.items() if label != self.selected]
        return self.top_probability - max(others, default=0.0)

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

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", _check_probability(self.probability, "binary"))

    @property
    def confidence(self) -> float:
        """Distance from 0.5, scaled to [0, 1] (the two-option choice formula)."""
        return abs(2.0 * self.probability - 1.0)


Decision = ChoiceDecision | BinaryDecision


def validate_answers(
    request: DecisionRequest, answers: Mapping[str, RawAnswer], resolution: float = 0.0
) -> dict[str, Decision]:
    """Turn raw backend answers into typed decisions or fail loudly.

    ``resolution`` is the rounding step of the backend's reported probabilities
    (0.01 for Jev 1.13, 0.0 for exact backends). Each reported value may then be
    off by at most ``resolution / 2``, which bounds every partial sum.
    """
    resolution = _check_resolution(resolution)
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
            decisions[name] = _validate_choice(name, question, answer, resolution)
        elif isinstance(question, BinaryQuestion):
            if not isinstance(answer, RawBinary):
                raise DecisionContractError(f"{name}: expected a binary answer")
            decisions[name] = BinaryDecision(_check_probability(answer.probability, name))
        else:  # pragma: no cover - DecisionRequest only admits the two kinds
            raise DecisionContractError(f"{name}: unsupported question kind")
    return decisions


def _validate_choice(
    name: str, question: ChoiceQuestion, answer: RawChoice, resolution: float
) -> ChoiceDecision:
    labels = question.labels
    if type(answer.selected) is not str or answer.selected not in labels:
        raise DecisionContractError(
            f"{name}: selected {answer.selected!r} is not a requested option"
        )
    if any(type(key) is not str for key in answer.probabilities) or set(
        answer.probabilities
    ) != set(labels):
        raise DecisionContractError(f"{name}: probabilities do not cover exactly the options")
    values = {
        label: _check_probability(answer.probabilities[label], f"{name}[{label}]")
        for label in labels
    }
    selected = labels[labels.index(answer.selected)]
    try:
        # Request order, and the requested label objects, never the backend's.
        return ChoiceDecision(selected=selected, probabilities=values, resolution=resolution)
    except DecisionContractError as error:
        raise DecisionContractError(f"{name}: {error}") from error


def _check_sums(values: Iterable[float], resolution: float) -> None:
    """Reject distributions that rounding to ``resolution`` cannot explain.

    Rounding moves each value by at most resolution/2, so the k largest values
    can exceed 1 by at most k * resolution/2, and the full sum can fall short of
    1 by at most n * resolution/2.
    """
    half_step = resolution / 2
    partial = 0.0
    ranked = sorted(values, reverse=True)
    for k, value in enumerate(ranked, start=1):
        partial += value
        if partial > 1.0 + k * half_step + _EPS:
            raise DecisionContractError(
                f"top-{k} probabilities sum to {partial:.4f}, more than rounding allows"
            )
    if partial < 1.0 - len(ranked) * half_step - _EPS:
        raise DecisionContractError(f"probabilities sum to {partial:.4f}, not 1")


# --- backends ----------------------------------------------------------------


@dataclass(frozen=True)
class Capabilities:
    """Hard request limits a backend accepts; checked before any call."""

    max_options: int | None = None
    max_questions: int | None = None
    probability_resolution: float = 0.0
    """Rounding step of reported probabilities in [0, 1); 0.0 means exact."""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "probability_resolution", _check_resolution(self.probability_resolution)
        )


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
    probability_resolution: float = 0.0
    requests: list[DecisionRequest] = field(default_factory=list)

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            max_options=self.max_options,
            max_questions=self.max_questions,
            probability_resolution=self.probability_resolution,
        )

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        check_capabilities(request, self.capabilities)
        self.requests.append(request)
        raw = {name: self.answers[name] for name in request.questions if name in self.answers}
        return DecisionBatch(
            decisions=validate_answers(request, raw, self.probability_resolution),
            receipt=Receipt(backend="scripted", model="scripted"),
        )
