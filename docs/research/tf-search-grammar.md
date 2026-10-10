# Text-Fabric search grammar and validation surface

Research for issue #2. Researched 2026-10-10.

- **Text-Fabric:** `text-fabric==13.1.0` (the version resolved by `text-fabric>=13.1,<14`).
- **Real corpus:** BHSA data version **2021**, the latest. It ships in `ETCBC/bhsa` release v1.8.1 (2023-10-28), with `otext.tf` `@dateWritten=2021-12-09`.
- **Evidence:** every claim below is backed by an executable test:
  - [`tests/conformance/test_tf_search_grammar.py`](../../tests/conformance/test_tf_search_grammar.py) runs in CI on a tiny synthetic corpus.
  - [`tests/conformance/test_tf_search_grammar_bhsa.py`](../../tests/conformance/test_tf_search_grammar_bhsa.py) runs on BHSA 2021 and is opt-in through `TF_JEV_BHSA_DIR`.
- **Sources:** code references are to the installed `tf` package. The narrative docs (`tf.about.searchusage`) are not shipped in the wheel. The parser code is the authority here.

## 1. Pipeline inside Text-Fabric

`S.search(template)` builds `tf.search.searchexe.SearchExe` and runs these stages:

| Stage | Code | Rejects |
|---|---|---|
| syntax / tokenize | `search/syntax.py` `_tokenize`, `parseLine`, `parseFeatureVals` | unrecognized lines, illegal names, malformed feature conditions, non-numeric limits, bad regexes, quantifier structure |
| semantics / grammar | `search/semantics.py` `_grammar` | indentation errors, lonely relations, relations on undefined names |
| semantics / validation | `search/semantics.py` `_validation` | unknown object types, missing node/edge features, value-type mismatches, unknown relations, values on valueless edges |
| connectedness | `search/graph.py` `connectedness` | empty templates, disconnected query graphs |
| spin atoms | `search/spin.py` `spinAtoms` → `_doQuantifier` | **quantifier bodies are only parsed here** |
| stitch / fetch | `search/stitch.py`, `searchexe.fetch` | result-limit overflow ("cut off at N results") |

## 2. Template grammar (13.1.0)

A template is a sequence of lines (`\n`-separated). Blank lines are ignored, and so are lines whose first non-blank character is `%` (comments).

### 2.1 Atom lines

```
[indent][op ]name:otype [feature-conditions...]
[indent][op ]otype [feature-conditions...]
```

- **`otype`** is a corpus object type, or a named set when `sets=` is passed, or `.` for "any type". Matching is case-sensitive (`Word` is rejected).
- **`name`** must match `[A-Za-z0-9_.-]+`; other names fail with `Illegal name`. The value `..` is reserved as the parent reference inside quantifiers.
- **Name/type shadowing.** If an atom's `otype` equals the name of a previously named node, TF resolves it as a reference to that node. It does **not** treat it as the object type, and the query stays valid. Test: `test_node_name_equal_to_an_otype_silently_shadows_that_otype`. ⇒ Generated names must be disjoint from every object type and set name.
- **Indentation** expresses embedding: a deeper-indented atom gets an implicit `child ]] parent` edge. Outdenting must return to a previously used indent level.
- **Optional `op` prefix** (`<: word`) relates the *previous sibling atom* to this one.

### 2.2 Node-feature conditions

Conditions are separated by whitespace. They appear either on the atom line or on following lines that contain only conditions. Feature names match `[a-zA-Z0-9-@_]+` and are case-sensitive.

| Form | Meaning | Type constraints |
|---|---|---|
| `f=v` | value equals `v` | int features: `v` must be an integer literal |
| `f=v1\|v2` | value in set | same |
| `f#v`, `f#v1\|v2` | value not in set (nodes without a value **match**) | same |
| `f` | has a value | — |
| `f#` | has no value | — |
| `f*` | no constraint (loads the feature) | — |
| `f>n`, `f<n` | strict integer comparison; `n` matches `-?[0-9]+` | rejected on str features |
| `f~re` | Python `re.search` on the value | rejected on int features |

Additional points:

