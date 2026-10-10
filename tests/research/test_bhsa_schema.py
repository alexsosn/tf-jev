"""Opt-in evidence for the corpus-schema research (#4) on BHSA 2021.

Run with ``TF_JEV_BHSA_DIR=~/text-fabric-data/github/ETCBC/bhsa/tf/2021``.
Numbers match docs/research/data/bhsa-2021-schema-probe.md.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import pytest

from scripts.probe_corpus_schema import content_digest
from tests.conformance.tf_harness import run_template

BHSA_2021_DIGEST = "62807aecab9a9689c19f9e454a16709f9b093d185b76b3874e7037ff34ecf793"


def test_bhsa_content_digest_identifies_the_pinned_release(bhsa_dir: Path) -> None:
    assert content_digest(bhsa_dir) == BHSA_2021_DIGEST


def test_bhsa_object_types_and_edge_features(bhsa_api: Any) -> None:
    TF = bhsa_api.TF
    sets = TF.explore(silent="deep", show=True)

    assert [level[0] for level in bhsa_api.C.levels.data] == [
        "book", "chapter", "lex", "verse", "half_verse", "sentence", "sentence_atom",
        "clause", "clause_atom", "phrase", "phrase_atom", "subphrase", "word",
    ]  # fmt: skip
    assert set(sets["edges"]) == {
        "oslots", "mother", "functional_parent", "distributional_parent",
        "omap@2017-2021", "omap@c-2021",
    }  # fmt: skip
    assert TF.features["omap@c-2021"].edgeValues is True
    assert TF.features["mother"].edgeValues is False
    assert len(sets["nodes"]) == 109


@pytest.mark.parametrize(
    "feature, otype, distinct",
    [
        ("gn", "word", 4),
        ("sp", "word", 14),
        ("sp", "lex", 14),
        ("function", "phrase", 29),
        ("typ", "phrase", 13),
        ("typ", "clause", 42),
        ("lex", "word", 8769),
        ("number", "phrase", 9),
        ("number", "word", 29736),
        ("g_word_utf8", "word", 92474),
    ],
)
def test_bhsa_domains_differ_per_object_type(
    bhsa_api: Any, feature: str, otype: str, distinct: int
) -> None:
    bhsa_api.TF.load(feature, add=True, silent="deep")

    assert len(bhsa_api.Fs(feature).freqList({otype})) == distinct


def test_bhsa_empty_string_values_need_the_empty_regex(bhsa_api: Any) -> None:
    bhsa_api.TF.load("nme", add=True, silent="deep")

    assert dict(bhsa_api.Fs("nme").freqList())[""] == 121983
    empty = run_template(bhsa_api, "word nme~^$", limit=200000)
    assert empty.results is not None and len(empty.results) == 121983
    assert run_template(bhsa_api, "word nme#").results == ()


def test_bhsa_missing_values_are_mostly_sentinel_strings(bhsa_api: Any) -> None:
    bhsa_api.TF.load("nametype root", add=True, silent="deep")
    words = bhsa_api.F.otype.sInterval("word")
    n_words = words[1] - words[0] + 1

    assert "NA" in dict(bhsa_api.Fs("gn").freqList({"word"}))
    assert "absent" in dict(bhsa_api.Fs("prs").freqList({"word"}))
    assert sum(c for _, c in bhsa_api.Fs("nametype").freqList({"word"})) == n_words - 391084


def test_bhsa_feature_names_that_equal_object_types(bhsa_api: Any) -> None:
    sets = bhsa_api.TF.explore(silent="deep", show=True)
    otypes = {level[0] for level in bhsa_api.C.levels.data}

    assert sorted(set(sets["nodes"]) & otypes) == ["book", "chapter", "lex", "verse"]


def test_bhsa_pointed_hebrew_values_are_often_not_nfc(bhsa_api: Any) -> None:
    bhsa_api.TF.load("voc_lex_utf8", add=True, silent="deep")
    values = {v for v, _ in bhsa_api.Fs("voc_lex_utf8").freqList()}

    assert sum(1 for v in values if unicodedata.normalize("NFC", v) != v) == 3287
