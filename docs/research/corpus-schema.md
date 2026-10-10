# Corpus schema and feature-value discovery

Research for issue #4, done 2026-10-11.

- **Text-Fabric:** `text-fabric==13.1.0`.
- **Real corpus:** BHSA **2021**, the `ETCBC/bhsa` v1.8.1 release.
- **Executable evidence:**
  - [`scripts/probe_corpus_schema.py`](../../scripts/probe_corpus_schema.py) is a generic probe that works on any TF dataset. Its full BHSA output is [`data/bhsa-2021-schema-probe.md`](data/bhsa-2021-schema-probe.md).
  - [`tests/research/test_schema_discovery.py`](../../tests/research/test_schema_discovery.py) runs in CI on the synthetic fixture.
  - [`tests/research/test_bhsa_schema.py`](../../tests/research/test_bhsa_schema.py) is opt-in via `TF_JEV_BHSA_DIR`.

No production schema API is frozen here. §6 proposes the `CorpusSchema` contract that #5 will implement.

## 1. Discovery APIs and their cost

| Step | API | BHSA 2021 cost | Notes |
|---|---|---|---|
| open | `Fabric(locations=dir)` then `TF.load("")` | ~4.5 s (cached binaries) | Loads `otype`, `oslots` and every feature `otext` references (section and text-format features). In the fixture that means `lex` and `number`. |
| enumerate | `TF.explore(show=True)` | **0.04 s** | Public. Loads **metadata only** for every feature and returns `{nodes, edges, configs, computeds}`. |
| feature metadata | `TF.features[f].metaData`, `.dataType` (`str`/`int`), `.isEdge`, `.edgeValues` | free after `explore` | **Before `explore`, a feature that isn't loaded has empty metadata and `isEdge is None`** (pinned by a test). |
| object types | `api.C.levels.data` | free | Ordered from largest to slot level, with average sizes. |
| type extent | `F.otype.sInterval(t)` | free | Each type occupies one contiguous node range (verified node by node on BHSA in review). |
| value domain | `api.Fs(f).freqList(nodeTypes={t})` | 0.1–0.15 s per feature | Public. Returns `(value, count)` sorted by frequency. Needs the feature data loaded. |
| load data | `TF.load(names, add=True)` | ~0.04 s per typical feature; 8.1 s for all 111 non-`omap` features; `omap@*` alone 5.5 s | |
| edge structure | `api.Es(e).data` | free once loaded | Source → targets (with values when `edgeValues`). |

**Recommended extraction:**

1. `load("")`, then `explore()`, which gives every name, kind and type for 125 features.
2. Load only the features whose domains are needed.
3. Never load `omap@*`. These are version-mapping edges, unusable in queries, and they cost 5.5 s.

## 2. Measured cardinalities

Value domains **must be measured per (feature, object type)**. Several features span types with very different domains:

- `typ`: 42 values on `clause`, 43 on `clause_atom`, 13 on `phrase` and on `phrase_atom`.
- `number`: 9 values on `phrase`, 31 on `clause`, 29,736 on `word`.
- `sp` and `lex` are defined on both `word` and `lex` nodes.

The full table has 146 (feature, type) pairs; see the probe output. Representative rows:

| feature | type | dtype | distinct | note |
|---|---|---|---:|---|
| `gn` | word | str | 4 | includes `NA`, `unknown` |
| `nu` | word | str | 5 | |
| `vt` | word | str | 9 | |
| `sp` | word, lex | str | 14 | |
| `vs` | word | str | 26 | |
| `function` | phrase | str | 29 | |
| `typ` | clause | str | 42 | |
| `rela` | clause / phrase | str | 13 / 3 | |
| `nametype` | word | str | 10 | **no value on 391,084 of 426,590 words** |
| `root` | word | str | 757 | no value on 354,539 words |
| `gloss` | word, lex | str | 6,132 | English. 1,972 values contain spaces |
| `lex` | word, lex | str | 8,769 | |
| `voc_lex_utf8` | word, lex | str | 8,091 | 3,287 values are not NFC |
| `g_word_utf8` | word | str | 92,474 | 50,369 not NFC; 6,488 are the empty string |
| `number` | word | int | 29,736 | |
| `chapter` | chapter, verse | int | 150 | range 1–150 |
| `dist` | clause | int | 39 | range −120…8 |

**Bucket summary over all 146 pairs:**

| distinct values | str | int | Consequence for bounded choice (see §4) |
|---|---:|---:|---|
| 1–8 | 31 | 0 | direct Choice |
| 9–32 | 22 | 6 | direct Choice |
| 33–255 | 43 | 5 | narrow to ≤ 32 first (rounding, order bias); never one wide Choice |
| 256–2,000 | 6 | 9 | retrieval required |
| >2,000 | 20 | 4 | retrieval required |

