# Design: borrow already-loaded authoritative otype map (#20)

In `_extract`, use `node_types = api.F.otype.data` instead of `dict(api.F.otype.items())`. The pinned TF 13.1.0 implementation makes these exactly the same contents; `.data` is loaded in the TF core API. The extractor uses it only as an ephemeral mapping, never stores it on the returned immutable `CorpusSchema`. Preserve all existing type interval/count checks, effective loaded-data SHA records, feature/edge validations, and snapshot/source identity. Never assume insertion order: `sorted(node_types.items())` remains unchanged.

Regression (RED before production): full extraction of a real saved tiny TF corpus after disallowing `F.otype.items()`; verify exact schema digest, immutable JSON, native compiled `word sp=verb` tuples, and full vs selected identity. The pre-change implementation must raise on the disabled access; the new implementation cannot read it. Existing sparse/unicode/overlay tests still guard semantics.

Pinned BHSA 2021 workflow must confirm the historical full SHA and complete selected native tuple oracle and report actual full schema extraction CPU seconds and process RSS for this change; do not use fixed noisy runtime thresholds. Note that the original TF session still holds the `otype` mapping, so this saves only a redundant copy. No changes to the public API, compiler, parser or package dependencies.

Merge only after exact-head Python 3.11–3.13 quality and distribution, real pinned BHSA full/selected profiling and broad native replay (when affected), plus fresh logically independent adversarial review. Keep #20 open for further material memory optimization unless the measured gain and remaining work justify closure.
