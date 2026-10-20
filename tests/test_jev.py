"""Exercise the adapter through the real SDK's HTTP serialization/decoding."""

from __future__ import annotations

import json
import logging
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest

httpx2 = pytest.importorskip("httpx2")
pytest.importorskip("typesafe_sdk")
from typesafe_sdk import RetryPolicy, TypeSafeClient  # noqa: E402

from tf_jev.decisions import (  # noqa: E402
    BackendError,
    BinaryQuestion,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBackend,
    DecisionContractError,
    DecisionRequest,
    Option,
)
from tf_jev.jev import DEFAULT_MODEL, JevBackend  # noqa: E402

SECRET = "test-key-do-not-log"
PRIVATE = "private-request-do-not-log"


def request() -> DecisionRequest:
    return DecisionRequest(
        {"mention": PRIVATE},
        {
            "value": ChoiceQuestion("Select", (Option("c0", "e\u0301"), Option("c1", None))),
            "binary": BinaryQuestion("Is it structural?"),
        },
    )


def response() -> dict[str, Any]:
    return {
        "model": DEFAULT_MODEL,
        "usage": {"input_tokens": 20, "output_tokens": 5},
        "answers": {
            "value": {
                "type": "choice",
                "choice": "c0",
                "probabilities": {"c0": 0.75, "c1": 0.25},
                "confidence": 0.99,
            },
            "binary": {"type": "noul", "noul": 0.6},
        },
    }


@contextmanager
def backend(
    payload: Any, status: int = 200
) -> Iterator[tuple[JevBackend, list[Any], TypeSafeClient]]:
    calls: list[Any] = []

    def handle(req: Any) -> Any:
        calls.append({"body": json.loads(req.content), "auth": req.headers["authorization"]})
        return httpx2.Response(
            status, json=payload, headers={"x-typesafe-request-id": SECRET}, request=req
        )

    client = TypeSafeClient(
        api_key=SECRET, transport=httpx2.MockTransport(handle), retry=RetryPolicy(max_retries=0)
    )
    adapter = JevBackend(client=client)
    try:
        yield adapter, calls, client
    finally:
        adapter.close()
        client.close()


