"""Optional thin adapter over the official synchronous TypeSafe SDK."""

from __future__ import annotations

import logging
import os
import time
from contextvars import ContextVar
from types import TracebackType
from typing import Annotated, NoReturn, Self

try:
    from pydantic import BaseModel, ConfigDict, Field
    from typesafe_sdk import (
        Choice,
        ChoiceAnswer,
        Noul,
        NoulAnswer,
        Question,
        RetryPolicy,
        TypeSafeAPIConnectionError,
        TypeSafeAPIError,
        TypeSafeAPIResponseValidationError,
        TypeSafeAPITimeoutError,
        TypeSafeClient,
        TypeSafeError,
        Usage,
    )
except ImportError:
    raise ImportError("JevBackend requires the optional tf-jev[jev] extra") from None

from tf_jev.decisions import (
    BackendError,
    Capabilities,
    ChoiceQuestion,
    DecisionBatch,
    DecisionContractError,
    DecisionRequest,
    RawAnswer,
    RawBinary,
    RawChoice,
    Receipt,
    check_capabilities,
    validate_answers,
)

DEFAULT_MODEL = "jev-1.13.0"
_REQUEST_MODELS = frozenset({DEFAULT_MODEL, "jev-latest", "jev-preview"})
_QUIET: ContextVar[bool] = ContextVar("tf_jev_sdk_quiet", default=False)


class _ScopedSDKLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _QUIET.get()


# The SDK logs via this exact logger. Filtering affects only this execution context,
# leaves logger configuration alone, and preserves other SDK clients' logs.
logging.getLogger("typesafe_sdk").addFilter(_ScopedSDKLogs())


class _Response(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")
    model: str
    usage: Usage
    answers: dict[str, Annotated[ChoiceAnswer | NoulAnswer, Field(discriminator="type")]]


def _fail(error: BackendError) -> NoReturn:
    try:
        raise error from None
    finally:
        # Even suppressed context retains the original object unless explicitly cleared.
        error.__context__ = None


def _sdk_error(error: TypeSafeError) -> BackendError:
    if isinstance(error, TypeSafeAPIResponseValidationError):
        kind = "response"
    elif isinstance(error, TypeSafeAPITimeoutError):
        kind = "timeout"
    elif isinstance(error, TypeSafeAPIConnectionError):
        kind = "connection"
    elif isinstance(error, TypeSafeAPIError):
        kind = {401: "authentication", 429: "rate_limit"}.get(error.status, "http")
    else:
        kind = "configuration"
    status = error.status if isinstance(error, TypeSafeAPIError) else None
    return BackendError(kind, status)


class JevBackend:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        client: TypeSafeClient | None = None,
        timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        if type(model) is not str or model not in _REQUEST_MODELS:
            _fail(BackendError("configuration"))
        if api_key is not None and type(api_key) is not str:
            _fail(BackendError("configuration"))
        if client is not None and (not isinstance(client, TypeSafeClient) or api_key is not None):
            _fail(BackendError("configuration"))
        if isinstance(timeout, bool):
            _fail(BackendError("configuration"))
        self._model = model
        self._timeout = timeout
        self._retry = retry
        self._closed = False
        self._owns_client = client is None
        failure = None
        token = _QUIET.set(True)
        try:
            if client is None:
                key = api_key
                if key is None:
                    key = os.environ.get("JEV_API_KEY", "").strip() or None
                client = TypeSafeClient(
                    api_key=key, model=model, base_url="https://api.typesafe.ai"
                )
        except TypeSafeError:
            failure = BackendError("configuration")
        finally:
            _QUIET.reset(token)
        if failure is not None:
            _fail(failure)
        assert client is not None
        self._client = client

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(max_options=255, probability_resolution=0.01)

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        if self._closed:
            _fail(BackendError("closed"))
        check_capabilities(request, self.capabilities)
        questions: dict[str, Question] = {}
        for name, question in request.questions.items():
            if isinstance(question, ChoiceQuestion):
                questions[name] = Choice(
                    instructions=question.prompt,
                    criteria={option.label: option.description for option in question.options},
                )
            else:
                questions[name] = Noul(instructions=question.prompt)
        failure = None
        result = None
        token = _QUIET.set(True)
        started = time.perf_counter()
        try:
            response = self._client.system_one(
                state=dict(request.context),
                questions=questions,
                model=self._model,
                timeout=self._timeout,
                retry=self._retry,
                response_model=_Response,
            )
            if response.model != DEFAULT_MODEL:
                _fail(BackendError("response"))
            for count in (response.usage.input_tokens, response.usage.output_tokens):
                if count is not None and (type(count) is not int or count < 0):
                    _fail(BackendError("response"))
            raw: dict[str, RawAnswer] = {}
            for name, answer in response.answers.items():
                if isinstance(answer, ChoiceAnswer):
                    raw[name] = RawChoice(answer.choice, answer.probabilities)
                else:
                    raw[name] = RawBinary(answer.noul)
            validated = validate_answers(request, raw, self.capabilities.probability_resolution)
            result = DecisionBatch(
                validated,
                Receipt(
                    backend="jev",
                    model=response.model,
                    latency_s=time.perf_counter() - started,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                ),
            )
        except TypeSafeError as error:
            failure = _sdk_error(error)
        except DecisionContractError:
            failure = BackendError("response")
        finally:
            _QUIET.reset(token)
        if failure is not None:
            _fail(failure)
        assert result is not None
        return result

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            if self._owns_client:
                self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
