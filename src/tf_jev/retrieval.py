"""Local, bounded retrieval over identity-bound schema string domains."""

from __future__ import annotations

import unicodedata
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from enum import Enum

from tf_jev.decisions import ChoiceQuestion, Option
from tf_jev.schema import ENUM_LIMIT, CorpusSchema


class RetrievalError(ValueError):
    """Invalid retrieval request or an incomplete candidate set."""


class Normalization(Enum):
    EXACT = "exact"
    NFC = "nfc"
    NFC_CASEFOLD = "nfc_casefold"


class Match(Enum):
    EXACT = "exact"
    PREFIX = "prefix"


def _key(value: str, normalization: Normalization) -> str:
    if normalization is Normalization.EXACT:
        return value
    value = unicodedata.normalize("NFC", value)
    if normalization is Normalization.NFC_CASEFOLD:
        value = unicodedata.normalize("NFC", value.casefold())
    return value


@dataclass(frozen=True)
class Candidate:
    label: str
    value: str
    count: int

    def __post_init__(self) -> None:
        if type(self.label) is not str or not self.label.isascii() or not self.label.isalnum():
            raise RetrievalError("candidate label must be a nonempty ASCII identifier")
        if type(self.value) is not str:
            raise RetrievalError("candidate value must be a str")
        if type(self.count) is not int or self.count < 1:
            raise RetrievalError("candidate count must be a positive integer")


@dataclass(frozen=True)
class RetrievalResult:
    handle: str
    candidates: tuple[Candidate, ...]
    total_matches: int

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        if type(self.handle) is not str or not self.handle:
            raise RetrievalError("result requires a source handle")
        if len(candidates) > ENUM_LIMIT or any(not isinstance(c, Candidate) for c in candidates):
            raise RetrievalError("invalid or over-budget candidate set")
        if type(self.total_matches) is not int or self.total_matches < len(candidates):
            raise RetrievalError("total_matches must be an integer at least the retained count")
        if len({c.label for c in candidates}) != len(candidates) or len(
            {c.value for c in candidates}
        ) != len(candidates):
            raise RetrievalError("candidate labels and values must be unique")
        object.__setattr__(self, "candidates", candidates)

    @property
    def truncated(self) -> bool:
        return self.total_matches > len(self.candidates)

    def _require_complete(self) -> None:
        if not self.candidates or self.truncated:
            raise RetrievalError("a complete nonempty candidate set is required")

    def as_question(self, prompt: str) -> ChoiceQuestion:
        """Explicit bounded handoff; never sends an incomplete domain to a model."""
        self._require_complete()
        return ChoiceQuestion(prompt, tuple(Option(c.label, c.value) for c in self.candidates))

    def resolve(self, label: str) -> str:
        """Recover an original corpus value only from this complete result's labels."""
        self._require_complete()
        if type(label) is str:
            for candidate in self.candidates:
                if candidate.label == label:
                    return candidate.value
        raise RetrievalError("label is not a retrieved candidate")


@dataclass(frozen=True)
class RetrievalIndex:
    handle: str
    normalization: Normalization
    _entries: tuple[tuple[str, str, int], ...] = field(repr=False)
    _keys: tuple[str, ...] = field(repr=False)

    @classmethod
    def from_schema(
        cls,
        schema: CorpusSchema,
        handle: str,
        *,
        normalization: Normalization = Normalization.EXACT,
    ) -> RetrievalIndex:
        if not isinstance(normalization, Normalization):
            raise RetrievalError("normalization must be a Normalization")
        values = schema.retrieval_values(handle)
        entries = []
        for value, count in values:
            if type(value) is not str:
                raise RetrievalError("retrieval requires a string domain")
            entries.append((_key(value, normalization), value, count))
        ordered = tuple(sorted(entries))
        return cls(handle, normalization, ordered, tuple(e[0] for e in ordered))

    def lookup(
        self, text: str, *, match: Match = Match.EXACT, limit: int = ENUM_LIMIT
    ) -> RetrievalResult:
        if type(text) is not str:
            raise RetrievalError("lookup text must be a str")
        if not isinstance(match, Match):
            raise RetrievalError("match must be a Match")
        if type(limit) is not int or not 1 <= limit <= ENUM_LIMIT:
            raise RetrievalError(f"limit must be an integer in [1, {ENUM_LIMIT}]")
        key = _key(text, self.normalization)
        if match is Match.PREFIX and not key:
            raise RetrievalError("prefix lookup requires a nonempty key")
        start = bisect_left(self._keys, key)
        if match is Match.EXACT:
            end = bisect_right(self._keys, key)
        else:
            end = start
            while end < len(self._keys) and self._keys[end].startswith(key):
                end += 1
        candidates = tuple(
            Candidate(f"c{i:04}", value, count)
            for i, (_, value, count) in enumerate(self._entries[start : min(end, start + limit)])
        )
        return RetrievalResult(self.handle, candidates, end - start)
