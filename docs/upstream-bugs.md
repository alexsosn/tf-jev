# Upstream bugs (internal tracker)

Defects found in third-party dependencies while building tf-jev. They are tracked here and **filed upstream later, together with a proposed fix PR**. Do not file them piecemeal.

Each entry gives the affected version, a minimal reproduction, the evidence in this repository, and how tf-jev works around it.

## Text-Fabric (`annotation/text-fabric`)

### TF-1: Invalid quantifier body fails open

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
- **Expected:** the outer search fails, with `exe.good = False` and no results, as it does for the same error outside a quantifier.
- **Likely fix:** in `_doQuantifier`, check `exe.good` after each nested search. If it is false, set `searchExe.good = False` and stop. The same pattern affects the `/where/`, `/have/`, `/with/` and `/or/` branches.
- **Evidence:** `tests/conformance/test_tf_search_grammar.py::test_invalid_quantifier_body_fails_open_without_message_check` and `tests/conformance/test_tf_search_grammar_bhsa.py::test_bhsa_quantifier_body_error_is_reported`.
- **tf-jev mitigation:** a query counts as valid only if no message tuple is flagged as an error (see `docs/research/tf-search-grammar.md` §3).

## Candidates (behavior, not necessarily bugs)

Discuss these upstream only if a fix PR makes the case. They are recorded for completeness.

- **Name/type shadowing is silent.** An atom whose type equals an earlier node name becomes a reference to that node, with no warning. This is documented TF behavior for name references, but the collision with real object types is never reported. Evidence: `test_node_name_equal_to_an_otype_silently_shadows_that_otype`.
- **`\t` and `\n` escapes unescape to the letters `t` and `n`.** They are listed in `ESCAPES` like real escapes, so users are likely to read them as tab and newline. Evidence: `test_backslash_t_and_n_escapes_are_not_control_characters`.
- **The result-limit overflow is reported as an error** ("cut off at N results"), indistinguishable by status from a grammar error.
- **Unhelpful message for a type-mismatched comparison.** For `lex<5` on a str feature, the message prints `<function _makeLimit.<locals>.<lambda> …>` instead of the condition.