- **Unknown values are not errors.** `sp=nonesuch` parses and returns 0 results. Value validity must be checked against the corpus schema (#4 and #5).
- **Corpus conventions are data, not grammar.** In BHSA, `prs#` returns 0, because "no suffix" is the literal string value `absent`.

### 2.3 Value escaping (the critical part)

`_esc` maps exactly six two-character sequences to sentinels `chr(0)`…`chr(5)` before any matching. `_unesc` maps them back to their **second character**:

| Written | Value char | Note |
|---|---|---|
| `\\` | `\` | |
| `\ ` | space | an unescaped space ends the condition (`lex=a b` → `Missing feature "b"`) |
| `\|` | `\|` | an unescaped `\|` means alternation |
| `\=` | `=` | optional: `=` inside a value is already literal |
| `\t` | **`t`** | not a tab |
| `\n` | **`n`** | not a newline |

Consequences, all tested:

- A lone backslash not followed by one of these characters is literal (`a\b` matches `a\b`).
- `#`, `<`, `>`, `/`, `~`, `%` and `:` are literal inside a value after the operator.
- **Inexpressible as equality values:** the empty string, any value containing tab or newline, and any value containing `chr(0)`–`chr(5)`, which collide with the escape sentinels.
- Unicode values work verbatim (BHSA `g_word_utf8`, Hebrew in the fixture).
- Inside `~` regexes, `\|` and `\=` stay backslash-escaped (`inRe=True`). The other four escapes behave as above.

The canonical escaping for a compiler is: backslash → `\\`, then space → `\ `, then `|` → `\|`. Values containing a C0 control character (U+0000–U+001F) are rejected, as is the empty value. The other three escapes are never emitted.

### 2.4 Relation lines and operators

A relation line has the form `name op name`, with names matching `[A-Za-z0-9_.-]+`. It may appear anywhere; TF sorts relations after atoms. The full legend (from `relationLegend`):

| Group | Operators |
|---|---|
| node identity | `=` `#` |
| canonical order | `<` `>` |
| slot sets | `==` same slots, `&&` overlap, `##` different slot sets, `\|\|` disjoint, `[[` embeds, `]]` embedded in |
| slot order | `<<` `>>` completely before/after; `<:` `:>` immediately before/after |
| boundaries | `=:` same start, `:=` same end, `::` same start and end |
| k-near | `=k:` `:k=` `:k:` `<k:` `:k>`. `k` is a gap tolerance: `<0:` returns the same rows as `<:`, and `<1:` allows one intervening slot. **`k` is unbounded**: `<99999999999999999999:` is accepted and matches every pair, even a node with itself |
| feature comparison | `.f.`, `.f=g.`, `.f#g.`, `.f<g.`, `.f>g.` (int only), `.f~re~g.` (str only). Missing values count as unequal for `#` |
| edge features | `-e>` forward, `<e-` backward, `<e>` either direction. Valued edges also accept `-e=v>`, `-e>n>`, and similar |

Additional points:

- **Direction matters and is not checked:** `w [[ c` (a word embeds a clause) is valid and returns 0.
- `oslots` and `omap` edges cannot be used, and TF does **not** reject them with a message: `a <oslots> b` **raises** `KeyError` (`relations.py` `add_V_Relations`). Feature comparisons on a feature that isn't loaded (`.lexx.`) raise `AttributeError`, and a bad regex in `.f~r~g.` raises `re.error`. Tests: `warp_edge_oslots`, `featcmp_unknown_feature`, `featcmp_bad_regex`.
- A value on an edge feature without `edgeValues` is rejected.

### 2.5 Quantifiers

A quantifier follows an atom at the same indentation and ends with `/-/`:

- `/without/ T /-/`
- `/where/ A /have/ H /-/`
- `/with/ T1 /or/ T2 … /-/`

Inside the body, `..` refers to the parent atom. Nesting is allowed. Structure errors are syntax errors (`Unterminated`, `Can not start with "/have/:"`).

`spin._doQuantifier` builds each sub-search as `cleanParent(parent line)` followed by the body lines. That construction has three consequences, all tested:

- **The body's indentation is kept.** A body line indented deeper than the quantifier keyword is a *child* of the parent, which adds an implicit `]] parent` edge. `n1:word` with an indented `w:word` body matches nothing, because a word can't embed a word, so nothing is excluded. Bodies must sit at the keyword's indentation. Test: `test_indented_quantifier_body_is_embedded_in_the_parent`.
- **The parent atom line is regenerated *unescaped* (TF-2).** `cleanParent` calls `_genLine`, and `_genLine` calls `_unesc`. So `n1:word lex=a\|b` becomes the alternation `lex=a|b` in the sub-search, and `lex=a\ b` becomes `Missing feature "b"`. The first case produces silently wrong results that no message reveals. Conditions placed on a **continuation line** under the parent are not copied into the sub-search. They still constrain the outer universe, and `/with/` intersects with that universe, so the result is correct in every branch. A continuation line must not *start* with a bare presence condition (`  gn …`), because `parseLine` tries the atom pattern first and reads it as an atom of type `gn`. The same unescaping applies to `..`-typed atom lines inside the body. Tests: `test_escaped_value_on_quantified_atom_line_is_unescaped_in_the_sub_search`, `without_canonical_escaped_parent_value`.
- **An empty body is valid.** `word /without/ /-/` excludes every node, with no message. Test: `empty_without_body_excludes_everything`.

**Invalid bodies don't fail the outer search (TF-1).** A quantifier body is parsed only during atom spinning, by a nested `SearchExe` that shares the message cache. When that parse fails, the nested search returns an empty result, and each quantifier treats the empty result as data:

| Branch | Effect of an invalid sub-template |
|---|---|
| `/without/` body | `universe − ∅`: **every** parent passes (fail-open). On BHSA a misspelled feature returns all 88,131 clauses. |
| `/where/` antecedent | the empty antecedent returns the yarn unchanged: every parent passes (fail-open) |
| `/have/` consequent | every parent that matched the antecedent is **excluded** (wrong, but not open) |
| `/with/` or `/or/` alternative | that alternative is dropped silently; the others still contribute |

In every case the outer `exe.good` stays `True`, and only the error messages reveal the problem. The message check (§3) catches all four. Tests: `test_invalid_quantifier_body_fails_open_without_message_check`, `quantifier_where_antecedent_error`, `quantifier_have_error`, `quantifier_with_bad_alternative`, and `test_bhsa_quantifier_body_error_is_reported`.

## 3. Validation surface

There are three usable entry points:

1. **`S.search(t, here=False, limit=n, _msgCache=[])`.** Returns `(results, status, html, exe)`. This is exactly how TF's own `A.search` (`tf/advanced/search.py`) calls it. It is the authoritative check, and the test harness uses it. Three rules apply:
   - **Validity = no error-flagged messages *and* no exception.** This covers the outer template and the quantifier bodies. Some invalid templates raise instead of logging (§2.4), so the call must be wrapped.
   - **Judge only after the results are consumed.** Without a `limit`, `results` is a generator. The returned `status` is computed before it runs, and the overflow error ("cut off at N results") is appended only while the generator is consumed. The harness materializes the results and then re-derives the status with `wrapMessages`. Test: `test_result_overflow_is_reported_even_without_limit`.
   - **An explicit `limit` truncates silently,** with no message. Detect overflow by asking for `limit = n + 1`. Test: `test_explicit_limit_truncates_silently`.
2. **`SearchExe(api, t, _msgCache=[])._parse(); ._prepare()`.** These are private. They run syntax, semantics and connectedness **without** spinning or fetching: about 10–40 ms on BHSA, versus 0.3–0.7 s for a `limit=10` search and up to about 40 s for an unbounded one. They do *not* validate quantifier bodies, though the bodies are available as deContexted templates on `exe.qnodes[q][3]` and could be checked recursively the same way `spin._doQuantifier` builds them.
3. **`S.study(t)`.** This spins the atoms, which costs about as much as execution, and prints messages unless silenced. It is not useful as a cheap validator.

**Parse validity ≠ cardinality.** A valid query can return 0 results (unknown values, the wrong relation direction) or explode: `phrase < phrase` on BHSA hits the fail limit (`SEARCH_FAIL_FACTOR × maxNode` = 5,787,324) and emits an **error** message ("cut off at … results") once the results are consumed. Validation must classify that message as a result-size condition, not a grammar error. The cleaner option is an explicit `limit` with an `n + 1` overflow probe.

Recommendation for #3:

- Validate compiled queries statically with (2) plus a recursive check of the quantifier bodies, treating any exception as invalid.
- Use (1) with a `limit` as the integration oracle.
- Guard the private API with these conformance tests and the existing `text-fabric<14` pin.

## 4. Prototype grammar subset

The compiler for #3 emits only the following. It covers nontrivial morphology plus relation queries, for example "feminine plural verbs immediately followed by a noun inside the same clause, in clauses without a predicate phrase".

| Construct | Canonical emitted form |
|---|---|
| atom | `nK:otype` on its own line, with **every atom named** and names generated disjoint from all object types and set names |
| equality / alternatives | `f=v`, `f=v1\|v2` (values escaped per §2.3; int features take integer literals only) |
| inequality | `f#v`, `f#v1\|v2` |
| presence / absence | `f`, `f#` |
| integer bounds | `f>n`, `f<n` (int features only) |
| embedding | explicit relation lines `a [[ b` / `a ]] b` rather than indentation |
| slot relations | `==` `&&` `\|\|` `=:` `:=` `::` |
| order | `<<` `>>` `<:` `:>` `<k:` `:k>`, where `0 ≤ k ≤ K_MAX` and the compiler fixes the bound (TF imposes none) |
| edge features | `-e>`, `<e-`, `<e>` (valueless form only) |
| negation | a single `/without/ … /-/` attached to an atom `nK:otype`. On that atom line, conditions whose rendering needs no escape stay on the atom line; conditions with escaped values go on one following **indented** continuation line, which therefore always starts with `f=`/`f#` and never with a bare `f` (a line starting with a bare name is parsed as an atom). This works around TF-2; a **non-empty** body sits at the keyword's indentation (0), so nothing is implicitly embedded; the body refers to the parent **only** through `..` in relation lines, never through a `..`-typed atom |

All atom lines sit at indent 0, followed by relation lines in a deterministic order. Only continuation lines for the conditions of a quantified atom are indented. This flat form is equivalent to the indented form (indentation only adds `]]` edges) and avoids the outdent rules entirely.

### Deferred (explicit)

| Construct | Reason |
|---|---|
| `~` regex conditions | a regex is free-form syntax a model must not author; revisit only as a retrieval-produced, deterministic pattern |
| `f*` | no query semantics |
| `.` any-type atoms | weakly typed; no benchmark need yet |
| `=`/`#` node identity, canonical `<`/`>`, `##`, k-variants other than `<k:`/`:k>` | rarely needed; `<`/`>` semantics (canonical node order) are unintuitive in natural language |
| feature-comparison relations `.f.` … | useful later (agreement queries); needs its own IR design |
| edge values `-e=v>` | needs edge-value schema research (#4) |
| `/where/ /have/`, `/with/ /or/`, nested quantifiers | disjunction and universal quantification enlarge the IR and evaluation surface |
| named sets (`sets=`) | depends on app-level configuration |
| indentation-based nesting and `op`-prefixed atoms | equivalent to explicit relations; not emitted |

## 5. Invariants derived for the compiler (#3)

1. Escape values per §2.3, and reject empty values and values containing control characters with a dedicated *unrepresentable value* error.
2. Never emit a generated name equal to an object type or set name.
3. Feature, object type and edge names are emitted only if they match TF's name patterns *and* are present in the schema. A feature name containing `.` or another character outside `[a-zA-Z0-9-@_]` is inexpressible. The warp features `oslots`, `otype` and all `omap@…` features are excluded even though every schema contains them.
4. Relation operators come from a closed enum, never from strings. `k` is bounded by the compiler.
5. A query is accepted only when TF reports zero error messages *after* its results are consumed (or a limit is given), quantifier bodies included, and no exception is raised.
6. Every TF call that executes a query passes an explicit `limit`, probing with `n + 1` to detect overflow.
7. A quantified atom line carries no escaped condition. Escaped value conditions go on one indented continuation line, which never begins with a bare presence condition, because `  gn …` is parsed as an atom of type `gn` (test `test_continuation_line_starting_with_bare_presence_is_parsed_as_an_atom`). Quantifier bodies are non-empty and sit at the keyword's indentation, and the parent is referenced only through `..` relation lines.

## 6. Follow-up risks

- **Upstream defects** TF-1 (invalid quantifier bodies don't fail the search) and TF-2 (the quantified parent line is unescaped) are tracked in [docs/upstream-bugs.md](../upstream-bugs.md), to be filed upstream together with fix PRs.
- **Private validation API.** `_parse` and `_prepare` may change across TF minor versions. The conformance suite is the tripwire.
