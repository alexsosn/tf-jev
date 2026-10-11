"""Guided, schema-bound natural-language to single-atom QueryIR orchestration.

A small first vertical slice of issue #9. No generic relation/quantifier parser,
no raw grammar strings from the backend, no semantic accuracy claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from tf_jev.compiler import CompileError, compile_query
from tf_jev.decisions import (
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBackend,
    DecisionContractError,
    DecisionRequest,
    Option,
    RawChoice,
    check_capabilities,
    validate_answers,
)
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.retrieval import Match, RetrievalError, RetrievalIndex
from tf_jev.schema import CorpusSchema, Enumerated, Large, SchemaError

ParseStatus = Literal["ok", "ambiguous", "unsupported", "low_confidence"]


@dataclass(frozen=True)
class ChoiceEvidence:
    """Opaque selections; original corpus values remain in local QueryIR only."""

    question: str
    selected: str
    confidence: float


@dataclass(frozen=True)
class ParseResult:
    status: ParseStatus
    query: Query | None
    native_query: str | None
    confidence: float
    evidence: tuple[ChoiceEvidence, ...]


def parse_one_atom(
    text: str,
    schema: CorpusSchema,
    backend: DecisionBackend,
    *,
    feature_candidates: tuple[str, ...] = (),
    value_hint: str | None = None,
    min_confidence: float = 0.8,
) -> ParseResult:
    """Choose one corpus-bound object, optionally with one equality predicate.

    Caller-supplied feature_candidates are *only a shortlist*, validated against
    the given schema. High-cardinality feature values are retrieved by exact
    value_hint, not extracted or invented by the backend. No structural request
    can be expressed unless the backend wrongly classifies it as single-node:
    generic natural-language intent accuracy is explicitly outside this slice.
    """
    if type(min_confidence) not in (int, float) or not (
        math.isfinite(min_confidence) and 0.0 <= min_confidence <= 1.0
    ):
        raise ValueError("confidence threshold must be finite and in [0, 1]")
    if type(feature_candidates) is not tuple or any(
        type(feature) is not str for feature in feature_candidates
    ):
        raise ValueError("feature shortlist must be a tuple of schema feature names")
    if len(set(feature_candidates)) != len(feature_candidates):
        raise ValueError("feature shortlist contains duplicates")
    if any(feature not in {f.name for f in schema.node_features} for feature in feature_candidates):
        raise ValueError("feature shortlist contains an unknown node feature")
    if value_hint is not None and type(value_hint) is not str:
        raise ValueError("value hint must be exact text")
    if not isinstance(schema, CorpusSchema):
        raise ValueError("a trusted CorpusSchema is required")
    evidence: list[ChoiceEvidence] = []

    def finished(
        status: ParseStatus, query: Query | None = None, native: str | None = None
    ) -> ParseResult:
        return ParseResult(
            status, query, native,
            min((entry.confidence for entry in evidence), default=0.0),
            tuple(evidence),
        )

    def choose(question_id: str, prompt: str, options: tuple[Option, ...]) -> str | None:
        # Never silently truncate schema choices to fit a backend/model limit.
        if (
            backend.capabilities.max_options is not None
            and len(options) > backend.capabilities.max_options
        ):
            return None
        request = DecisionRequest(
            {"request": text},
            {question_id: ChoiceQuestion(prompt, options)},
        )
        check_capabilities(request, backend.capabilities)
        batch = backend.decide(request)
        if set(batch.decisions) != {question_id}:
            raise DecisionContractError("backend returned missing or extra decisions")
        original = batch.decisions[question_id]
        if type(original) is not ChoiceDecision:
            raise DecisionContractError("backend returned a non-choice decision")
        checked = validate_answers(
            request,
            {question_id: RawChoice(original.selected, original.probabilities)},
            backend.capabilities.probability_resolution,
        )[question_id]
        assert isinstance(checked, ChoiceDecision)
        evidence.append(ChoiceEvidence(question_id, checked.selected, checked.confidence))
        return checked.selected

    mode = choose(
        "mode",
        "Classify the request: exactly one node type with at most one equality feature, "
        "or ambiguous/unsupported relations, counting, ranking, and quantifiers.",
        (
            Option("single", "Exactly one node type, optionally one feature equality"),
            Option("ambiguous", "Multiple defensible interpretations, abstain"),
            Option("unsupported", "Any relation, computation or unsupported meaning, abstain"),
        ),
    )
    if mode is None:
        return finished("unsupported")
    if evidence[-1].confidence < min_confidence:
        return finished("low_confidence")
    if mode != "single":
        return finished("ambiguous" if mode == "ambiguous" else "unsupported")

    node_types = tuple(t.name for t in schema.object_type_details if t.expressible)
    if not node_types:
        return finished("unsupported")
    selected_type = choose(
        "type",
        "Choose the corpus object type the user requests, or abstain via mode.",
        tuple(Option(f"t{i:03}", name) for i, name in enumerate(node_types)),
    )
    if selected_type is None:
        return finished("unsupported")
    if evidence[-1].confidence < min_confidence:
        return finished("low_confidence")
    object_type = node_types[int(selected_type[1:])]

    # Only user-supplied, schema-verified features are available; a full corpus
    # inventory is never partly shown and then mistaken for an exhaustive list.
    eligible = tuple(
        feature
        for feature in feature_candidates
        if schema.domain(feature, object_type).distinct > 0
    )
    selected_feature = choose(
        "feature",
        "Choose exactly one listed feature equality, or select none.",
        (Option("none", "No feature predicate"),)
        + tuple(Option(f"f{i:03}", feature) for i, feature in enumerate(eligible)),
    )
    if selected_feature is None:
        return finished("unsupported")
    if evidence[-1].confidence < min_confidence:
        return finished("low_confidence")

    predicates: tuple[Predicate, ...] = ()
    if selected_feature != "none":
        feature = eligible[int(selected_feature[1:])]
        domain = schema.domain(feature, object_type).kind
        options: tuple[Option, ...]
        values: tuple[str, ...]
        if isinstance(domain, Enumerated):
            values = tuple(value for value, _count in domain.values)
            options = tuple(Option(f"v{i:03}", ascii(value)) for i, value in enumerate(values))
        elif isinstance(domain, Large):
            if value_hint is None:
                return finished("unsupported")
            try:
                narrowed = RetrievalIndex.from_schema(schema, domain.retrieval_handle).lookup(
                    value_hint, match=Match.EXACT
                )
                if not narrowed.candidates or narrowed.truncated:
                    return finished("unsupported")
            except (RetrievalError, SchemaError):
                return finished("unsupported")
            values = tuple(candidate.value for candidate in narrowed.candidates)
            options = tuple(
                Option(candidate.label, ascii(candidate.value))
                for candidate in narrowed.candidates
            )
        else:  # integer bounds/feature equality requires a separate scoped design
            return finished("unsupported")
        if not options:
            return finished("unsupported")
        selected_value = choose(
            "value",
            "Choose the exact attested corpus feature value.",
            options,
        )
        if selected_value is None:
            return finished("unsupported")
        if evidence[-1].confidence < min_confidence:
            return finished("low_confidence")
        if isinstance(domain, Large):
            # Resolve the opaque label against the original source inventory.
            value = narrowed.resolve(selected_value)
        else:
            value = values[int(selected_value[1:])]
        predicates = (Predicate(feature, PredicateOp.EQ, (value,)),)
    result = Query((Atom(object_type, predicates),))
    try:
        native = compile_query(result, schema)
    except (CompileError, SchemaError):
        return finished("unsupported")
    return finished("ok", result, native)
