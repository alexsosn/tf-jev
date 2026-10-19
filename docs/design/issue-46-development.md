# Development gates and diagnosis record (#46)

- Research/protocol `4be61bc`, then committed missing-module RED `47585ee`.
- Trace equality/native tiny execution, explicit stage/probability diagnostics,
  failed usage/disclosure, malformed labels and batched usage tests GREEN.
- Saved real tiny-corpus CLI observed RED: mixed accepted/stopped outcomes caused
  JSON key sorting of None versus str. Fix serializes an explicit non-decision
  marker; native integration GREEN.
- Every probe variant tested via real SDK/MockTransport, including five-question
  usage accounting. Focused GREEN: 19 tests. Full suite: 556 passed, 41 skipped;
  Ruff/mypy and Python 3.11–3.13/wheel CI passed on frozen source `df65c44`.
- Full 52-request development trace plus fixed 96 probes completed once. No
  heldout calls, parser tuning or model version changes. All 116 sources and full
  schema key match the original study. Original artifacts remain byte-identical.
- Later adversarial instrumentation review: observed RED for a shape decision
  followed by a type timeout; last validated stage was lost. Fix preserves last
  observed versus last attempted question, without treating an error as a model
  decision. Focused GREEN: 20. Does not change the measured distributions.
- Native type inventory confirms word at index 12/13; all 11 type-stage winners
  are word. Six supported first-per-family native development gold queries
  replay with frozen counts/signatures. No old gold is rewritten.
- Diagnosis and probe limits in `reports/abstention-diagnosis-2026-10-20/README.md`.
  No bounded production change is justified yet; corpus-aware planning design,
  development calibration and fresh untouched evaluation are #48.
- Final exact-head tests, public artifact recomputation/disclosure audit and
  logically independent adversarial review are recorded on PR #47 before merge.
