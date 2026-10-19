# Research: TF evidence version versus supported runtime (#45)

2026-10-20. Read #45, the #44 dependency-failure review, current dependency/CI,
benchmark verification, schema identity and synthetic live/diagnostic fixtures.
No overlap with an open implementation PR. Main is synced after #47.

Authoritative upstream comparison:
https://github.com/annotation/text-fabric/compare/v13.1.0...v13.1.1
Pinned refs: 13.1.0 `dd227ce62b5536de53a0e20eac98c0459da8fd3d`,
13.1.1 `5473037f4e91e0d7e108119cbe12aa908b72c617`.
Actual Python changes are version metadata plus two defensive structure fixes:
`core.prepare.structure` returns six Nones on invalid configuration (matching its
normal six-field result), and `core.text.nodeFromHeading` returns None after an
unconfigured-structure warning. No search engine, node/edge feature, or native
query grammar source changed. This warrants compatibility testing, not assuming
semantic incompatibility from fixture failures.

A separate /tmp Python 3.12 environment installs real TF 13.1.1, SDK 0.7.5 and
current dev tools; project .venv remains TF 13.1.0 / SDK 0.7.4. Current ordinary
tests wrongly hard-code 13.1.0 into a synthetic corpus fixture and schema version
assertion, conflating a package runtime identity with the canonical frozen BHSA
benchmark. Source-drift unit tests must isolate source validation from version
rejection, while a separate adversarial test preserves wrong-version rejection
BEFORE source access/model initialization. Canonical benchmark/version/source
validation and all published reports remain unchanged.
