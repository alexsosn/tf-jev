"""Executable evidence for the corpus-schema research (#4) on the tiny fixture.

Pins the Text-Fabric discovery APIs a CorpusSchema extractor relies on. See
docs/research/corpus-schema.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric

from scripts.probe_corpus_schema import content_digest, corpus_identity, probe
from tests.conformance.tf_harness import build_tiny_corpus, run_template


@pytest.fixture(scope="module")
def tiny_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("tiny-schema")
    build_tiny_corpus(directory)
    return directory


def fresh(directory: Path) -> tuple[Any, Any]:
    TF = Fabric(locations=str(directory), silent="deep")
    return TF, TF.load("", silent="deep")


def test_unloaded_features_have_no_metadata_until_explored(tiny_dir: Path) -> None:
    """``load("")`` loads only otext-referenced features (here ``lex``, ``number``)."""
    TF, api = fresh(tiny_dir)

    assert sorted(api.Fall()) == ["lex", "number", "otype"]
    assert TF.features["mother"].isEdge is None
    assert TF.features["gn"].metaData == {}


def test_explore_classifies_features_from_metadata_only(tiny_dir: Path) -> None:
    TF, api = fresh(tiny_dir)

    sets = TF.explore(silent="deep", show=True)

    assert {"lex", "sp", "rank", "typ", "suffix", "otype"} <= set(sets["nodes"])
    assert set(sets["edges"]) == {"oslots", "mother", "dist"}
    assert sets["configs"] == ("otext",)
    assert TF.features["rank"].dataType == "int"
    assert TF.features["dist"].edgeValues is True
    assert TF.features["mother"].edgeValues is False
    assert "sp" not in api.Fall()  # still only metadata


def test_value_domains_must_be_taken_per_object_type(tiny_dir: Path) -> None:
    TF, api = fresh(tiny_dir)
    TF.load("typ", add=True, silent="deep")

    phrase = dict(api.Fs("typ").freqList({"phrase"}))
    clause = dict(api.Fs("typ").freqList({"clause"}))

    assert phrase == {"NP": 2, "PP": 1, "VP": 1, "AdjP": 1}
    assert clause == {"xQt0": 1, "NmCl": 1}


def test_empty_string_is_an_empty_alternative_in_a_value_set(tiny_dir: Path) -> None:
    """``f=|`` is the value set ``{""}``: TF splits values on ``|``.

    Words 1 and 3 have suffix "", word 2 "H", word 4 "JM", words 5-8 no value.
    """
    TF, api = fresh(tiny_dir)
    api = TF.loadAll(silent="deep")

    assert dict(api.Fs("suffix").freqList())[""] == 2
    assert run_template(api, "word suffix=|").results == ((1,), (3,))
    assert run_template(api, "word suffix=|H").results == ((1,), (2,), (3,))
    assert run_template(api, "word suffix~^$").results == ((1,), (3,))
    # "no value" is a different thing from the empty string
    assert run_template(api, "word suffix#").results == ((5,), (6,), (7,), (8,))
    # f#| excludes the empty string but keeps nodes without a value
    assert run_template(api, "word suffix#|").results == ((2,), (4,), (5,), (6,), (7,), (8,))
    assert not run_template(api, "word suffix=").ok


def test_probe_reports_per_type_domains_and_empty_values(tiny_dir: Path) -> None:
    report = "\n".join(probe(tiny_dir))

    assert "| `typ` | `phrase` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |" in report
    assert "| `typ` | `clause` | str | 2 | 1-8 | 0 | 0 | 0 | 0 |" in report
    assert "| `suffix` | `word` | str | 3 | 1-8 | 4 | 2 | 0 | 0 |" in report
    assert "| `lex` | `word` | str | 8 | 1-8 | 0 | 0 | 0 | 3 |" in report
    assert "| `mother` | False | clause→clause: 1 |" in report


def test_probe_requires_otext(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    (tmp_path / "otext.tf").unlink()

    with pytest.raises(SystemExit, match="otext"):
        probe(tmp_path)


def test_content_digest_is_unambiguous_and_skips_directories(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    # same concatenation of name + NUL + bytes under a naive scheme
    (a / "x.tf").write_bytes(b"1\x00y.tf\x002")
    (b / "x.tf").write_bytes(b"1")
    (b / "y.tf").write_bytes(b"2")
    (b / "sub.tf").mkdir()

    assert content_digest(a) != content_digest(b)


def test_corpus_identity_covers_every_location_in_order(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "x.tf").write_bytes(b"1")
    (b / "y.tf").write_bytes(b"2")

    assert corpus_identity([a, b]) == ((str(a), content_digest(a)), (str(b), content_digest(b)))
    assert corpus_identity([a, b]) != corpus_identity([b, a])