def test_request_mapping_and_validated_receipt() -> None:
    with backend(response()) as (adapter, calls, _):
        protocol: DecisionBackend = adapter
        assert protocol.capabilities.max_options == 255
        assert protocol.capabilities.probability_resolution == 0.01
        result = protocol.decide(request())
        assert len(calls) == 1
        body = calls[0]["body"]
        assert body == {
            "state": {"mention": PRIVATE},
            "model": DEFAULT_MODEL,
            "questions": {
                "value": {
                    "type": "choice",
                    "instructions": "Select",
                    "criteria": {"c0": "e\u0301", "c1": None},
                },
                "binary": {"type": "noul", "instructions": "Is it structural?"},
            },
        }
        value = result.decisions["value"]
        assert isinstance(value, ChoiceDecision) and value.selected == "c0"
        assert value.confidence == 0.5  # recomputed, not wire confidence 0.99
        assert result.receipt.backend == "jev" and result.receipt.model == DEFAULT_MODEL
        assert result.receipt.input_tokens == 20 and result.receipt.output_tokens == 5
        assert result.receipt.latency_s >= 0
        assert SECRET not in repr(adapter) + repr(result)
        assert PRIVATE not in repr(result)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "future_extra",
        "wrong_kind",
        "unknown_label",
        "probability_labels",
        "negative_probability",
        "boolean_probability",
        "string_probability",
        "bad_sum",
        "not_top",
        "negative_tokens",
        "bool_tokens",
        "string_tokens",
        "model_drift",
        "missing_answers",
        "missing_type",
        "malformed_answer",
        "missing_usage",
    ],
)
def test_rejects_malformed_or_unrequested_answers(mutation: str) -> None:
    body = response()
    choice = body["answers"]["value"]
    if mutation == "missing":
        del body["answers"]["binary"]
    elif mutation == "extra":
        body["answers"]["extra"] = {"type": "noul", "noul": 0.5}
    elif mutation == "future_extra":
        body["answers"]["extra"] = {"type": "future", "text": SECRET}
    elif mutation == "wrong_kind":
        body["answers"]["value"] = {"type": "noul", "noul": 0.5}
    elif mutation == "unknown_label":
        choice["choice"] = SECRET
    elif mutation == "probability_labels":
        choice["probabilities"] = {"c0": 0.75, SECRET: 0.25}
    elif mutation == "negative_probability":
        choice["probabilities"]["c1"] = -0.25
    elif mutation == "boolean_probability":
        choice["probabilities"]["c1"] = True
    elif mutation == "string_probability":
        choice["probabilities"]["c1"] = "0.25"
    elif mutation == "bad_sum":
        choice["probabilities"] = {"c0": 1.0, "c1": 1.0}
    elif mutation == "not_top":
        choice["choice"] = "c1"
    elif mutation == "negative_tokens":
        body["usage"]["input_tokens"] = -1
    elif mutation == "bool_tokens":
        body["usage"]["input_tokens"] = True
    elif mutation == "string_tokens":
        body["usage"]["input_tokens"] = "20"
    elif mutation == "model_drift":
        body["model"] = SECRET
    elif mutation == "missing_answers":
        del body["answers"]
    elif mutation == "missing_type":
        del choice["type"]
    elif mutation == "malformed_answer":
        body["answers"]["value"] = SECRET
    elif mutation == "missing_usage":
        del body["usage"]
    with backend(body) as (adapter, _, _):
        with pytest.raises(BackendError) as exc:
            adapter.decide(request())
        assert exc.value.kind == "response"
        rendered = "".join(traceback.format_exception(exc.value))
        assert SECRET not in rendered and PRIVATE not in rendered
        assert exc.value.__cause__ is None and exc.value.__context__ is None


