"""Candidate admission differs from proposal certainty; native TF owns semantics."""

from typing import Any

import pytest

from tests.conformance.tf_harness import run_template
from tests.test_grounded_parser import PlanBackend, plan
from tf_jev.candidate import CandidateParser, candidate_meaning
from tf_jev.grounded import Gate, GroundedPolicy
from tf_jev.ir import Atom, Predicate, PredicateOp, Query
from tf_jev.parser import ParseStatus
from tf_jev.schema import extract_schema


def test_weak_proposal_requires_strong_complete_verdict(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    backend = PlanBackend(plan(), "atom0.pred0.feature")
    result = CandidateParser(schema, backend).parse("Return verbs.")
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert result.confidence == pytest.approx(0.65)
    assert run_template(tiny_api, result.query).results == ((3,), (6,), (8,))
    assert "candidate_meaning" in backend.requests[-1].context
    for selected, weak, reason in [
        (plan(), "verify", "low_confidence"),
        (plan() | {"verify": "no"}, None, "candidate_mismatch"),
    ]:
        result = CandidateParser(schema, PlanBackend(selected, weak)).parse("Return verbs.")
        assert result.status is ParseStatus.ABSTAINED and result.reason == reason
        assert result.ir is None and result.query is None and result.projection == ()
    with pytest.raises(ValueError, match="per-stage"):
        CandidateParser(schema, backend, GroundedPolicy(type_gate=Gate()))


def test_complete_three_conditions_native_results(tiny_api: Any) -> None:
    selected = plan()
    for i, (feature, value) in enumerate([("sp", "verb"), ("gn", "f"), ("nu", "pl")]):
        prefix = f"atom0.pred{i}"
        selected.update(
            {
                prefix + ".feature": feature,
                prefix + ".operator": "=",
                prefix + ".count": "1",
                prefix + ".value0": value,
            }
        )
    selected["atom0.pred3.feature"] = "STOP"
    backend = PlanBackend(selected, "atom0.pred1.feature")
    result = CandidateParser(extract_schema(tiny_api), backend).parse(
        "Return feminine plural verbs."
    )
    assert result.status is ParseStatus.SUPPORTED and result.query
    assert run_template(tiny_api, result.query).results == ((6,),)
    meaning = backend.requests[-1].context["candidate_meaning"]
    assert all(f'annotation "{f}"' in meaning for f in ("sp", "gn", "nu"))


@pytest.mark.parametrize(
    "op,expected,description",
    [
        (
            PredicateOp.NE,
            ((1,), (3,), (4,), (5,), (6,), (7,), (8,)),
            "missing annotations also match",
        ),
        (PredicateOp.PRESENT, ((1,), (2,), (3,), (4,)), "including empty strings"),
        (PredicateOp.ABSENT, ((5,), (6,), (7,), (8,)), "must be missing"),
    ],
)
def test_explanation_matches_native_missing_and_empty_semantics(
    tiny_api: Any, op: PredicateOp, expected: tuple[tuple[int, ...], ...], description: str
) -> None:
    from tf_jev.compiler import compile_query

    schema = extract_schema(tiny_api)
    query = Query(
        (Atom("word", (Predicate("suffix", op, ("H",) if op is PredicateOp.NE else ()),)),)
    )
    assert run_template(tiny_api, compile_query(query, schema)).results == expected
    assert description in candidate_meaning(query, (0,), schema)


@pytest.mark.parametrize(
    "name",
    [
        "test_three_predicates_require_done_and_fourth_refuses",
        "test_fidelity_and_backend_failures_emit_no_query",
        "test_complete_parser_roundtrips_real_sdk",
    ],
)
def test_shared_contract_on_candidate_parser(tiny_api: Any, monkeypatch: Any, name: str) -> None:
    import tests.test_grounded_parser as contract

    monkeypatch.setattr(contract, "GroundedParser", CandidateParser)
    getattr(contract, name)(tiny_api)


@pytest.mark.parametrize("shape", ["relation", "without"])
def test_native_witness_scope(tiny_api: Any, monkeypatch: Any, shape: str) -> None:
    import tests.test_grounded_parser as contract

    monkeypatch.setattr(contract, "GroundedParser", CandidateParser)
    contract.test_predicted_parent_child_scope(tiny_api, shape)


def test_distinct_stop_feature(tmp_path: Any, monkeypatch: Any) -> None:
    import tests.test_grounded_parser as contract

    monkeypatch.setattr(contract, "GroundedParser", CandidateParser)
    contract.test_done_feature_is_not_the_stop_sentinel(tmp_path)


@pytest.mark.parametrize(
    "name",
    [
        "test_candidate_meaning_is_complete_and_native_validated",
        "test_meaning_preserves_exclusion_edge_and_distance",
    ],
)
def test_complete_explanation(tiny_api: Any, monkeypatch: Any, name: str) -> None:
    import scripts.jev_focus as research
    import tests.test_jev_focus as contract

    monkeypatch.setattr(research, "candidate_meaning", candidate_meaning)
    getattr(contract, name)(tiny_api)


def test_partial_and_context_limits(tiny_api: Any) -> None:
    from dataclasses import replace

    backend = PlanBackend(plan())
    partial = extract_schema(tiny_api, node_features=("sp",))
    assert (
        CandidateParser(partial, backend).parse("Return verbs.").reason
        == "incomplete_schema_coverage"
    )
    assert not backend.requests
    full = extract_schema(tiny_api)
    feature = replace(full.node_features[0], description='"' * 20000)
    full = replace(full, node_features=(feature, *full.node_features[1:]))
    result = CandidateParser(full, backend).parse("Return verbs.")
    assert result.reason == "context_budget" and result.query is None
    # Focused shape/type questions contain no feature descriptions. Refuse BEFORE
    # sending the escaped feature payload, not necessarily before all model calls.
    assert [next(iter(r.questions)) for r in backend.requests] == ["shape", "atom0.type"]


@pytest.mark.parametrize("limit", [1, 5, 7])
def test_call_budget_withholds_unverified_candidate(tiny_api: Any, limit: int) -> None:
    backend = PlanBackend(plan())
    result = CandidateParser(
        extract_schema(tiny_api), backend, GroundedPolicy(max_calls=limit)
    ).parse("Return verbs.")
    assert result.reason == "call_budget" and result.query is None and result.ir is None
    assert len(backend.requests) == limit
