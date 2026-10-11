# Issue #10 development record: complete benchmark v2

- Read mandatory entry docs and issue #10/#9; no active overlapping PR.
- Researched loaded BHSA 2021 annotations, native diagnostics, output witnesses,
  official feature meanings and source licensing before implementation.
- Persisted research/design, then wrote deterministic tests. Observed RED:
  `ModuleNotFoundError: scripts.bhsa_benchmark` (the initial local module name).
- Implemented model-free trusted-gold runner. Focused real tiny-TF tests passed.
- Two additional RED tests found list-valued classifications escaping as TypeError;
  strict text validation fixed them. Another RED exposed invalid projection on an
  empty result. Extended the shared native harness with executor arity, then
  validated projection even when there are zero rows. All focused tests GREEN.
- On the user's request to sync, fetched remote. Main had advanced through #23–#27
  to `1fd1993`; fast-forwarded before finalizing. Re-read new docs and all five
  PR/review discussions. Reconciled into a complete v2, with frozen v1 retained
  as history and all five original evaluation requests still held out.
- Authored 109 cases: 86 supported, 11 ambiguous, 12 unsupported. Every supported
  native gold was executed against actual local BHSA 2021. Initial independent
  raw feature/slot/edge oracle check matched all 86 frozen signatures/counts;
  repeat the independent audit on the exact final head before merge.
- Runner reuses native diagnostic-aware conformance execution, with no model,
  no compiler heuristic and no gold regeneration path. Dedicated pinned BHSA CI
  verifies both v2 partitions alongside the unchanged v1/native tutorial replay.
- Final merge gates: exact-head Ruff/mypy/full tests including opt-in BHSA,
  standard CI Python 3.11–3.13 and wheel, exact-head pinned native CI, then a
  logically independent adversarial code/data review recorded on the PR.

No parser or model accuracy is claimed. Literal high-cardinality lookup cases
measure explicitly named annotations; translation/general semantic retrieval
quality remains for parser/evaluation research. The public heldout is procedural,
not secret, and must be replaced/versioned after tuning informed by its results.
