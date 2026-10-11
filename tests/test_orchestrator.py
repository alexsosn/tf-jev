"""RED-first vertical-slice tests: bounded decisions -> validated QueryIR -> TF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric

from tests.conformance.tf_harness import run_template
from tf_jev.decisions import (
    Capabilities,
    ChoiceDecision,
    DecisionBatch,
    DecisionContractError,
    RawChoice,
    Receipt,
    ScriptedBackend,
)
from tf_jev.orchestrator import parse_one_atom
from tf_jev.schema import CorpusSchema, extract_schema


def selected(label: str, labels: tuple[str, ...], p: float = 0.99) -> RawChoice:
    if len(labels) == 1:
        return RawChoice(label, {label: 1.0})
    return RawChoice(
        label, {other: p if other == label else (1 - p) / (len(labels) - 1)
                for other in labels},
    )


def backend_for(
    schema: CorpusSchema, *, feature: str | None = None, value: str | None = None,
    mode: str = "single", confidence: float = 0.99, max_options: int = 32,
) -> ScriptedBackend:
    types = tuple(x.name for x in schema.object_type_details if x.expressible)
    word_label = f"t{types.index('word'):03}"
    answers = {
        "mode": selected(mode, ("single", "ambiguous", "unsupported"), confidence),
        "type": selected(word_label, tuple(f"t{i:03}" for i in range(len(types)))),
    }
    if feature is None:
        answers["feature"] = selected("none", ("none",))
    else:
        answers["feature"] = selected("f000", ("none", "f000"))
    if value is not None:
        domain = schema.domain(feature or "sp", "word").kind
        from tf_jev.schema import Enumerated, Large

        if isinstance(domain, Enumerated):
            vals = tuple(x for x, _count in domain.values)
            answers["value"] = selected(f"v{vals.index(value):03}", tuple(
                f"v{i:03}" for i in range(len(vals))
            ))
        elif isinstance(domain, Large):
            answers["value"] = selected("c0000", ("c0000",))
    return ScriptedBackend(answers, max_options=max_options)


def test_typed_single_atom_compiles_and_executes_on_real_tf(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    backend = backend_for(schema, feature="sp", value="verb")
    out = parse_one_atom(
        "Give me all verbs", schema, backend, feature_candidates=("sp",)
    )
    assert out.status == "ok"
    assert out.query is not None and out.query.atoms[0].object_type == "word"
    assert out.native_query is not None
    native = run_template(tiny_api, out.native_query, limit=100)
    assert native.ok and native.results == ((3,), (6,), (8,))
    assert len(out.evidence) == 4
    assert out.confidence == min(x.confidence for x in out.evidence)
    assert len(backend.requests) == 4
    assert all(set(r.context) == {"request"} for r in backend.requests)


def test_bare_node_type_uses_only_schema_symbol(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    backend = backend_for(schema)
    out = parse_one_atom("All word nodes", schema, backend)
    assert out.status == "ok" and out.native_query is not None
    native = run_template(tiny_api, out.native_query, limit=100)
    assert native.ok and native.results == tuple((n,) for n in range(1, 9))
    assert len(backend.requests) == 3


@pytest.mark.parametrize("mode", ["ambiguous", "unsupported"])
def test_abstention_does_not_guess_structure(tiny_api: Any, mode: str) -> None:
    schema = extract_schema(tiny_api)
    backend = backend_for(schema, mode=mode)
    out = parse_one_atom("A complex request", schema, backend)
    assert out.status == mode and out.query is None and out.native_query is None
    assert len(backend.requests) == 1


def test_single_low_confidence_mode_abstains_before_any_query(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    backend = backend_for(schema, confidence=0.8)
    out = parse_one_atom("verbs", schema, backend, min_confidence=0.8)
    assert out.status == "low_confidence"
    assert len(backend.requests) == 1 and out.native_query is None
    assert out.confidence < 0.8


def test_feature_budget_blocks_incomplete_choice_set(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    backend = backend_for(schema, max_options=4)
    out = parse_one_atom(
        "Some feature", schema, backend,
        feature_candidates=("lex", "sp", "gn", "nu"),
    )
    assert out.status == "unsupported" and out.native_query is None
    assert len(backend.requests) == 2
    assert all(len(r.questions) == 1 for r in backend.requests)


def test_fail_closed_on_unknown_feature_and_invalid_threshold(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)
    backend = backend_for(schema)
    with pytest.raises(ValueError, match="feature"):
        parse_one_atom("x", schema, backend, feature_candidates=("invented",))
    with pytest.raises(ValueError, match="confidence"):
        parse_one_atom("x", schema, backend, min_confidence=float("nan"))
    assert not backend.requests


def test_reject_backend_forged_label_despite_valid_choice_decision(tiny_api: Any) -> None:
    schema = extract_schema(tiny_api)

    class Forgery:
        capabilities = Capabilities()

        def decide(self, request: Any) -> DecisionBatch:
            return DecisionBatch(
                decisions={"mode": ChoiceDecision("model_invented", {"model_invented": 1.0})},
                receipt=Receipt("fake", "fake"),
            )

    with pytest.raises(DecisionContractError):
        parse_one_atom("Make arbitrary code", schema, Forgery())  # type: ignore[arg-type]


def test_large_domain_exact_retrieval_preserves_original_values(
    tmp_path: Path,
) -> None:
    values = ["a|b", "a b", "a\\b", "e\u0301", "bidi\u202e"] + [
        f"x{i:02}" for i in range(40)
    ]
    tf = Fabric(locations=str(tmp_path), silent="deep")
    assert tf.save(
        nodeFeatures={
            "otype": {**dict.fromkeys(range(1, len(values) + 1), "word"),
                      len(values) + 1: "sentence"},
            "lex": dict(enumerate(values, 1)),
        },
        edgeFeatures={"oslots": {len(values) + 1: set(range(1, len(values) + 1))}},
        metaData={
            "otype": {"valueType": "str"}, "lex": {"valueType": "str"},
            "oslots": {"valueType": "str"},
            "otext": {"fmt:text-orig-full": "{lex}"},
        },
        silent="deep",
    )
    api = Fabric(locations=str(tmp_path), silent="deep").load("lex", silent="deep")
    schema = extract_schema(api)
    for value in ("a|b", "a b", "a\\b", "e\u0301"):
        backend = backend_for(schema, feature="lex", value=value)
        out = parse_one_atom(
            "Find exact word lexeme", schema, backend,
            feature_candidates=("lex",), value_hint=value,
        )
        assert out.status == "ok" and out.query is not None
        assert out.query.atoms[0].predicates[0].values == (value,)
        assert out.native_query is not None
        run = run_template(api, out.native_query, limit=100)
        assert run.ok and run.results == ((values.index(value) + 1,),)

    no_hint = backend_for(schema, feature="lex")
    out = parse_one_atom("Find some lexeme", schema, no_hint, feature_candidates=("lex",))
    assert out.status == "unsupported" and out.native_query is None
    assert len(no_hint.requests) == 3
