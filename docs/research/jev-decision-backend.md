# Jev API, existing clients, and the backend-neutral decision contract

Research for issue #6, done 2026-10-11.

Every claim below is grounded in one of three places:

- the official docs at `docs.typesafe.ai`, which I fetched as Markdown via `llms.txt`;
- the source of `typesafe-sdk==0.7.4`;
- an opt-in live probe of `jev-1.13.0` run on 2026-10-11 with the project key.

I did not use README, blog or third-party guide material as evidence. Several of those sources contradict each other: some name the package `typesafe-ai` (a redirect shim) or `jev`, which is an unrelated decorator package that needs Python ≥3.14.

## 1. API contract (verified)

| Topic | Finding | Source |
|---|---|---|
| Endpoint | `POST https://api.typesafe.ai/v1/systemone` with `Authorization: Bearer <key>`. `GET /v1/models` lists the aliases only. | docs `api.md`, `models.md`; probe |
| Request | `{state, model, questions}`. `state` is a string, object or array. Question ids are **not** sent to the model. Option labels **and** their descriptions **are** sent. | `api.md`, `primitives/choice.md` |
| Noul | `instructions`, optional `criteria{true,false}`. The answer is `{noul: p}` with **no confidence field**. | `api.md`; SDK `NoulAnswer` |
| Choice | `criteria` maps a label to a description or `null`. The answer is `{choice, probabilities, confidence}`. | `api.md` |
| Score | An ordered `criteria` list. The answer is `{score, legend, probabilities, confidence}`, where `score` is the probability-weighted mean. | `api.md` |
| Choice limit | **255 options.** The probe sent 256 and got **400** "Too many choices. Must have at most 255 choices." | probe |
| Score limit | **10 levels.** 11 gave **400**. A single level is accepted, although the docs say "at least two". | probe |
| Questions per call | Not documented as a count. The limit is the context budget: 64k tokens per request, and 32k for `state` plus the longest question. 64 nouls in one call worked (1,224 input tokens, 535 ms). | `models.md`; probe |
| Batching semantics | `state` is ingested once and every question is evaluated against it in parallel, so answers are independent. | `models.md` |
| Probabilities | Floats rounded to **two decimals** (e.g. `0.98/0.01/0.01`). Sums are 1 within rounding. In a 255-option answer almost every tail option is exactly `0.0`. | probe |
| Confidence | Choice: `(p_max − 1/n)/(1 − 1/n)`. Score: a distance-weighted variant. Noul: none (use `|2p−1|`). | `confidence.md` |
| Model pinning | Alias `jev-latest` → `jev-1.13.0`, and `jev-preview` is currently the same. Versioned ids are accepted even though `/v1/models` doesn't list them. The response `model` field reports the resolved version. An unknown model gives **400** "Unknown model". | `models.md`; probe |
| Errors | The docs list 401, 422 (validation), 429 (rate limit) and 529 (overloaded). **The live API returned 400, not 422, for limit violations and unknown models.** | `api.md`; probe |
| Rate limits | 100k tokens/s and 80 req/s, "adjusting dynamically … can change without notice". | `models.md` |
| Pricing | **$0.042 per million input tokens. Output tokens are free.** The probe's 4-question request used 555 input tokens, about $0.000023. | `models.md`; probe |
| Latency | 290–550 ms per call in the probe, from a laptop. | probe |
| Language | English is the primary language. Other languages "are handled but not equally well". | `models.md` |
| Known weaknesses (jev-1.13) | Literal reading, arithmetic and counting, numeric representations, indirection, distracting state, **option-order bias toward the first option**, generation. | `model-jaggedness/jev-1.13.md` |

## 2. Privacy and data flow

- **Training.** "Jev is not trained on customer requests or responses" (`models.md`). The Privacy Policy repeats that commitment.
- **Retention.** The DPA (last updated 2026-04-24) gives **no retention period**: data is kept "for as long as necessary taking into account the purpose of the Processing". Zero data retention is offered to **enterprise customers only** (`legal.md`). A default account must therefore assume that request contents are retained.
- **Subprocessors.** These are listed at `trust.typesafe.ai/subprocessors`.

What this means for tf-jev:

