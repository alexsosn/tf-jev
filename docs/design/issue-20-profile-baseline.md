# Design: reproducible, nonintrusive schema baseline (#20)

Provide `profile_schema(directory: Path, *, trace_python: bool = False) -> dict[str, object]`, returning valid JSON-compatible metadata and separate load/extraction measurements. CLI: `python -m scripts.profile_schema <local-tf-directory> [--output report.json] [--trace-python]`. No mutation, cache writes outside TF itself, model calls, network access or raw corpus value export.

**Schema identity:** Use the existing `CorpusSchema.identity.loaded_sha256` and `tf_version`; corpus dataset/version may be published. Report # of admissible node/edge features, object types and `identity.key` to enable provenance comparison; do not echo user paths.

**Resource measurements:** Capture process current RSS using Linux `/proc/self/status`, total process peak RSS via `resource.getrusage(RUSAGE_SELF)` with documented Linux KiB units (platform-dependent other OS => null), and elapsed seconds from monotonic `time.perf_counter`. The difference in process RSS across phases is *not* an allocation count. Optional `tracemalloc` captures Python allocations across extraction but changes memory/time behavior; annotate tracing status in JSON. One session per invocation; repeat across fresh processes to compare distributions rather than treating warm sequential extractions as independent cold runs.

**Tests first:** Use the tiny real TF test harness and a temporary corpus directory. Require nonnegative load/extract seconds, distinct stage boundaries, consistent counts/digests, valid serialized JSON, no location path in report. Validate errors on missing/malformed source directories, no misleading report files on failure. Require no extra TF dependency changes and strict Python matrix. A separate pinned BHSA Actions job will run exactly this command, archive counts-only report, and show actual trace-free baseline.

**Non-goals:** no change to `extract_schema()`, no performance improvement claim/issue closure in this PR; after measurement, profile and optimize effective loaded hashing, duplicated sorting, object type tables and retained inventories with RED-first correctness checks.
