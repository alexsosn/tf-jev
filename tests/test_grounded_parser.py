"""Opt-in predicted planning against real native TF semantics."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from tests.conformance.tf_harness import build_tiny_corpus, load_api, run_template
from tests.test_parser import ChoosingBackend, choices
from tf_jev.decisions import Capabilities, ChoiceDecision, ChoiceQuestion, DecisionBatch, Receipt
from tf_jev.grounded import Gate, GroundedParser, GroundedPolicy
from tf_jev.parser import ParsePolicy, ParseStatus, SemanticParser
from tf_jev.schema import extract_schema


class PlanBackend:
    capabilities = Capabilities(max_options=255)

    def __init__(self, selections: dict[str, str], weak: str | None = None) -> None:
        self.selections, self.weak = selections, weak
        self.requests: list[Any] = []

    def decide(self, request: Any) -> DecisionBatch:
        self.requests.append(request)
        answers = {}
        for name, question in request.questions.items():
            assert isinstance(question, ChoiceQuestion)
            target = self.selections.get(name, "STOP")

            def matches(description: str | None, target: str = target) -> bool:
                d = description or ""
                if d.startswith("{"):
                    record = json.loads(d)
                    return bool(
                        record.get("kind") == "stop"
                        if target == "STOP"
                        else record.get("name") == target
                    )
                return d == target or d.startswith(target + ":")

            selected = next(o for o in question.options if matches(o.description))
            top = 0.65 if name == self.weak else 0.99
            if len(question.options) == 1:
                top = 1.0
            probabilities = {
                o.label: top if o == selected else (1 - top) / (len(question.options) - 1)
                for o in question.options
            }
            answers[name] = ChoiceDecision(selected.label, probabilities)
        return DecisionBatch(answers, Receipt("scripted", "test", 0.001, 11, 2))


def plan() -> dict[str, str]:
    result = choices()
    result.pop("atom0.count")
    result["atom0.pred1.feature"] = "STOP"
    return result


def test_public_api_predicts_features_and_native_query(tiny_api: Any) -> None:
    backend = PlanBackend(plan())
    schema = extract_schema(tiny_api)
    result = GroundedParser(schema, backend).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    assert not any(e.id == "atom0.count" for e in result.evidence)
    corpus = json.loads(backend.requests[0].context["corpus"])
    assert {t["name"] for t in corpus["types"]} == set(schema.object_types)
    assert "regex" in backend.requests[0].context["grammar"]
    assert "values" not in backend.requests[0].context["corpus"]
    candidate = json.loads(backend.requests[-1].context["candidate"])
    assert candidate["query"]["atoms"][0]["predicates"][0]["feature"] == "sp"
    assert candidate["projection"] == [0]


def test_legacy_parser_remains_unchanged(tiny_api: Any) -> None:
    backend = ChoosingBackend(choices())
    result = SemanticParser(extract_schema(tiny_api), backend).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED
    assert "corpus" not in backend.requests[0].context
    assert any(e.id == "atom0.count" for e in result.evidence)
    assert ParsePolicy().min_probability == 0.8


def test_three_predicates_require_done_and_fourth_refuses(tiny_api: Any) -> None:
    selected = plan()
    for i, (f, v) in enumerate([("sp", "verb"), ("gn", "f"), ("nu", "pl")]):
        prefix = f"atom0.pred{i}"
        selected.update(
            {
                prefix + ".feature": f,
                prefix + ".operator": "=",
                prefix + ".count": "1",
                prefix + ".value0": v,
            }
        )
    selected["atom0.pred3.feature"] = "STOP"
    schema = extract_schema(tiny_api)
    result = GroundedParser(schema, PlanBackend(selected)).parse("Return feminine plural verbs.")
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(tiny_api, result.query).results == ((6,),)
    assert any(e.id == "atom0.pred3.feature" for e in result.evidence)
    selected["atom0.pred3.feature"] = "rank"
    result = GroundedParser(schema, PlanBackend(selected)).parse(
        "Return feminine plural verbs with rank greater than 2."
    )
    assert result.status is ParseStatus.UNSUPPORTED and result.reason == "predicate_budget"
    assert result.query is None and result.ir is None and result.projection == ()
    assert result.evidence[-1].id == "atom0.pred3.feature"


def test_done_feature_is_not_the_stop_sentinel(tmp_path: Path) -> None:
    from tf.fabric import Fabric

    build_tiny_corpus(tmp_path)
    assert Fabric(locations=str(tmp_path), silent="deep").save(
        nodeFeatures={"DONE": {1: "yes"}}, metaData={"DONE": {"valueType": "str"}}, silent="deep"
    )
    api = load_api(tmp_path)
    selected = plan()
    selected.update({"atom0.pred0.feature": "DONE", "atom0.pred0.operator": "present"})
    result = GroundedParser(extract_schema(api), PlanBackend(selected)).parse(
        "Return words with DONE present."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(api, result.query).results == ((1,),)


def test_explicit_stage_gate_preserves_defaults(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    default = GroundedParser(schema, PlanBackend(plan(), "atom0.type")).parse("Return verbs.")
    assert default.status is ParseStatus.ABSTAINED
    result = GroundedParser(
        schema, PlanBackend(plan(), "atom0.type"), GroundedPolicy(type_gate=Gate(0.6, 0.2))
    ).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED and result.confidence == pytest.approx(0.65)
    for bad in [True, float("nan"), float("inf"), -0.1, 1.1]:
        with pytest.raises(ValueError):
            Gate(bad, 0.2)
    with pytest.raises(ValueError):
        GroundedPolicy(type_gate=("bad",))  # type: ignore[arg-type]


@pytest.mark.parametrize("shape", ["relation", "without"])
def test_predicted_parent_child_scope(tiny_api: Any, shape: str) -> None:
    selected = plan()
    selected.update(
        {
            "shape": shape,
            "atom0.type": "phrase",
            "atom0.pred0.feature": "function",
            "atom0.pred0.operator": "=",
            "atom0.pred0.count": "1",
            "atom0.pred0.value0": "Objc",
            "atom1.type": "word",
            "atom1.pred0.feature": "sp",
            "atom1.pred0.operator": "=",
            "atom1.pred0.count": "1",
            "atom1.pred0.value0": "verb",
            "atom1.pred1.feature": "STOP",
            "relation": "[[",
            "output": "[0]",
        }
    )
    backend = PlanBackend(selected)
    result = GroundedParser(extract_schema(tiny_api), backend).parse(
        "Return object phrases with no verbal word."
        if shape == "without"
        else "Return distinct object phrases containing a verbal word."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query
    rows = run_template(tiny_api, result.query).results
    assert rows == (() if shape == "without" else ((12, 6),))
    request = next(r for r in backend.requests if "atom1.pred0.feature" in r.questions)
    assert json.loads(request.context["focus"])["object_type"] == "word"
    assert json.loads(request.context["focus"])["predicates"] == []


def test_partial_and_escaped_budget_refuse_before_backend(tiny_api: Any) -> None:
    backend = PlanBackend(plan())
    partial = extract_schema(tiny_api, node_features=("sp",))
    assert (
        GroundedParser(partial, backend).parse("Return verbs.").reason
        == "incomplete_schema_coverage"
    )
    full = extract_schema(tiny_api)
    feature = replace(full.node_features[0], description='"' * 20000)
    full = replace(full, node_features=(feature, *full.node_features[1:]))
    assert GroundedParser(full, backend).parse("Return verbs.").reason == "context_budget"
    assert not backend.requests


def test_fidelity_and_backend_failures_emit_no_query(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    selected = plan()
    selected["verify"] = "no"
    result = GroundedParser(schema, PlanBackend(selected)).parse("Return verbs.")
    assert result.reason == "candidate_mismatch" and result.query is None

    class Hostile(PlanBackend):
        def decide(self, request: Any) -> Any:
            raise RuntimeError("secret-key-private-server-error")

    result = GroundedParser(schema, Hostile(plan())).parse("Return verbs.")
    assert result.status is ParseStatus.ERROR and result.reason == "backend_or_contract"
    assert "secret" not in str(result)


def test_complete_parser_roundtrips_real_sdk(tiny_api: Any) -> None:
    http = pytest.importorskip("httpx2")
    sdk = pytest.importorskip("typesafe_sdk")
    from tf_jev.decisions import DecisionRequest, Option
    from tf_jev.jev import JevBackend

    planner = PlanBackend(plan())
    calls = []

    def handle(request: Any) -> Any:
        wire = json.loads(request.content)
        calls.append(wire)
        native = DecisionRequest(
            wire["state"],
            {
                name: ChoiceQuestion(
                    q["instructions"],
                    tuple(
                        Option(label, description) for label, description in q["criteria"].items()
                    ),
                )
                for name, q in wire["questions"].items()
            },
        )
        batch = planner.decide(native)
        answers = {}
        for name, d in batch.decisions.items():
            assert isinstance(d, ChoiceDecision)
            answers[name] = dict(
                type="choice",
                choice=d.selected,
                probabilities=dict(d.probabilities),
                confidence=1.0,
            )
        return http.Response(
            200,
            json=dict(
                model="jev-1.13.0", answers=answers, usage=dict(input_tokens=11, output_tokens=2)
            ),
            request=request,
        )

    with sdk.TypeSafeClient(
        api_key="test-only",
        transport=http.MockTransport(handle),
        retry=sdk.RetryPolicy(max_retries=0),
    ) as client:
        with JevBackend(client=client) as backend:
            result = GroundedParser(extract_schema(tiny_api), backend).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    assert len(result.evidence) == len(calls) == 8
    assert sum(e.receipt.input_tokens or 0 for e in result.evidence) == 88
    assert json.loads(calls[-1]["state"]["candidate"])["projection"] == [0]