1. **What may be sent:** the user's natural-language request, schema symbols (type, feature and value labels), and short tf-jev-authored descriptions. Corpus *text* is not sent: structural compilation doesn't need it (AGENTS.md security rule).
2. **Every call is logged in a `Receipt`** that records the backend, the resolved model, tokens and latency. It never records the context, prompts or key.
3. **The SDK can leak data in its own error messages.** It strips secret headers and truncates error bodies to 200 characters (`MAX_ERROR_BODY_LENGTH`), but a 4xx body can echo request content. The adapter (#8) must not log SDK exception text verbatim when the request contained user content. It should log the status, the request id and the error class instead.

## 3. Existing Python clients

| Candidate | Status (2026-10-11) | Assessment |
|---|---|---|
| **`typesafe-sdk` 0.7.4** (official, `typesafe-ai/typesafe-sdk-python`, MIT) | Released 2026-10-09. Typed (`py.typed`), Python ≥3.10. Dependencies: `httpx2`, `pydantic` 2, `tenacity`, `truststore`. | Owns everything we would otherwise rebuild: auth (`TYPESAFE_API_KEY`), base URL and model defaults, retries with exponential backoff that honor `retry-after`, a typed exception hierarchy, pydantic response decoding, and secret-header redaction. |
| `docxology/daf-jev` 0.7.2 (MIT, single author, 7★) | Not on PyPI. Its own `httpx` transport, separate from the official SDK. A large surface: benchmarks, Bayesian graphs, MCP server, figures. | Its contract is stringly typed (`DecisionPrediction.type: str`, `value: str | float`, `DecisionRequest.state: Any`, `settings: Mapping[str, Any]`). It duplicates the official transport, and depending on it would pull in an unrelated research stack. Two ideas worth borrowing: a per-call **receipt** (resolved model, tokens, latency, request hash), and declared **capabilities** (`max_options`, `max_score_levels`). |
| `typesafe-ai` 0.1.0 | Re-export shim for `typesafe-sdk`. | Nothing to add. |
| `jev` 0.3.0 | A decorator that compiles functions into Jev queries. Python ≥3.14. | Out of scope, and its Python requirement is incompatible. |
| `pydantic-ai[typesafe]` | Agent-framework integration. | Far too heavy for one bounded call. |

### Gaps in the official SDK that tf-jev must cover (checked in source)

1. **No client-side limits.** It only checks that options are non-empty (`questions.py`). The 255-option and 10-level limits are enforced only by the server, which costs a round trip.
2. **Response consistency is not checked against the request.** The SDK doesn't verify that `choice` is one of the requested labels, that `probabilities` cover exactly the requested labels, or that every question has an answer: `SystemOneResponse.answers` defaults to `{}`. Answer types it doesn't recognize are **dropped with only a log warning** (`response_types.py`). The question is then silently missing.
3. **Empty and whitespace labels are accepted by the API,** and the probe saw an empty label actually win. tf-jev must reject them before sending.

None of these is a transport defect. They belong at tf-jev's own boundary.

## 4. Dependency decision

**Wrap the official `typesafe-sdk` behind a thin adapter (#8). Do not depend on `daf-jev`. Do not write a custom HTTP client.**

- Add `typesafe-sdk>=0.7.4,<0.8` as an **optional extra** (`tf-jev[jev]`). The schema, IR and compiler layers stay importable without it.
- The adapter maps `DecisionRequest` to `Choice`/`Noul`, and maps `SystemOneResponse.answers` to `RawChoice`/`RawBinary`. Everything else is `validate_answers`.
- **Credentials.** The adapter takes an explicit `api_key`. When none is given, it reads `JEV_API_KEY` (this project's `.env` convention) and then the SDK's own `TYPESAFE_API_KEY`. The key is never stored on result objects or printed in a `repr`.
- **Model.** Pin `jev-1.13.0` by default rather than `jev-latest`, so confidence thresholds tuned during evaluation (#11) don't drift silently. Record `response.model` in every receipt.
- **Retries and timeouts** are owned by the SDK's `RetryPolicy`. tf-jev only normalizes the SDK's exceptions into its own backend-error category (design.md error policy).

No live-API test runs in CI. The live probe becomes an opt-in test in #8, gated on an environment variable, and never needs a secret in CI.

## 5. Backend-neutral contract (`src/tf_jev/decisions.py`)

The contract is implemented and covered by RED-first tests in `tests/test_decisions.py`:

- **Questions:** `ChoiceQuestion(prompt, options: tuple[Option, ...])` and `BinaryQuestion(prompt)`. Option labels are opaque ids that tf-jev chooses. They must be non-empty, contain no control characters, and be unique. Score is deliberately left out: no parser decision needs an ordinal rubric yet, and Jev's own docs advise against using score magnitudes numerically.
- **Requests:** `DecisionRequest(context: Mapping[str, str], questions: Mapping[str, Question])`.
- **Backends:** `DecisionBackend` is a protocol with `capabilities` and `decide(request) -> DecisionBatch(decisions, receipt)`. `check_capabilities` enforces `max_options` and `max_questions` **before** any call.
- **The boundary:** `validate_answers(request, raw)` rejects any of these:
  - missing or unrequested answers;
  - a mismatched answer kind;
  - a selected label that wasn't requested;
  - a probability set that doesn't match the requested labels;
  - a non-finite or out-of-range probability;
  - sums off by more than the rounding tolerance;
  - a selection that isn't a highest-probability option.

  Because of this, **no backend can return text that wasn't in the request**, and query syntax can never come from a model.
- **Confidence is computed locally**, so Jev and baseline backends (#12) are compared on one scale:
  - `ChoiceDecision.confidence` uses Jev's documented Choice formula;
  - `top_probability` and `margin` (top minus runner-up) are also exposed, as `confidence.md` recommends;
  - `BinaryDecision.confidence = |2p − 1|`.
- **Testing:** `ScriptedBackend` is the deterministic fake for TDD. It runs the same capability check and validation as a real backend.

## 6. Design consequences for the parser (#9) and retrieval (#7)

- **Two-decimal probabilities** make tail ranking among many options meaningless, and confidence is quantized. Use hierarchical or narrowed choices (#7) to keep candidate sets small. Gate on `margin` as well as `confidence`.
- **Option-order bias.** For structural decisions, where a wrong answer gives a plausible but wrong query, ask the question a second time with the options in reverse order (a second question in the same call costs nothing extra in latency). Abstain if the two answers disagree.
- **Numbers** (the `k` in `<k:`, integer feature bounds): extract them deterministically from the request text. Use Jev only to decide which role a number plays. The jaggedness doc explicitly advises keeping arithmetic and numeric comparison in code.
- **Noul answers near 0.5 are uninformative.** The probe gave 0.45 for "Does the request exclude something?" on a request with no negation. Treat a band around 0.5 as abstention, not as a weak yes or no.
- **Batching.** One call per request, with all independent questions packed together, fits easily in the context budget. Dependent decisions, such as choosing a feature value after choosing the feature, need a second round trip, at roughly 0.3–0.5 s each.
