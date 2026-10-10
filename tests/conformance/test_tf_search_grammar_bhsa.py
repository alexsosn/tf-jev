"""Opt-in conformance checks on the real BHSA corpus, pinned to data version 2021.

Run with ``TF_JEV_BHSA_DIR=~/text-fabric-data/github/ETCBC/bhsa/tf/2021``.
Counts were recorded with text-fabric 13.1.0 against BHSA release v1.8.1.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.conformance.tf_harness import run_template

COUNTS: dict[str, tuple[str, int]] = {
    "feat_eq": ("word sp=verb", 73710),
    "feat_conjunction": ("word sp=verb gn=f nu=pl", 725),
    "indent_embeds": ("clause\n  word sp=verb", 73710),
    "adjacent": ("word sp=verb\n<: word sp=subs", 15336),
    "edge_mother": ("a:clause\nb:clause\na -mother> b", 13917),
    "without": ("clause\n/without/\n  phrase function=Pred\n/-/", 31061),
    "prs_absent_is_a_string_value_not_missing": ("word prs#", 0),
    "unknown_value_is_silently_empty": ("word sp=nonesuch", 0),
}


@pytest.mark.parametrize("template, count", COUNTS.values(), ids=COUNTS.keys())
def test_bhsa_counts(bhsa_api: Any, template: str, count: int) -> None:
    outcome = run_template(bhsa_api, template)

    assert outcome.ok, outcome.error_text()
    assert outcome.results is not None
    assert len(outcome.results) == count


def test_bhsa_absent_suffix_is_literal_value(bhsa_api: Any) -> None:
    outcome = run_template(bhsa_api, "word prs=absent")

    assert outcome.ok
    assert outcome.results is not None and len(outcome.results) > 0


def test_bhsa_quantifier_body_error_is_reported(bhsa_api: Any) -> None:
    outcome = run_template(bhsa_api, "clause\n/without/\n  phrase functionx=Pred\n/-/")

    assert not outcome.ok
    assert 'Missing feature "functionx"' in outcome.error_text()