## 3. Value representation findings

- **Two kinds of "missing".**
  1. *No value*: the node isn't in the feature's data at all (`nametype`, `root`). It is matched by `f#` and excluded by `f`.
  2. *Sentinel strings*: `NA`, `unknown`, `absent`, `n/a` and `<unknown>` are ordinary values (`gn`, `nu`, `ps`, `vt`, `vs`, `st`, `prs`, `pfm`, `rela`, `det`, `root`, `gloss`). For these, `f#` matches **nothing**. Example: `word prs#` returns 0 because "no suffix" is `absent`.

  What a sentinel means is a **corpus convention**. The generic schema must keep sentinels as ordinary values. Interpreting them, for example mapping "has no suffix" to `prs=absent`, belongs in a BHSA-specific description layer that is kept apart from the generic code.
- **The empty string is a real and frequent value.** It covers 28 (feature, word) pairs: `nme` 121,983, `g_pfm` 381,594, `pfm` 11,438, `g_word_utf8` 6,488, and others. A bare `f=` is a syntax error and `f#` means "no value", but **the empty string is an ordinary member of a value set: `f=|` is `{""}`**, because TF splits values on `|`. On BHSA, `nme=|` matches the same 121,983 words as `nme~^$`, `nme=|H` matches 130,917 (121,983 + 8,934), and `nme#|` matches 304,607. Note that `f#|` excludes the empty string but still matches nodes that have *no* value. So the empty string fits the existing `=`/`#` value-set grammar, and it can be merged with other values under #2 invariant 8 (one condition per feature). **No regex amendment is needed.** A regex would actually be worse: the two constant regexes would collide under the last-condition-wins rule, and Python's `$` also matches before a trailing newline. (An earlier draft of this PR proposed `~^$`/`~.`; that was wrong, and adversarial review caught it.)
- **Values that need escaping** (space, `|`, `\`): `label` (21,054 values), `gloss` (1,972), `voc_lex_utf8` (440), `lex_utf8` (438, multi-word place names such as `אבל בית מעכה`), `g_word_utf8` (305). The escaping from #2 §2.3 covers all of them. No control characters were found apart from the empty string.
- **Non-NFC values are common** in pointed Hebrew (`g_*_utf8`, `voc_lex_utf8`, `qere_utf8`, `kq_hybrid_utf8`, and two `book@fa` names). Values must be kept and compiled **byte-for-byte**. They can never be decision labels (#6: labels are ids; values go in descriptions and in an id → value table).
- **Integers** are true `int`s, negative ones included (`dist`). They have small value sets but meaningful *ranges*: a domain is better described by min, max and count than by an enumeration.

## 4. Bounded-choice policy (proposed thresholds)

These combine the #6 findings with the measurements above. Jev limits Choice to 255 options, rounds probabilities to 2 decimals, and has a known first-option bias.

- **≤ 32 values**: offer the whole domain in one Choice. This covers 53 of 146 pairs, including every core morphology feature.
- **33–255 values**: always narrow to ≤ 32 before the model decides, either with a deterministic prefilter (type or category, or a match on the request text) or with a hierarchical Choice. A single wide Choice is never used. With 2-decimal probabilities, the tail of a large choice is all `0.0`.
- **> 255 values**: deterministic retrieval (#7) must narrow the domain to at most 32 candidates before any model call. This is mandatory for the string features `lex`, `voc_lex*`, `gloss`, `g_word*`, `root`, `label` and `pargr`.
- **Integer features are always `IntRange`, whatever their cardinality** (e.g. `number` on words, with 29,736 values). The number is extracted from the request deterministically (#6: no arithmetic in the model), and the schema's min, max and count validate the extracted literal. Retrieval never applies to integers.

The thresholds are policy constants for #5 and #7, not facts about Text-Fabric.

## 5. Corpus and version identity

| Component | Source | Purpose |
|---|---|---|
| text-fabric version | `importlib.metadata.version("text-fabric")` | Parser behaviour (conformance suite) |
| dataset id | `otext` metadata `dataset` (`BHSA`) and the directory name (`2021`) | Readable identity |
| written date | `otext` `@dateWritten` (`2021-12-09T14:23:29Z`) | Readable identity |
| release marker | `__checkout__.txt` (`v1.8.1`, `gb112c16…`), present only when TF downloaded the data | Provenance, when available |
| **content digest** | per location: SHA-256 over the length-prefixed name and content of every `*.tf` file, sorted by name. Subdirectories (TF's `.tf` cache) are skipped; hidden `*.tf` files are included, as TF's own discovery does | **The cache key.** A corpus loaded from several locations (base data plus feature modules) is identified by the **ordered tuple of (location, digest)** (`corpus_identity`). BHSA 2021: `226a3ce7…11d0`, 173 MB in about 0.55 s. Pinned by a test. |

A digest over file headers only takes 5 ms, but it misses changes to the data, so it is rejected as a cache key. The full digest is cheap enough to compute once per `CorpusSchema` extraction.

## 6. Proposed `CorpusSchema` contract (for #5)

The schema is an immutable, deterministic, serializable snapshot. Every collection is sorted, so two extractions of the same corpus produce byte-identical JSON.

```text
CorpusSchema
  identity: CorpusIdentity(dataset, version_dir, date_written, tf_version, content_sha256)
  object_types: tuple[ObjectType]                 # in C.levels order
      ObjectType(name, slot: bool)
  node_features: tuple[NodeFeature]               # sorted by name
      NodeFeature(name, dtype: "str"|"int", description: str | None,
                  domains: tuple[ValueDomain])     # one per object type carrying it
  edge_features: tuple[EdgeFeature]               # omap@*, oslots excluded
      EdgeFeature(name, has_values: bool, description,
                  endpoints: tuple[(from_type, to_type, count)])   # all pairs, never truncated
                  # edge-value domains: out of scope (edge values are deferred in #2)
  ValueDomain(object_type, node_count, missing_count,
              kind: Enumerated(values: tuple[(value, count)])        # str, ≤ ENUM_LIMIT
                  | Large(distinct, retrieval_handle)               # str, > ENUM_LIMIT, via #7
                  | IntRange(min, max, distinct),                  # every int feature
              has_empty_string: bool, non_nfc_count: int)
  reserved_names: frozenset[str]                  # object types (and sets): never node names (#2 inv. 2)
  type_named_features: frozenset[str]             # features sharing a type name (BHSA: book,
                                                  #   chapter, lex, verse): never bare first token
                                                  #   on a continuation line (#2 inv. 7)
```

Determinism rules:

- `Enumerated.values` is sorted by **value**, ascending by code point. It is not sorted by frequency (`freqList` order), so ties can't depend on counts.
- `IntRange` holds only integers.
- Everything is serialized as JSON with `sort_keys=True`, `ensure_ascii=False` and `separators=(",", ":")`, with values written byte-for-byte. Byte-identical output is then part of the #5 tests.

Validation helpers for #5:

- `node_feature(name, object_type)`, `edge_feature(name)` and `object_type(name)` raise a schema error for unknown or outdated symbols. This is the "invalid symbols fail before compilation" acceptance criterion.
- `domain(feature, object_type)` gives per-type value checks. The check is exact for `Enumerated` domains, a range check for `IntRange`, and a retrieval lookup for `Large`.
- Expressibility flags reuse the #2 invariants: feature names must match `[A-Za-z0-9_][A-Za-z0-9_@-]*`, and `otype`, `oslots` and `omap@*` are excluded.

**Explicitly not in the schema:** BHSA names, sentinel semantics, glosses used as labels, prompts. Corpus-specific interpretation lives in a separate, optional description layer.

## 7. Privacy and data flow

What the model can see during parsing:

| Data | Sent? | Notes |
|---|---|---|
| the user's request | yes | the request context |
| object type and feature names | yes | as option *descriptions*; labels are ids |
| feature `description` metadata | yes, as descriptions | short, written by the corpus authors |
| enumerated values (≤ 32, or narrowed ≤ 255) | yes | grammatical codes such as `verb` or `f` |
| high-cardinality values | **only the ≤ 32 retrieval candidates** | these can be corpus text (`g_word_utf8` word forms, `gloss`, `label` such as `GEN 01,01`); never the whole vocabulary |
| corpus running text, node numbers, counts | **no** | structural compilation never needs them |
| content digest and identity | no | local only |

Under the default TypeSafe account terms (#6), retention is unspecified and zero data retention is enterprise-only. Retrieval candidates are the one place where verbatim corpus content leaves the machine. The parser (#9) should record which candidate values were sent, in its receipt, for audit.

## 8. Follow-ups

- **#5** implements §6 on the fixture and BHSA. Thresholds (§4) and exclusions (§1) are constants with tests.
- **#7** owns `Large` domains, retrieval handles, and normalization (e.g. NFC or dediacritized matching keys mapped back to the exact original bytes).
- **#3** (compiler) gets two inputs from here: the empty string as a value-set member (`f=|…`, §3), and the two ways a value can be missing (no value is matched by `f#`; sentinels are ordinary values).
