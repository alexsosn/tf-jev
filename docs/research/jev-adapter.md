# Jev adapter follow-through — issue #8

Rechecked 2026-10-11 against installed official typesafe-sdk 0.7.4 source
(`_core/client/sync/client.py`, `endpoints.py`, `response_types.py`,
`schemas/base.py`, `transport.py`, `logging.py`, `errors.py`, `retry.py`) and
current [API](https://docs.typesafe.ai/api.md) /
[model](https://docs.typesafe.ai/models.md) documentation. The earlier
[backend research](jev-decision-backend.md) remains the dependency decision.

The synchronous client exposes public `system_one(..., response_model=...)`.
Custom Pydantic models use the SDK's normal HTTP/JSON decoding and error handling.
This avoids the default SystemOneResponse decoder's deliberate dropping of
unknown answer types: an unexpected extra question must not disappear before
our request/answer consistency check. Use SDK ChoiceAnswer/NoulAnswer/Usage with
a tagged choice/noul union in a required answer mapping. Strictness is validated
with actual SDK MockTransport calls, not a fake that bypasses serialization.

SDK debug logging includes raw bodies; info logs include server request ids.
Secret-header redaction does not cover a credential echoed in a body or request
id. Suppress the SDK logger only in the adapter's active execution context with
a ContextVar filter. Do not globally lower its level or suppress other clients.
Normalize errors to static kinds and numeric HTTP status only. No server message,
field path, request id, raw response or SDK exception chain reaches the public
error or receipt. SDK transport/HTTP error types remain responsible for retries.

Usage exposes optional input/output token counts but no charged-cost field.
Retain counts and local elapsed time (including retries); do not invent billed
cost from a historical price. SDK response confidence is not a correctness oracle;
recompute confidence from request-bound validated probabilities as before.
Negative token counts and unexpected resolved models are invalid responses.

Probability rounding is only researched for jev-1.13.0. Pin that default and
require it in the resolved response, even if an explicit alias is requested.
Reject other model configurations until their contract is researched. A supplied
SDK client can configure transport for testing/advanced use; the adapter still
overrides the requested model. Owned clients explicitly use the official API
root, overriding TYPESAFE_BASE_URL so an environment setting cannot silently
redirect request data/authentication. SDK handles auth syntax, retries/timeouts
and pooling. No new transport is justified.
