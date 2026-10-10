"""Executable conformance fixture for the native Text-Fabric search grammar (#2).

Every case runs through real Text-Fabric search on a tiny synthetic corpus
(see ``tf_harness``). Node numbers refer to that corpus:

    words 1..8 | phrases 9..13 | clauses 14 (words 1-4), 15 (words 5-8) | sentence 16

These tests pin Text-Fabric behavior, not tf-jev behavior. If one fails after a
Text-Fabric upgrade, the grammar research in docs/research/tf-search-grammar.md
must be revisited before the compiler is touched.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.conformance.tf_harness import run_template

R = tuple[tuple[int, ...], ...]


def rows(*tuples: tuple[int, ...]) -> R:
    return tuple(sorted(tuples))


def ones(*nodes: int) -> R:
    return rows(*((n,) for n in nodes))


VALID: dict[str, tuple[str, R]] = {
    # --- atoms and node-feature constraints -------------------------------
    "otype_only": ("phrase", ones(9, 10, 11, 12, 13)),
    "feat_eq": ("word sp=verb", ones(3, 6, 8)),
    "feat_conjunction": ("word sp=verb gn=f nu=pl", ones(6)),
    "feat_alternatives": ("word sp=verb|adjv", ones(3, 6, 7, 8)),
    "feat_neq": ("word sp#verb", ones(1, 2, 4, 5, 7)),
    "feat_neq_alternatives": ("word sp#verb|subs", ones(1, 7)),
    "feat_neq_matches_nodes_without_value": ("word gn#m", ones(1, 2, 5, 6, 7)),
    "feat_has_value": ("word gn", ones(2, 3, 4, 5, 6, 8)),
    "feat_has_no_value": ("word gn#", ones(1, 7)),
    "feat_any_or_none": ("word gn*", ones(1, 2, 3, 4, 5, 6, 7, 8)),
    "int_gt": ("word rank>6", ones(7, 8)),
    "int_lt": ("word rank<2", ones(1)),
    "int_eq_alternatives": ("word rank=3|4", ones(3, 4)),
    "regex": ("word lex~^BR", ones(3)),
    # Repeated conditions on one feature of one atom: the last one silently wins.
    "repeated_feature_last_wins": ("word sp=verb sp=subs", ones(2, 4, 5)),
    "repeated_bound_last_wins": ("word rank>2 rank<5", ones(1, 2, 3, 4)),
    "repeated_bound_across_lines_last_wins": ("word rank>2\n  rank<5", ones(1, 2, 3, 4)),
    "repeated_exclusion_across_lines_last_wins": (
        "word sp#verb\n  sp#a\\ b",
        ones(1, 2, 3, 4, 5, 6, 7, 8),
    ),
    "range_via_two_atoms_and_identity": (
        "a:word rank>2\nb:word rank<5\na = b",
        rows((3, 3), (4, 4)),
    ),
    "feature_on_continuation_line": ("word\n  sp=verb", ones(3, 6, 8)),
    "comment_line": ("% comment\nword sp=verb", ones(3, 6, 8)),
    "unknown_value_is_silently_empty": ("word sp=nonesuch", ()),
    # --- literal values and escaping --------------------------------------
    "value_with_gt_and_slash": ("word lex=R>CJT/", ones(2)),
    "value_unicode": ("word lex=בָּרָא", ones(8)),
    "escaped_space": (r"word lex=a\ b", ones(5)),
    "escaped_pipe": (r"word lex=a\|b", ones(6)),
    "unescaped_pipe_is_alternation": ("word lex=a|b", ()),
    "escaped_backslash": (r"word lex=a\\b", ones(7)),
    "lone_backslash_is_literal": (r"word lex=a\b", ones(7)),
    "backslash_t_is_letter_t_not_tab": (r"word gloss=\t", ones(1)),
    "escaped_pipe_in_regex": (r"word lex~^a\|b$", ones(6)),
    # --- embedding --------------------------------------------------------
    "indent_embeds": ("clause\n  phrase function=Pred", rows((14, 10))),
    "embeds_named": ("c:clause\np:phrase function=Pred\nc [[ p", rows((14, 10))),
    "embeds_direction_matters": ("c:clause\np:phrase function=Pred\np [[ c", ()),
    "embedded_in": ("c:clause\np:phrase function=Pred\np ]] c", rows((14, 10))),
    "any_type_dot": ("c:clause\n  . function=Pred", rows((14, 10))),
    # --- slot and order relations ----------------------------------------
    "adjacent_op_prefix": ("word sp=subs\n<: word sp=verb", rows((2, 3), (5, 6))),
    "adjacent_named": ("a:word sp=subs\nb:word sp=verb\na <: b", rows((2, 3), (5, 6))),
    "adjacent_converse": ("a:word sp=subs\nb:word sp=verb\nb :> a", rows((2, 3), (5, 6))),
    "k_near_before_k1": ("a:word sp=prep\nb:word sp=verb\na <1: b", rows((1, 3))),
    "k_near_before_k0_equals_adjacent": (
        "a:word sp=subs\nb:word sp=verb\na <0: b",
        rows((2, 3), (5, 6)),
    ),
    "canonical_before": (
        "a:phrase function=Pred\nb:phrase\na < b",
        rows((10, 11), (10, 12), (10, 13)),
    ),
    "completely_before": (
        "a:phrase function=Pred\nb:phrase\na << b",
        rows((10, 11), (10, 12), (10, 13)),
    ),
    "completely_after": (
        "a:phrase function=Pred\nb:phrase\na >> b",
        rows((10, 9)),
    ),
    "k_near_after_k1": ("a:word sp=verb\nb:word sp=prep\na :1> b", rows((3, 1))),
    "same_slots": ("a:phrase\nb:word\na == b", rows((10, 3), (11, 4))),
    "overlap": (
        "a:clause\nb:phrase\na && b",
        rows((14, 9), (14, 10), (14, 11), (15, 12), (15, 13)),
    ),
    "no_common_slots": ("a:clause\nb:phrase function=Pred\na || b", rows((15, 10))),
    "same_start": ("a:clause\nb:phrase\na =: b", rows((14, 9), (15, 12))),
    "same_end": ("a:clause\nb:phrase\na := b", rows((14, 11), (15, 13))),
    "same_start_and_end": ("a:phrase\nb:word\na :: b", rows((10, 3), (11, 4))),
    # --- edge features ----------------------------------------------------
    "edge_forward": ("a:clause\nb:clause\na -mother> b", rows((15, 14))),
    "edge_backward": ("a:clause\nb:clause\na <mother- b", rows((14, 15))),
    "edge_either": ("a:clause\nb:clause\na <mother> b", rows((14, 15), (15, 14))),
    "edge_valued_any": ("a:word\nb:word\na -dist> b", rows((1, 2), (1, 3))),
    "edge_value_eq": ("a:word\nb:word\na -dist=2> b", rows((1, 3))),
    "edge_value_gt": ("a:word\nb:word\na -dist>1> b", rows((1, 3))),
    # --- feature comparison relations ------------------------------------
    "featcmp_same": ("a:word\nb:word\na .gn. b\na <: b", rows((3, 4), (5, 6))),
    "featcmp_differ_counts_missing_as_unequal": (
        "a:word\nb:word\na .gn#gn. b\na <: b",
        rows((1, 2), (2, 3), (4, 5), (6, 7), (7, 8)),
    ),
    # --- quantifiers ------------------------------------------------------
    "without": ("clause\n/without/\n  phrase function=Pred\n/-/", ones(15)),
    "where_have": ("phrase\n/where/\n  w:word sp=verb\n/have/\n  w gn=f\n/-/", ones(9, 11, 12)),
    "with_or": (
        "clause\n/with/\n  phrase function=Pred\n/or/\n  phrase function=PreC\n/-/",
        ones(14, 15),
    ),
    # Canonical quantifier form: parent conditions on a continuation line, body at
    # the indentation of the quantifier keyword, parent referenced only via `..`.
    "without_canonical_flat_body": (
        "n1:word sp=verb\n/without/\nw:word sp=adjv\n.. <: w\n/-/",
        ones(3, 8),
    ),
    "without_canonical_escaped_parent_value": (
        "n1:word\n  lex=a\\|b\n/without/\nw:word sp=adjv\n.. <: w\n/-/",
        (),
    ),
    "without_canonical_split_conditions": (
        "n1:word gn\n  lex=a\\|b\n/without/\nw:word sp=adjv\n.. <: w\n/-/",
        (),
    ),
    "empty_without_body_excludes_everything": ("word\n/without/\n/-/", ()),
    "parent_reference": ("clause\n/without/\n  w:word sp=adjv\n  .. [[ w\n/-/", ones(14)),
}

INVALID: dict[str, tuple[str, str]] = {
    # syntax stage
    "illegal_name": ("a!b:word", 'Illegal name: "a!b"'),
    "empty_value": ("word lex=", 'Unrecognized feature condition "lex="'),
    "unescaped_space_splits_constraint": ("word lex=a b", 'Missing feature "b"'),
    "non_numeric_limit": ("word rank<abc", 'Limit is non numeric "abc"'),
    "unterminated_quantifier": ("clause\n/without/\n  phrase", 'Unterminated "/without/"'),
    "quantifier_bad_start": ("clause\n/have/\n  phrase\n/-/", 'Can not start with "/have/:"'),
    # semantics stage
    "unknown_otype": ("wordx", 'Unknown object type: "wordx"'),
    "otype_case_sensitive": ("Word", 'Unknown object type: "Word"'),
    "unknown_feature": ("word spx=verb", 'Missing feature "spx"'),
    "feature_case_sensitive": ("word SP=verb", 'Missing feature "SP"'),
    "int_feature_string_value": ("clause number=abc", '"abc" is not a number'),
    "int_feature_regex": ("word rank~^1", 'Feature "rank" has wrong values'),
    "str_feature_comparison": ("word lex<5", 'Feature "lex" has wrong values'),
    "valueless_edge_with_value": ("a:clause\nb:clause\na -mother=1> b", "cannot have values"),
    "unknown_relation": ("a:word\nb:word\na <<<< b", 'Unknown relation: "<<<<"'),
    "undefined_relation_name": ("a:word\na <: zz", 'Relation with undefined name: "zz"'),
    "lonely_relation": ("<: word", "Lonely relation: not allowed at outermost level"),
    "bad_outdent": ("clause\n  phrase\n word", "Unexpected indent: 1"),
    # connectedness stage
    "empty_template": ("", "Search without instructions"),
    "disconnected": ("clause\nphrase", "More than one connected components (2)"),
    # failures raised as exceptions rather than messages
    "warp_edge_oslots": ("a:word\nb:phrase\na <oslots> b", "KeyError"),
    "featcmp_unknown_feature": ("a:word\nb:word\na .lexx. b\na <: b", "AttributeError"),
    "featcmp_bad_regex": (
        "a:word\nb:word\na .lex~[~lex. b\na <: b",
        "unterminated character set",  # re.error, renamed PatternError in 3.13
    ),
    # quantifier sub-search
    "quantifier_where_antecedent_error": (
        "phrase\n/where/\n  word spx=verb\n/have/\n  word\n/-/",
        'Missing feature "spx"',
    ),
    "quantifier_have_error": (
        "phrase\n/where/\n  w:word sp=verb\n/have/\n  w gnx=f\n/-/",
        'Missing feature "gnx"',
    ),
    "quantifier_with_bad_alternative": (
        "clause\n/with/\n  phrase function=Pred\n/or/\n  phrase functionx=PreC\n/-/",
        'Missing feature "functionx"',
    ),
    "quantifier_body_unknown_feature": (
        "clause\n/without/\n  phrase functionx=Pred\n/-/",
        'Missing feature "functionx"',
    ),
}


@pytest.mark.parametrize("template, expected", VALID.values(), ids=VALID.keys())
def test_valid_template(tiny_api: Any, template: str, expected: R) -> None:
    outcome = run_template(tiny_api, template)

    assert outcome.ok, outcome.error_text()
    assert outcome.results == expected


@pytest.mark.parametrize("template, message", INVALID.values(), ids=INVALID.keys())
def test_invalid_template(tiny_api: Any, template: str, message: str) -> None:
    outcome = run_template(tiny_api, template)

    assert not outcome.ok
    assert message in outcome.error_text()


def test_invalid_quantifier_body_fails_open_without_message_check(tiny_api: Any) -> None:
    """An invalid /without/ body excludes nothing: TF yields *every* parent node.

    Only the collected messages reveal the error, so a validator must check
    message status and never trust ``exe.good`` or a non-empty result alone.
    """
    template = "clause\n/without/\n  phrase functionx=Pred\n/-/"
    (results, _status, _html, exe) = tiny_api.S.search(
        template, here=False, silent="deep", _msgCache=[]
    )

    assert exe.good
    assert sorted(results) == [(14,), (15,)]
    assert not run_template(tiny_api, template).ok


def test_backslash_t_and_n_escapes_are_not_control_characters() -> None:
    """``\\t`` and ``\\n`` unescape to the letters, so tab/newline values are inexpressible."""
    from tf.search.syntax import _esc, _unesc

    assert _unesc(_esc(r"a\tb\nc")) == "atbnc"


def test_node_name_equal_to_an_otype_silently_shadows_that_otype(tiny_api: Any) -> None:
    """A later atom whose type equals an earlier node *name* refers to that node.

    The query stays valid but its meaning changes, so generated names must be
    disjoint from every object type (and named set) of the loaded corpus.
    """
    honest = run_template(tiny_api, "a:phrase function=Pred\n  word")
    shadowed = run_template(tiny_api, "word:phrase function=Pred\n  word")

    assert honest.ok and honest.results == rows((10, 3))
    assert shadowed.ok and shadowed.results == ()


def test_limit_bounds_results_without_changing_validity(tiny_api: Any) -> None:
    outcome = run_template(tiny_api, "a:word\nb:word\na < b", limit=3)

    assert outcome.ok
    assert outcome.results == rows((1, 2), (1, 3), (1, 4))


def test_escaped_value_on_quantified_atom_line_is_unescaped_in_the_sub_search(
    tiny_api: Any,
) -> None:
    """TF-2: the parent atom line is regenerated *unescaped* for the sub-search.

    ``a\\|b`` becomes the alternation ``a|b`` inside /without/, nothing is
    excluded, and no message reveals it. Word 6 (lex ``a|b``) is immediately
    followed by an adjective, so the honest answer is empty.
    """
    template = "n1:word lex=a\\|b\n/without/\nw:word sp=adjv\n.. <: w\n/-/"
    outcome = run_template(tiny_api, template)

    assert outcome.ok
    assert outcome.results == ones(6)


def test_indented_quantifier_body_is_embedded_in_the_parent(tiny_api: Any) -> None:
    """Body lines keep their indentation, which adds an implicit ``]] parent`` edge.

    A word cannot be embedded in another word, so the indented body matches
    nothing and excludes nothing: verb 6 survives although it precedes an adjective.
    """
    indented = run_template(
        tiny_api, "n1:word sp=verb\n/without/\n  w:word sp=adjv\n  .. <: w\n/-/"
    )
    flat = run_template(tiny_api, "n1:word sp=verb\n/without/\nw:word sp=adjv\n.. <: w\n/-/")

    assert indented.ok and indented.results == ones(3, 6, 8)
    assert flat.ok and flat.results == ones(3, 8)


def test_result_overflow_is_reported_even_without_limit(tiny_api: Any) -> None:
    """Fail limit on the tiny corpus is 4 * 16 = 64 results; this query has 392."""
    template = "a:word\nb:word\nc:word\na # b\nb # c"

    unbounded = run_template(tiny_api, template)
    bounded = run_template(tiny_api, template, limit=1000)

    assert not unbounded.ok
    assert "cut off at 64 results" in unbounded.error_text()
    assert bounded.ok and bounded.results is not None and len(bounded.results) == 392


def test_explicit_limit_truncates_silently(tiny_api: Any) -> None:
    outcome = run_template(tiny_api, "a:word\nb:word\na < b", limit=3)

    assert outcome.ok and outcome.results is not None and len(outcome.results) == 3


def test_large_k_is_accepted_and_matches_everything(tiny_api: Any) -> None:
    outcome = run_template(tiny_api, "a:word\nb:word\na <99999999999999999999: b")

    assert outcome.ok and outcome.results is not None and (1, 1) in outcome.results


def test_continuation_line_starting_with_bare_presence_is_parsed_as_an_atom(
    tiny_api: Any,
) -> None:
    """``  gn sp=verb`` is an atom of type ``gn``, not a condition line.

    The quantifier then no longer follows an atom at its level and the template is
    rejected. With the presence condition later on the line, it is a condition line.
    """
    bare_first = run_template(
        tiny_api, "n1:word\n  gn sp=verb\n/without/\nw:word sp=adjv\n.. <: w\n/-/"
    )
    value_first = run_template(
        tiny_api, "n1:word\n  sp=verb gn\n/without/\nw:word sp=adjv\n.. <: w\n/-/"
    )

    assert not bare_first.ok
    assert "Does not immediately follow an atom at the same level" in bare_first.error_text()
    assert value_first.ok and value_first.results == ones(3, 8)


def test_condition_line_starting_with_dash_feature_is_parsed_as_an_op_line() -> None:
    """Feature names may start with ``-``; such a continuation line becomes an op line."""
    from tf.search.syntax import parseLine

    assert parseLine("  -x=a\\ b")[0] == "op"
    assert parseLine("  x=a\\ b")[0] == "feat"
