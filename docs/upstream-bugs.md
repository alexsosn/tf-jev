# Upstream bugs (internal tracker)

Defects found in third-party dependencies while building tf-jev. They are tracked here and **filed upstream later, together with a proposed fix PR**. Do not file them piecemeal.

Each entry gives the affected version, a minimal reproduction, the evidence in this repository, and how tf-jev works around it.

## Text-Fabric (`annotation/text-fabric`)

### TF-1: Invalid quantifier sub-template does not fail the search

- **Affected:** `text-fabric` 13.1.0. Found 2026-10-10 in issue #2.
- **Status:** not filed. Fix PR not started.
- **Where:** `tf/search/spin.py` `_doQuantifier`. A quantifier body is parsed only when its nested `SearchExe` runs. If parsing fails, `exe.search()` returns an empty set. For `/without/`, the result becomes `universe - set()`, so every parent node passes. The outer `exe.good` stays `True`, and `S.search` still returns results.
- **Repro:**

  ```text
  clause
  /without/
    phrase functionx=Pred
  /-/
  ```

  On BHSA 2021 this returns all 88,131 clauses. The only signal is an error tuple in `_msgCache` (`Missing feature "functionx"`).
- **Other branches** (each verified on the tiny corpus):
  - An invalid `/where/` antecedent returns the yarn unchanged, so every parent passes (fail-open).
  - An invalid `/have/` consequent excludes every parent that matched the antecedent.
  - An invalid `/with/` or `/or/` alternative is silently dropped from the union.
- **Expected:** the outer search fails, with `exe.good = False` and no results, as it does for the same error outside a quantifier.
- **Likely fix:** in `_doQuantifier`, check `exe.good` after each nested search. If it is false, set `searchExe.good = False` and stop.
- **Evidence:** in `tests/conformance/test_tf_search_grammar.py`, the tests `test_invalid_quantifier_body_fails_open_without_message_check`, `quantifier_where_antecedent_error`, `quantifier_have_error` and `quantifier_with_bad_alternative`; and `tests/conformance/test_tf_search_grammar_bhsa.py::test_bhsa_quantifier_body_error_is_reported`.
- **tf-jev mitigation:** a query counts as valid only if no message tuple is flagged as an error (see `docs/research/tf-search-grammar.md` §3).

### TF-2: Quantified parent atom is re-emitted unescaped

- **Affected:** `text-fabric` 13.1.0. Found 2026-10-11 in the review of PR #15.
- **Status:** not filed. Fix PR not started.
- **Where:** `tf/search/spin.py` `_doQuantifier` calls `syntax.cleanParent(atom src)`. That calls `_genLine`, which calls `_unesc(features)`, so the regenerated parent line loses its escapes before it is parsed again. `deContext` regenerates `..`-typed atom lines in the same way.
- **Repro** (tiny conformance corpus; word 6 has lex `a|b` and is immediately followed by an adjective):

  ```text
  n1:word lex=a\|b
  /without/
  w:word sp=adjv
  .. <: w
  /-/
  ```

  This returns word 6. The expected result is empty, because the sub-search reads `lex=a|b` as an alternation and so excludes nothing. With `lex=a\ b` the sub-search fails with `Missing feature "b"`.
- **Expected:** the sub-search sees the same constraint as the outer template.
- **Likely fix:** in `_genLine`, re-escape the regenerated parts instead of unescaping them. Alternatively, keep the original escaped source text when building `cleanAtom`.
- **Evidence:** `test_escaped_value_on_quantified_atom_line_is_unescaped_in_the_sub_search`.
- **tf-jev mitigation:** escaped conditions of a quantified atom go on an indented continuation line that starts with a value condition, and `..`-typed atoms are never emitted (`docs/research/tf-search-grammar.md` §2.5 and §4).

## Candidates (behavior, not necessarily bugs)

Discuss these upstream only if a fix PR makes the case. They are recorded for completeness.

- **Name/type shadowing is silent.** An atom whose type equals an earlier node name becomes a reference to that node, with no warning. This is documented TF behavior for name references, but the collision with real object types is never reported. Evidence: `test_node_name_equal_to_an_otype_silently_shadows_that_otype`.
- **`\t` and `\n` escapes unescape to the letters `t` and `n`.** They are listed in `ESCAPES` like real escapes, so users are likely to read them as tab and newline. Evidence: `test_backslash_t_and_n_escapes_are_not_control_characters`.
- **The result-limit overflow is reported as an error** ("cut off at N results"), indistinguishable by status from a grammar error. It is also appended only *after* `S.search` has returned its `status`, while the result generator is being consumed.
- **Some invalid templates raise instead of logging an error:**
  - `a <oslots> b` raises `KeyError`;
  - `.f.` on a feature that isn't loaded or doesn't exist raises `AttributeError`;
  - a bad regex in `.f~r~g.` raises `re.error`.
- **A condition line starting with a bare feature name is parsed as an atom** of that "type" (`parseLine` tries `atomRe` before falling back to a feature line).
- **An empty quantifier body is valid** (`word /without/ /-/` excludes everything).
- **`k` in the k-near relations is unbounded.** `<99999999999999999999:` is accepted.
- **Unhelpful message for a type-mismatched comparison.** For `lex<5` on a str feature, the message prints `<function _makeLimit.<locals>.<lambda> …>` instead of the condition.
