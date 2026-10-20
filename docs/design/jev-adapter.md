# Jev DecisionBackend — issue #8

`tf_jev.jev.JevBackend(api_key=None, model="jev-1.13.0", client=None,
timeout=None, retry=None)` implements the existing DecisionBackend protocol.
Install `tf-jev[jev]`; core/compiler/schema imports remain SDK independent.
The optional module gives an actionable ImportError if the extra is absent.

Explicit key wins; otherwise a nonblank JEV_API_KEY wins, then SDK
TYPESAFE_API_KEY. No automatic .env loading. Key validation belongs to the SDK.
The default stays pinned to jev-1.13.0. Explicit jev-1.14.0 is also supported.
Requests require the exact researched response: 1.13 -> 1.13, 1.14 -> 1.14,
jev-latest -> 1.13, jev-preview -> 1.14. An immutable mapping supplies a per-instance
expected model; future/unknown IDs and alias drift fail visibly rather than float.
Receipts record the actual validated version, never relabel 1.14 as 1.13. See the
[#50 contract research](../research/issue-50-model-versions.md).
Capabilities: 255 hard options, 0.01 probability resolution. Retrieval's stricter
32-option policy remains independent. Batched questions share one context and
produce one receipt. Dependent decisions require separate calls by the caller.

ChoiceQuestion maps its prompt and ordered label→description mapping to SDK
Choice. BinaryQuestion maps to Noul. State is a copied context mapping; no corpus
text is collected implicitly. SDK custom response-model decoding requires every
answer's choice/noul tag and catches unknown kinds; validate_answers checks
missing/extra ids, kinds, labels and probabilities. Server confidence is ignored
in favor of the existing local calculation. Metadata validation rejects negative
usage and model drift. Missing token counts stay None.

`BackendError` in decisions.py carries a static kind and optional numeric HTTP
status. Configuration, timeout, connection, authentication, rate limit, other HTTP,
response-validation and closed-client failures remain distinguishable. Response
messages, request ids, SDK errors, credentials and validation field paths are
excluded. DecisionContractError before a call remains a local request error.
SDK logging is suppressed for this adapter's active context using a filter, with
no process-wide logger-level changes. The adapter emits no request/response logs.

`close()` and context management release only an owned SDK client. Supplied
clients remain caller-owned. Close is idempotent; decide after close fails locally.
Timeout and retry options are forwarded to the SDK per call without implementing
retry loops. No async surface, score primitive, semantic parser, query text output,
or model quality claims are added.

Tests: RED first; real SDK + HTTP MockTransport for request/response contract,
malformed/forged answers, model/token metadata, credential-safe errors/logs,
limits, retries and client lifecycle. Live synthetic smoke is opt-in with
TF_JEV_LIVE=1 and credentials explicitly supplied through environment. Normal CI
installs the extra but uses no network-backed test. Wheel checks also verify core
modules work with no SDK installed. Independent review attacks raw HTTP responses
and should exercise a native TF path from a schema-derived bounded decision.