@pytest.mark.parametrize(
    ("status", "kind"), [(400, "http"), (401, "authentication"), (429, "rate_limit"), (529, "http")]
)
def test_http_errors_and_debug_logging_do_not_leak(
    status: int,
    kind: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    with backend({"error": SECRET + PRIVATE}, status) as (adapter, _, _):
        with pytest.raises(BackendError) as exc:
            adapter.decide(request())
        assert exc.value.kind == kind and exc.value.status == status
        assert SECRET not in caplog.text + repr(exc.value) + str(exc.value)
        assert PRIVATE not in caplog.text + "".join(traceback.format_exception(exc.value))
        assert exc.value.__context__ is None


def test_missing_token_counts_stay_unknown() -> None:
    body = response()
    body["usage"] = {}
    with backend(body) as (adapter, _, _):
        result = adapter.decide(request())
        assert result.receipt.input_tokens is None and result.receipt.output_tokens is None


def test_limits_checked_before_http_and_lifecycle() -> None:
    with backend(response()) as (adapter, calls, client):
        too_big = DecisionRequest(
            {}, {"q": ChoiceQuestion("Choose", tuple(Option(f"c{i}") for i in range(256)))}
        )
        with pytest.raises(DecisionContractError):
            adapter.decide(too_big)
        assert not calls
        adapter.close()
        adapter.close()
        assert not client._http_client.is_closed  # supplied client remains caller-owned
        with pytest.raises(BackendError) as exc:
            adapter.decide(request())
        assert exc.value.kind == "closed" and not calls


def test_owned_client_configuration_and_key_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[Any] = []
    original = TypeSafeClient.__init__

    def inspect(self: Any, **kwargs: Any) -> None:
        seen.append(kwargs.copy())
        kwargs["transport"] = httpx2.MockTransport(
            lambda req: httpx2.Response(200, json=response())
        )
        original(self, **kwargs)

    monkeypatch.setattr(TypeSafeClient, "__init__", inspect)
    monkeypatch.setenv("JEV_API_KEY", "project-key")
    monkeypatch.setenv("TYPESAFE_API_KEY", "sdk-key")
    monkeypatch.setenv("TYPESAFE_DEFAULT_MODEL", "different")
    monkeypatch.setenv("TYPESAFE_BASE_URL", "https://untrusted.invalid")
    for explicit, expected in [("explicit-key", "explicit-key"), (None, "project-key")]:
        with JevBackend(api_key=explicit) as adapter:
            owned = adapter._client
            assert seen[-1]["api_key"] == expected
            assert seen[-1]["base_url"] == "https://api.typesafe.ai"
            assert adapter.decide(request()).receipt.model == DEFAULT_MODEL
        assert owned._http_client.is_closed
    monkeypatch.setenv("JEV_API_KEY", " ")
    with JevBackend() as adapter:
        assert seen[-1]["api_key"] is None  # let SDK resolve TYPESAFE_API_KEY


def test_invalid_configuration_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    for env in ("JEV_API_KEY", "TYPESAFE_API_KEY"):
        monkeypatch.delenv(env, raising=False)
    configurations: list[dict[str, Any]] = [
        {},
        {"api_key": ""},
        {"api_key": "bad key"},
        {"api_key": SECRET, "model": SECRET},
    ]
    for kwargs in configurations:
        with pytest.raises(BackendError) as exc:
            JevBackend(**kwargs)
        assert exc.value.kind == "configuration" and SECRET not in str(exc.value)


def test_sdk_retry_is_reused_and_latency_includes_call() -> None:
    attempts: list[Any] = []

    def handle(req: Any) -> Any:
        attempts.append(req)
        return httpx2.Response(429 if len(attempts) == 1 else 200, json=response(), request=req)

    with TypeSafeClient(api_key=SECRET, transport=httpx2.MockTransport(handle)) as client:
        with JevBackend(
            client=client,
            retry=RetryPolicy(max_retries=1, backoff_initial=0, backoff_max=0, backoff_jitter=0),
        ) as adapter:
            result = adapter.decide(request())
            assert len(attempts) == 2 and result.receipt.latency_s >= 0


@pytest.mark.parametrize(
    ("exception", "kind"), [("timeout", "timeout"), ("connection", "connection")]
)
def test_transport_failure_is_normalized(exception: str, kind: str) -> None:
    def handle(req: Any) -> Any:
        cls = httpx2.ReadTimeout if exception == "timeout" else httpx2.ConnectError
        raise cls(SECRET + PRIVATE, request=req)

    with TypeSafeClient(
        api_key=SECRET, transport=httpx2.MockTransport(handle), retry=RetryPolicy(max_retries=0)
    ) as client:
        with JevBackend(client=client) as adapter:
            with pytest.raises(BackendError) as exc:
                adapter.decide(request())
            assert exc.value.kind == kind
            assert SECRET not in "".join(traceback.format_exception(exc.value))
            assert exc.value.__context__ is None


def test_schema_decision_to_native_tf_execution(tiny_api: Any) -> None:
    from tests.conformance.tf_harness import run_template
    from tf_jev.compiler import compile_query
    from tf_jev.ir import Atom, Predicate, PredicateOp, Query
    from tf_jev.schema import Enumerated, extract_schema

    schema = extract_schema(tiny_api)
    domain = schema.domain("sp", "word").kind
    assert isinstance(domain, Enumerated)
    labels = {f"c{i}": value for i, (value, _) in enumerate(domain.values)}
    question = ChoiceQuestion(
        "Find verbs", tuple(Option(label, value) for label, value in labels.items())
    )
    selected = next(label for label, value in labels.items() if value == "verb")
    body = response()
    body["answers"] = {
        "sp": {
            "type": "choice",
            "choice": selected,
            "confidence": 1.0,
            "probabilities": {label: float(label == selected) for label in labels},
        }
    }
    with backend(body) as (adapter, _, _):
        result = adapter.decide(DecisionRequest({"request": "find verbs"}, {"sp": question}))
    decision = result.decisions["sp"]
    assert isinstance(decision, ChoiceDecision)
    value = labels[decision.selected]
    text = compile_query(
        Query((Atom("word", (Predicate("sp", PredicateOp.EQ, (value,)),)),)), schema
    )
    native = run_template(tiny_api, text, limit=100)
    assert native.ok and native.results == tuple(
        (n,) for n, v in tiny_api.F.sp.items() if v == "verb"
    )


def test_logging_scope_restores_unrelated_sdk_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    sdk_log = logging.getLogger("typesafe_sdk")
    before = sdk_log.level
    with backend(response()) as (adapter, _, _):
        adapter.decide(request())
        sdk_log.warning("outside adapter scope")
    assert "outside adapter scope" in caplog.text
    assert SECRET not in caplog.text and PRIVATE not in caplog.text
    assert sdk_log.level == before


def test_explicit_alias_still_requires_researched_resolved_model() -> None:
    with backend(response()) as (_, calls, client):
        with JevBackend(client=client, model="jev-latest") as adapter:
            assert adapter.decide(request()).receipt.model == DEFAULT_MODEL
        assert calls[0]["body"]["model"] == "jev-latest"


@pytest.mark.parametrize(
    "requested,expected",
    [
        ("jev-1.13.0", "jev-1.13.0"),
        ("jev-1.14.0", "jev-1.14.0"),
        ("jev-latest", "jev-1.13.0"),
        ("jev-preview", "jev-1.14.0"),
    ],
)
@pytest.mark.parametrize(
    "returned", ["jev-1.13.0", "jev-1.14.0", "jev-1.15.0", "jev-preview", SECRET]
)
def test_requested_model_requires_exact_researched_resolution(
    requested: str,
    expected: str,
    returned: str,
) -> None:
    from dataclasses import FrozenInstanceError

    payload = response()
    payload["model"] = returned
    with backend(payload) as (_, calls, client):
        with JevBackend(client=client, model=requested) as adapter:
            if returned == expected:
                result = adapter.decide(request())
                assert result.receipt.model == expected
                with pytest.raises(FrozenInstanceError):
                    result.receipt.model = "changed"
            else:
                with pytest.raises(BackendError) as error:
                    adapter.decide(request())
                assert error.value.kind == "response"
                assert SECRET not in str(error.value) and error.value.__context__ is None
        assert not client._http_client.is_closed
        assert len(calls) == 1 and calls[0]["body"]["model"] == requested


def test_unknown_future_request_fails_before_transport() -> None:
    with backend(response()) as (_, calls, client):
        with pytest.raises(BackendError) as error:
            JevBackend(client=client, model="jev-1.15.0")
        assert error.value.kind == "configuration" and calls == []


def test_new_model_schema_choice_compiles_and_executes_native(tiny_api: Any) -> None:
    from tests.conformance.tf_harness import run_template
    from tf_jev.compiler import compile_query
    from tf_jev.ir import Atom, Predicate, PredicateOp, Query
    from tf_jev.schema import extract_schema

    schema = extract_schema(tiny_api)
    values = ("verb", "subs")
    for value in values:
        schema.validate_value("sp", "word", value)
    req = DecisionRequest(
        {"request": "select the verb annotation"},
        {
            "value": ChoiceQuestion(
                "Select an actual corpus value.",
                tuple(Option(f"c{i}", v) for i, v in enumerate(values)),
            )
        },
    )
    payload = response()
    payload["model"] = "jev-1.14.0"
    del payload["answers"]["binary"]
    with backend(payload) as (_, calls, client):
        with JevBackend(client=client, model="jev-1.14.0") as adapter:
            result = adapter.decide(req)
        answer = result.decisions["value"]
        assert isinstance(answer, ChoiceDecision)
        value = values[req.questions["value"].labels.index(answer.selected)]  # type: ignore[union-attr]
        query = compile_query(
            Query((Atom("word", (Predicate("sp", PredicateOp.EQ, (value,)),)),)), schema
        )
        assert run_template(tiny_api, query).results == ((3,), (6,), (8,))
        assert calls[0]["body"]["model"] == result.receipt.model == "jev-1.14.0"
