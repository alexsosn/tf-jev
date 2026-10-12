"""Installed model-free CLI on a genuinely saved native Text-Fabric corpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conformance.tf_harness import build_tiny_corpus
from tf_jev.cli import main


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    build_tiny_corpus(tmp_path)
    return tmp_path


def invoke(
    corpus: Path, capsys: pytest.CaptureFixture[str], *arguments: str
) -> tuple[int, str, str]:
    code = main(["compile", "--corpus", str(corpus), "--type", "word", *arguments])
    capture = capsys.readouterr()
    return code, capture.out, capture.err


def test_compile_only_is_selected_schema_and_no_execution(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, stdout, stderr = invoke(corpus, capsys, "--eq", "sp=verb")
    assert status == 0 and stderr == ""
    report = json.loads(stdout)
    assert report["query"] == "n0:word sp=verb"
    assert report["coverage_mode"] == "selected"
    assert report["executed"] is False
    assert len(report["schema_key"]) == 64
    assert "result_count" not in report
    assert str(corpus) not in stdout


def test_real_native_execution_counts_nodes_and_detects_overflow(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, err = invoke(corpus, capsys, "--eq", "sp=verb", "--execute", "--limit", "3")
    assert status == 0 and err == ""
    assert json.loads(out)["result_count"] == 3
    assert json.loads(out)["complete"] is True
    code, out, err = invoke(corpus, capsys, "--eq", "sp=verb", "--execute", "--limit", "2")
    assert code == 2 and out == "" and "limit" in err.lower()


def test_native_integer_and_string_literals_keep_types(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, _ = invoke(corpus, capsys, "--eq", "rank=3", "--execute")
    assert status == 0 and json.loads(out)["result_count"] == 1
    status, out, _ = invoke(corpus, capsys, "--eq", "lex=a|b", "--execute")
    assert status == 0 and json.loads(out)["result_count"] == 1
    assert json.loads(out)["query"] == r"n0:word lex=a\|b"
    status, out, _ = invoke(corpus, capsys, "--eq", "suffix=", "--execute")
    assert status == 0 and json.loads(out)["result_count"] == 2


@pytest.mark.parametrize("arguments", [
    ("--eq", "sp=unknown"),
    ("--eq", "rank=notanumber"),
    ("--eq", "sp=verb", "--eq", "sp=subs"),
    ("--eq", "sp=verb", "--absent", "sp"),
    ("--eq", "sp"),
    ("--eq", "sp=verb\n/without/"),
    ("--eq", "sp=verb", "--limit", "2"),
    ("--eq", "sp=verb", "--execute", "--limit", "0"),
    ("--eq", "sp=verb", "--execute", "--limit", "500001"),
])
def test_fail_closed_without_native_query_or_internal_diagnostics(
    corpus: Path, capsys: pytest.CaptureFixture[str], arguments: tuple[str, ...]
) -> None:
    status, stdout, stderr = invoke(corpus, capsys, *arguments)
    assert status == 2 and stdout == ""
    assert stderr.startswith("error:")
    assert str(corpus) not in stderr
    assert "Traceback" not in stderr
    assert "unknown" not in stderr  # no echo of potentially sensitive values


def test_presence_and_absence_are_compiled_and_executed(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, err = invoke(corpus, capsys, "--present", "sp", "--absent", "gn", "--execute")
    assert status == 0 and not err
    report = json.loads(out)
    assert report["query"] == "n0:word gn# sp"
    assert report["result_count"] == 2


def test_invalid_directory_does_not_show_user_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, err = invoke(tmp_path / "missing", capsys, "--eq", "sp=verb")
    assert status == 2 and not out and str(tmp_path) not in err


def test_explicit_limit_can_cover_full_bhsa_verb_cardinality(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # BHSA 2021's pinned verb query has 73,710 results; the CLI must permit
    # an explicit ceiling above that value. Real 73,710 count is tested in BHSA CI.
    status, out, err = invoke(
        corpus, capsys, "--eq", "sp=verb", "--execute", "--limit", "100000"
    )
    assert status == 0 and not err
    assert json.loads(out)["result_count"] == 3
