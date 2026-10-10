# CorpusSchema extraction contract (#5)

Research and design, 2026-10-11; follows #4 and the compiler's SymbolSchema.
Authority inspected: Text-Fabric 13.1.0 `FabricCore._makeIndex`, `explore`,
`load`, `Data.load`, `OtypeFeature.items`, `OslotsFeature.items` and feature APIs.

## Findings refining #4

- Fabric scans each location/module pair in order; the last file with a given
  feature name wins. Identity must cover those directories in that order.
- TF binary/data caching is mtime-based, and callers can mutate loaded feature
  dictionaries. A source-file digest alone cannot identify the actual memory
  snapshot. Identity therefore includes a digest over the effective loaded
  warp, node/edge data, feature metadata and object type order, in addition to
  per-directory file content digests. This also catches node-value permutations
  that leave domain counts unchanged. No mtime is a correctness key.
- An integer min/max range is not evidence of membership (sparse integers are
  common). IntRange stays the public summary; exact observed membership is
  retained locally and required for literal equality/exclusion validation.
  Compiler comparison thresholds remain ordinary integers, not domain members.
- Native absence is meaningful even on types where a feature is entirely
  missing. Each feature gets a domain for every type; empty IntRange endpoints
  are None, and empty string domains have no values. Presence/absence can use
  these features, but no literal can pass membership validation there.

## API and immutability

`extract_schema(api) -> CorpusSchema` accepts a loaded TF core API. It explores
metadata and loads every admissible query feature with add=True; this mutates
only the supplied TF session's loaded-feature inventory and never downloads.
Warp features and names outside the compiler's symbol pattern are excluded.
Raw object types are retained to reserve generated names; ObjectType has an
expressible flag. Extraction errors use SchemaError(ValueError) with generic
messages, not raw corpus values or TF exception strings.

Frozen records: CorpusIdentity (TF version, optional dataset/date/version,
ordered source locations/digests, loaded_sha256), ObjectType, NodeFeature,
EdgeFeature, ValueDomain, Enumerated, Large, IntRange. CorpusSchema exposes
object_types (name tuple for SymbolSchema), object_type_details, node_features,
edge_features, excluded_features, reserved_names, type_named_features.
Lookup helpers are object_type, node_feature, edge_feature, domain plus the
compiler's node_feature_type, validate_value and validate_edge.

ENUM_LIMIT=32 is the direct-choice threshold. Strings above it are Large with
an opaque deterministic retrieval handle tied to the full schema identity,
feature and type. Integer domains always use IntRange. Small values and counts
are sorted by exact value; Unicode is never normalized. non_nfc_count counts
distinct values. Empty strings and sentinels remain ordinary values.

Full sorted value/count inventories and exact membership are immutable local
side tables, omitted from repr and to_json. `retrieval_values(handle)` exposes
only a matching Large inventory, for #7's local narrowing; unknown/stale handles
fail. No backend or prompt construction exists here. to_json is a deterministic
summary with sort_keys, ensure_ascii=False and compact separators, not a model
payload or a reconstruction format (it omits the local inventories).

Extraction snapshots loaded data; subsequent session/disk mutations do not
alter the snapshot. Cache keys bind both source and loaded content. Callers
must extract anew after corpus changes; this ticket introduces no cache or
claim that an old schema automatically follows a changing session. Concurrent
mutation during extraction is unsupported; callers must keep the session and
source files stable during extraction.

## Gates and non-goals

RED-first API tests on an actual generated TF dataset cover domains per type,
empty/missing/non-NFC values, sparse integers, large handles, exact compiler
integration, identity changes, module override order, deep immutability,
deterministic JSON, excluded symbols and invalid load/node/edge data. BHSA 2021
checks measured counts, all endpoint pairs, warp exclusion and a real compiled
query. The complete relevant suite runs on a frozen head, followed by skeptical
review with raw TF data as the oracle. Normalization/retrieval ranking is #7;
edge-value predicates, schema reconstruction and model data flow are deferred.

## Development evidence

Initial RED: `.venv/bin/python -m pytest -q tests/test_schema.py` failed
collection with `ModuleNotFoundError: No module named 'tf_jev.schema'` before
production implementation. A later immutability attack produced RED for
mutable feature-description metadata; text fields now require actual strings.
TF reloads otext configuration during loading, so a mutated pre-load dataset
field is not evidence of the effective configuration; the regression exercises
node and edge descriptions that survive loading.

Focused BHSA 2021 verification passed (10 tests including the real corpus;
81.37 s on this machine). Full schema extraction loads all admissible features
and hashes their actual per-node/edge content; this is a deliberate one-time
cost, not a compile operation. Performance optimization must preserve exact
identity and domain semantics. Final checks/review are recorded on the PR at
the exact head, rather than updating verification prose after freezing it.

## Review amendment: native type intervals

Adversarial review of 2614e36 used an actual corpus with clause nodes
10, 14 and 15. TF loaded it, but `word`-style type selection through
F.otype.s uses the min/max interval: `clause` returned 10 through 15, including
phrase nodes. Merely checking that raw types and C.levels agree is insufficient.
The regression first demonstrated this native mismatch, then failed because
extraction did not raise. Extraction must verify each sInterval is exactly the
raw type extent, with no gaps/foreign nodes, before certifying domains. The old
review is invalidated; the fix receives full tests and independent re-review.
