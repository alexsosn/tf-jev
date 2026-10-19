"""Controlled probes preserve options and reveal positions, never raw labels."""

from typing import Any

import pytest

from scripts.diagnostic_probes import run_probes, variant_request
from tf_jev.decisions import (
    Capabilities,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBatch,
    DecisionRequest,
    Option,
    Receipt,
)


def original() -> DecisionRequest:
    return DecisionRequest(
        {"request": "private request", "selected": "{}", "contract": "private contract"},
        {
            "shape": ChoiceQuestion(
                "private prompt",
                tuple(Option(f"o{i:03}", f"private description {i}") for i in range(5)),
            )
        },
    )


def options(request: DecisionRequest, name: str = "shape") -> tuple[Option, ...]:
    question = request.questions[name]
    assert isinstance(question, ChoiceQuestion)
    return question.options


def test_reverse_preserves_label_description_pairs_and_mapping() -> None:
    base = original()
    changed, mapping = variant_request(base, "reversed")
    assert changed.context == base.context
    assert list(mapping) == [4, 3, 2, 1, 0]
    assert options(changed) == tuple(reversed(options(base)))
    assert options(base)[0].label == "o000"


@pytest.mark.parametrize("variant", ["control", "semantic_labels", "plain_shape", "request_only"])
def test_five_way_variants_never_truncate_or_add_categories(variant: str) -> None:
    changed, mapping = variant_request(original(), variant)
    assert len(changed.questions) == 1
    assert len(options(changed)) == 5
    assert list(mapping) == list(range(5))
    if variant == "request_only":
        assert dict(changed.context) == {"request": "private request"}


def test_decomposed_is_five_independent_binary_questions() -> None:
    changed, mapping = variant_request(original(), "decomposed")
    assert len(changed.questions) == 5 and not mapping
    assert all(len(options(changed, name)) == 2 for name in changed.questions)
    assert changed.context == original().context


def test_probe_canonicalization_and_batch_accounting() -> None:
    class First:
        capabilities = Capabilities()

        def decide(self, request: Any) -> DecisionBatch:
            answers = {}
            for name, q in request.questions.items():
                answers[name] = ChoiceDecision(
                    q.options[0].label, {o.label: float(i == 0) for i, o in enumerate(q.options)}
                )
            return DecisionBatch(answers, Receipt("fake", "fake", 0.0, 10, 2))

    rows = run_probes(First(), [("case", original())])
    assert len(rows) == 12
    reverse = next(r for r in rows if r["variant"] == "reversed")
    assert reverse["canonical_probabilities"] == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert reverse["canonical_selected_index"] == 4
    binary = next(r for r in rows if r["variant"] == "decomposed")
    assert len(binary["call"]["questions"]) == 5 and binary["call"]["input_tokens"] == 10
    assert binary["resolved_class"] is None  # all five yes answers conflict
    assert not any("private" in str(r) for r in rows)


def test_unknown_variant_refuses() -> None:
    with pytest.raises(ValueError):
        variant_request(original(), "invented")


def test_all_probe_variants_roundtrip_real_sdk_mock_transport() -> None:
    import json

    http = pytest.importorskip("httpx2")
    sdk = pytest.importorskip("typesafe_sdk")
    from tf_jev.jev import JevBackend

    calls = []

    def handle(request: Any) -> Any:
        body = json.loads(request.content)
        calls.append(body)
        answers = {}
        for name, q in body["questions"].items():
            labels = list(q["criteria"])
            answers[name] = dict(
                type="choice",
                choice=labels[0],
                confidence=1.0,
                probabilities={v: float(i == 0) for i, v in enumerate(labels)},
            )
        return http.Response(
            200,
            json=dict(
                model="jev-1.13.0", answers=answers, usage=dict(input_tokens=13, output_tokens=7)
            ),
            request=request,
        )

    with sdk.TypeSafeClient(
        api_key="test-only",
        transport=http.MockTransport(handle),
        retry=sdk.RetryPolicy(max_retries=0),
    ) as client:
        with JevBackend(client=client) as backend:
            rows = run_probes(backend, [("case", original())])
    assert len(calls) == len(rows) == 12
    assert all(r["call"]["error_kind"] is None for r in rows)
    assert sum(r["call"]["input_tokens"] for r in rows) == 12 * 13
    assert len(calls[-1]["questions"]) == 5
    assert all("private" not in str(r) and "test-only" not in str(r) for r in rows)
