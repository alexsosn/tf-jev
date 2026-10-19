# Compatibility verification record (#45)

Research/design committed first (`12f2b31`). Upstream tag/AST comparison identifies
only version metadata and two defensive structure paths; search ASTs are unchanged.

Observed RED on actual 13.1.1 before corrections: 7 failed, 550 passed, 41 skipped
in 21.81 s. Failures were hard-coded synthetic fixture/version expectations.
Runtime-aware tiny fixtures and isolated source-boundary tests then passed:
60 passed, 2 opt-in skips in the affected group. Full offline suites on the
implementation tree: 559 passed, 41 skipped on both TF 13.1.0 and 13.1.1.
Ruff/mypy pass, including the latest-supported CI lane.

Adversarial tests preserve canonical rejection BEFORE source reads or model
import when TF is 13.1.1. An actual-runtime canonical CLI invocation (no mocks)
also rejects 13.1.1 before model setup and writes no output. It makes no paid call.
Published benchmark/report files and production source remain unchanged.

Final exact-head both-runtime suites, real BHSA conformance/full-schema/native
query on 13.1.1, pinned native replay, latest/pinned Python matrix and wheel CI,
and logically independent review are recorded on PR #49 before merge. The added
floating lane detects future changes; compatibility with every future release
is not asserted.
