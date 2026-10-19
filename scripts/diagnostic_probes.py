"""Fixed development-only mechanism probes, not alternate query generation."""

from __future__ import annotations

from typing import Any

from scripts.diagnose_abstention import TraceBackend
from tf_jev.decisions import ChoiceQuestion, DecisionBackend, DecisionRequest, Option

VARIANTS = ("control", "reversed", "semantic_labels", "plain_shape", "request_only", "decomposed")
LABELS = ("single_entity", "two_related_entities", "exclude_embedded", "uncertain", "not_supported")
PLAIN = (
    "Return nodes of one kind, filtered by up to three annotations.",
    "Two kinds of nodes connected by one relation; return either kind or both.",
    "Return parent nodes that have no matching contained child nodes.",
    "The request has multiple unresolved meanings.",
    "The complete request cannot be expressed by the other supported structures.",
)


def variant_request(base: DecisionRequest, variant: str) -> tuple[DecisionRequest, tuple[int, ...]]:
    if set(base.questions) != {"shape"}:
        raise ValueError("expected the original shape question")
    question = base.questions["shape"]
    if not isinstance(question, ChoiceQuestion) or len(question.options) != 5:
        raise ValueError("expected all five original shape categories")
    context = dict(base.context)
    mapping = tuple(range(5))
    if variant == "control":
        return base, mapping
    if variant == "reversed":
        changed = ChoiceQuestion(question.prompt, tuple(reversed(question.options)))
        mapping = tuple(reversed(mapping))
    elif variant == "semantic_labels":
        changed = ChoiceQuestion(
            question.prompt,
            tuple(Option(LABELS[i], o.description) for i, o in enumerate(question.options)),
        )
    elif variant == "plain_shape":
        changed = ChoiceQuestion(
            "Choose the complete database request structure. Do not omit constraints. "
            "Use uncertain for unresolved intent and not supported if none fits.",
            tuple(Option(o.label, PLAIN[i]) for i, o in enumerate(question.options)),
        )
    elif variant == "request_only":
        context = {"request": base.context["request"]}
        changed = question
    elif variant == "decomposed":
        return DecisionRequest(
            context,
            {
                f"probe{i}": ChoiceQuestion(
                    "Does the COMPLETE request fit exactly this category? " + (o.description or ""),
                    (Option("o000", "yes"), Option("o001", "no")),
                )
                for i, o in enumerate(question.options)
            },
        ), ()
    else:
        raise ValueError("unknown probe variant")
    return DecisionRequest(context, {"shape": changed}), mapping


def run_probes(
    backend: DecisionBackend, representatives: list[tuple[str, DecisionRequest]]
) -> list[dict[str, Any]]:
    rows = []
    for case_id, base in representatives:
        for variant in VARIANTS:
            request, mapping = variant_request(base, variant)
            for replicate in (1, 2):
                trace = TraceBackend(backend)
                try:
                    trace.decide(request)
                except Exception:
                    pass  # Static call-level error remains in the trace.
                call = trace.calls[0]
                row: dict[str, Any] = dict(
                    id=case_id, variant=variant, replicate=replicate, call=call
                )
                if call["error_kind"] is None and variant != "decomposed":
                    data = call["questions"][0]
                    canonical = [0.0] * 5
                    for position, original in enumerate(mapping):
                        canonical[original] = data["probabilities"][position]
                    row["canonical_probabilities"] = canonical
                    row["canonical_selected_index"] = mapping[data["selected_index"]]
                    row["passes_original_gate"] = (
                        data["top_probability"] >= 0.8 and data["margin"] >= 0.2
                    )
                elif call["error_kind"] is None:
                    yes = [q["probabilities"][0] for q in call["questions"]]
                    row["yes_probabilities"] = yes
                    selected = [i for i, p in enumerate(yes) if p >= 0.8]
                    row["resolved_class"] = (
                        selected[0]
                        if len(selected) == 1
                        and all(i == selected[0] or p <= 0.2 for i, p in enumerate(yes))
                        else None
                    )
                rows.append(row)
    return rows
