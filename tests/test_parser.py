"""Boundary orchestration tests; scripted choices do not establish model quality."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.conformance.tf_harness import load_api, run_template
from tf_jev.decisions import (
    Capabilities,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBatch,
    DecisionRequest,
    Receipt,
)
from tf_jev.parser import ParsePolicy, ParseStatus, SemanticParser
from tf_jev.schema import extract_schema


class ChoosingBackend:
    def __init__(self, choices: dict[str, str], weak: str | None = None) -> None:
        self.choices = choices
        self.weak = weak
        self.requests: list[DecisionRequest] = []

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(max_options=255)

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        self.requests.append(request)
        decisions = {}
        for name, question in request.questions.items():
            assert isinstance(question, ChoiceQuestion)
            target = self.choices.get(name, "0")
            option = next(
                o
                for o in question.options
                if o.description == target or (o.description or "").startswith(target + ":")
            )
            top = 0.6 if name == self.weak else 0.98
            if len(question.options) == 1:
                top = 1.0
            probabilities = {
                o.label: (
                    top if o.label == option.label else (1 - top) / (len(question.options) - 1)
                )
                for o in question.options
            }
            decisions[name] = ChoiceDecision(option.label, probabilities)
        return DecisionBatch(decisions, Receipt("choosing", "test", input_tokens=10))


def choices(shape: str = "atom") -> dict[str, str]:
    return {
        "shape": shape,
        "atom0.type": "word",
        "atom0.count": "1",
        "atom0.pred0.feature": "sp",
        "atom0.pred0.operator": "=",
        "atom0.pred0.count": "1",
        "atom0.pred0.value0": "verb",
        "verify": "yes",
    }


def test_atomic_query_uses_schema_and_native_compiler(tiny_api: Any) -> None:
    backend = ChoosingBackend(choices())
    result = SemanticParser(extract_schema(tiny_api), backend).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED
    assert result.ir is not None and result.query is not None
    assert result.projection == (0,)
    assert run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    assert result.confidence == pytest.approx(0.98)
    assert len(result.evidence) == len(backend.requests)
    assert all(e.receipt.input_tokens == 10 for e in result.evidence)


@pytest.mark.parametrize("stage", ["shape", "atom0.type", "atom0.pred0.feature"])
def test_weak_structural_decision_stops_before_query(tiny_api: Any, stage: str) -> None:
    backend = ChoosingBackend(choices(), weak=stage)
    result = SemanticParser(extract_schema(tiny_api), backend).parse("Return verbs.")
    assert result.status is ParseStatus.ABSTAINED
    assert result.query is None and result.ir is None and result.projection == ()
    assert result.evidence[-1].id == stage
    assert result.confidence == pytest.approx(0.6)


@pytest.mark.parametrize("classification", ["unsupported", "ambiguous"])
def test_explicit_nonquery_states(tiny_api: Any, classification: str) -> None:
    result = SemanticParser(
        extract_schema(tiny_api), ChoosingBackend({"shape": classification})
    ).parse("Find unknown semantics.")
    assert result.status.value == classification
    assert result.query is None and len(result.evidence) == 1


def test_failed_whole_candidate_verification_abstains(tiny_api: Any) -> None:
    selected = choices()
    selected["verify"] = "no"
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(
        "Find irony."
    )
    assert result.status is ParseStatus.ABSTAINED
    assert result.reason == "candidate_mismatch"
    assert result.query is None


@pytest.mark.parametrize("shape", ["relation", "without"])
def test_parent_witness_projection_and_negation(tiny_api: Any, shape: str) -> None:
    selected = choices(shape)
    selected.update(
        {
            "atom0.type": "clause",
            "atom0.count": "0",
            "atom1.type": "word",
            "atom1.count": "1",
            "atom1.pred0.feature": "sp",
            "atom1.pred0.operator": "=",
            "atom1.pred0.count": "1",
            "atom1.pred0.value0": "verb",
            "relation": "[[",
            "output": "[0]",
        }
    )
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(
        "Return clauses with no verbs."
        if shape == "without"
        else "Return distinct clauses containing verbs."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query is not None
    assert result.projection == (0,)
    rows = run_template(tiny_api, result.query).results
    assert rows is not None
    assert {row[0] for row in rows} == (set() if shape == "without" else {14, 15})


def test_integer_bound_comes_from_request(tiny_api: Any) -> None:
    selected = choices()
    selected.update(
        {"atom0.pred0.feature": "rank", "atom0.pred0.operator": ">", "atom0.pred0.value0": "5"}
    )
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(
        "Return words with rank greater than 5."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query is not None
    assert run_template(tiny_api, result.query).results == ((6,), (7,), (8,))
    assert (
        SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected))
        .parse("Return high ranks.")
        .status
        is ParseStatus.UNSUPPORTED
    )


def test_backend_failure_is_sanitized(tiny_api: Any) -> None:
    class Failing(ChoosingBackend):
        def decide(self, request: DecisionRequest) -> DecisionBatch:
            raise RuntimeError("secret-key-and-server-body")

    result = SemanticParser(extract_schema(tiny_api), Failing({})).parse("Return verbs.")
    assert result.status is ParseStatus.ERROR
    assert "secret" not in repr(result)


def test_forged_typed_response_cannot_select_unrequested_token(tiny_api: Any) -> None:
    class Forged(ChoosingBackend):
        def decide(self, request: DecisionRequest) -> DecisionBatch:
            return DecisionBatch(
                {"shape": ChoiceDecision("injected", {"injected": 1.0})}, Receipt("fake", "fake")
            )

    result = SemanticParser(extract_schema(tiny_api), Forged({})).parse("Return verbs.")
    assert result.status is ParseStatus.ERROR and result.query is None


@pytest.mark.parametrize("text", ["", " ", "x" * 8193, "bad\x00input"])
def test_invalid_input_never_reaches_backend(tiny_api: Any, text: str) -> None:
    backend = ChoosingBackend({})
    assert SemanticParser(extract_schema(tiny_api), backend).parse(text).status is ParseStatus.ERROR
    assert not backend.requests


def test_call_budget_and_policy(tiny_api: Any) -> None:
    result = SemanticParser(
        extract_schema(tiny_api), ChoosingBackend(choices()), ParsePolicy(max_calls=1)
    ).parse("Return verbs.")
    assert result.status is ParseStatus.ABSTAINED and result.reason == "call_budget"
    with pytest.raises(ValueError):
        ParsePolicy(min_probability=True)


def test_real_bhsa_compiles_to_native_verbal_clause_results(bhsa_api: Any, bhsa_dir: Path) -> None:
    selected = choices("relation")
    selected.update(
        {
            "atom0.type": "clause",
            "atom0.count": "0",
            "atom1.type": "word",
            "atom1.count": "1",
            "atom1.pred0.feature": "sp",
            "atom1.pred0.operator": "=",
            "atom1.pred0.count": "1",
            "atom1.pred0.value0": "verb",
            "relation": "[[",
            "output": "[0]",
        }
    )
    schema = extract_schema(bhsa_api)
    result = SemanticParser(schema, ChoosingBackend(selected)).parse(
        "Return distinct clauses containing verbs."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query is not None
    native = run_template(bhsa_api, result.query)
    assert native.ok and native.results is not None
    # Native containment oracle; no gold benchmark import or model accuracy claim.
    expected = {c for w in bhsa_api.F.sp.s("verb") for c in bhsa_api.L.u(w, "clause")}
    assert {row[0] for row in native.results} == expected

    lex_choices = choices()
    lex_choices.update({"atom0.pred0.feature": "lex", "atom0.pred0.value0": "BR>["})
    lex_result = SemanticParser(schema, ChoosingBackend(lex_choices)).parse(
        "Return words whose lex annotation is exactly 'BR>['."
    )
    assert lex_result.status is ParseStatus.SUPPORTED and lex_result.query is not None
    assert run_template(bhsa_api, lex_result.query).results == tuple(
        (n,) for n in sorted(bhsa_api.F.lex.s("BR>["))
    )

    edges = choices("relation")
    edges.update(
        {
            "atom0.type": "clause",
            "atom1.type": "clause",
            "atom0.count": "0",
            "atom1.count": "0",
            "relation": "edge_forward",
            "edge": "mother",
            "output": "[1, 0]",
        }
    )
    edge_result = SemanticParser(schema, ChoosingBackend(edges)).parse(
        "Return mother-edge target then source clause pairs."
    )
    assert edge_result.status is ParseStatus.SUPPORTED and edge_result.query is not None
    edge_rows = run_template(bhsa_api, edge_result.query).results
    assert edge_rows is not None and edge_result.projection == (1, 0)
    expected_edges = {
        (m, n)
        for n in bhsa_api.F.otype.s("clause")
        for m in bhsa_api.E.mother.f(n)
        if bhsa_api.F.otype.v(m) == "clause"
    }
    assert {(row[1], row[0]) for row in edge_rows} == expected_edges


@pytest.fixture
def large_api(tmp_path: Path) -> Any:
    from tf.fabric import Fabric

    tf = Fabric(locations=str(tmp_path), silent="deep")
    tf.save(
        nodeFeatures={
            "otype": {**dict.fromkeys(range(1, 34), "word"), 34: "sentence"},
            "lex": {n: f"literal{n:02}" for n in range(1, 34)},
        },
        edgeFeatures={"oslots": {34: set(range(1, 34))}},
        metaData={
            "otype": {"valueType": "str"},
            "oslots": {"valueType": "str"},
            "lex": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{lex} "},
        },
        silent="deep",
    )
    return load_api(tmp_path, features="lex")


def test_large_values_are_retrieved_before_model_selection(large_api: Any) -> None:
    selected = choices()
    selected.update({"atom0.pred0.feature": "lex", "atom0.pred0.value0": "literal07"})
    backend = ChoosingBackend(selected)
    result = SemanticParser(extract_schema(large_api), backend).parse(
        "Return words with lex exactly 'literal07'."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query is not None
    assert run_template(large_api, result.query).results == ((7,),)
    value_question = next(
        r.questions["atom0.pred0.value0"]
        for r in backend.requests
        if "atom0.pred0.value0" in r.questions
    )
    assert isinstance(value_question, ChoiceQuestion)
    assert [o.description for o in value_question.options] == ["literal07"]
    assert all("literal33" not in str(r.context) for r in backend.requests)


def test_large_retrieval_miss_and_seed_budget_stop(large_api: Any) -> None:
    selected = choices()
    selected["atom0.pred0.feature"] = "lex"
    for text, reason in [
        ("Return lex 'not-attested'.", "retrieval_miss"),
        (" ".join(f"unknown{i}" for i in range(40)), "retrieval_seed_budget"),
    ]:
        backend = ChoosingBackend(selected)
        result = SemanticParser(extract_schema(large_api), backend).parse(text)
        assert result.status is ParseStatus.UNSUPPORTED and result.reason == reason
        assert result.query is None
        assert not any("atom0.pred0.value0" in r.questions for r in backend.requests)


def test_disjunction_and_multiple_predicates(tiny_api: Any) -> None:
    selected = choices()
    selected.update(
        {
            "atom0.count": "2",
            "atom0.pred0.count": "2",
            "atom0.pred0.value1": "subs",
            "atom0.pred1.feature": "gn",
            "atom0.pred1.operator": "=",
            "atom0.pred1.count": "1",
            "atom0.pred1.value0": "f",
        }
    )
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(
        "Return feminine verbs or nouns."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query is not None
    assert run_template(tiny_api, result.query).results == ((2,), (5,), (6,))


def test_directed_edges_and_reversed_output_roles(tiny_api: Any) -> None:
    selected = choices("relation")
    selected.update(
        {
            "atom0.type": "clause",
            "atom1.type": "clause",
            "atom0.count": "0",
            "atom1.count": "0",
            "relation": "edge_forward",
            "edge": "mother",
            "output": "[1, 0]",
        }
    )
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(
        "Return target then source clauses linked by mother."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query is not None
    assert result.projection == (1, 0)
    assert run_template(tiny_api, result.query).results == ((15, 14),)


@pytest.mark.parametrize("text", ["rank 5.4", "rank x-5", "rank 1e3"])
def test_integer_fragments_are_not_invented(tiny_api: Any, text: str) -> None:
    selected = choices()
    selected.update({"atom0.pred0.feature": "rank", "atom0.pred0.operator": ">"})
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(text)
    assert result.status is ParseStatus.UNSUPPORTED and result.query is None


def test_backend_option_limit_never_truncates(tiny_api: Any) -> None:
    class Small(ChoosingBackend):
        @property
        def capabilities(self) -> Capabilities:
            return Capabilities(max_options=4)

    backend = Small(choices())
    result = SemanticParser(extract_schema(tiny_api), backend).parse("Return verbs.")
    assert result.status is ParseStatus.UNSUPPORTED and result.reason == "choice_budget"
    assert not backend.requests


def test_margin_can_abstain_despite_high_top_probability(tiny_api: Any) -> None:
    class Close(ChoosingBackend):
        def decide(self, request: DecisionRequest) -> DecisionBatch:
            batch = super().decide(request)
            if "verify" in request.questions:
                question = request.questions["verify"]
                assert isinstance(question, ChoiceQuestion)
                return DecisionBatch(
                    {
                        "verify": ChoiceDecision(
                            question.labels[0], {question.labels[0]: 0.8, question.labels[1]: 0.2}
                        )
                    },
                    batch.receipt,
                )
            return batch

    result = SemanticParser(
        extract_schema(tiny_api), Close(choices()), ParsePolicy(min_margin=0.7)
    ).parse("Return verbs.")
    assert result.status is ParseStatus.ABSTAINED and result.reason == "low_confidence"


def test_compiler_rejects_nonattested_integer_equality(tiny_api: Any) -> None:
    selected = choices()
    selected.update({"atom0.pred0.feature": "rank", "atom0.pred0.value0": "999"})
    result = SemanticParser(extract_schema(tiny_api), ChoosingBackend(selected)).parse(
        "Return rank exactly 999."
    )
    assert result.status is ParseStatus.UNSUPPORTED
    assert result.reason == "compiler_rejected" and result.ir is None


def test_repeated_parse_does_not_reuse_prior_choices(tiny_api: Any) -> None:
    backend = ChoosingBackend(choices())
    parser = SemanticParser(extract_schema(tiny_api), backend)
    first = parser.parse("Return verbs.")
    backend.choices = {"shape": "unsupported"}
    second = parser.parse("Return ranked counts.")
    assert first.status is ParseStatus.SUPPORTED
    assert second.status is ParseStatus.UNSUPPORTED and len(second.evidence) == 1
    assert dict(backend.requests[-1].context)["selected"] == "{}"
