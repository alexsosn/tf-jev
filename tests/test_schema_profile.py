"""RED-first reproducible schema load/extraction measurements on real tiny TF."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.profile_schema import main, profile_schema
from tests.conformance.tf_harness import build_tiny_corpus, load_api
from tf_jev.schema import extract_schema


def test_tiny_corpus_profile_preserves_identity_and_limits_output(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    report = profile_schema(tmp_path)
    # The result is portable, machine-readable and excludes absolute local paths.
    data = json.loads(json.dumps(report, sort_keys=True, allow_nan=False))
    assert set(data) == {
        "format_version", "tf_version", "dataset", "version_dir",
        "identity_key", "loaded_sha256", "object_types",
        "node_features", "edge_features", "load_seconds",
        "extract_seconds", "rss_bytes_at_load", "rss_bytes_after_extract",
        "peak_process_rss_bytes", "trace_python",
        "python_traced_peak_bytes",
    }
    schema = extract_schema(load_api(tmp_path))
    assert data["format_version"] == 1
    assert data["loaded_sha256"] == schema.identity.loaded_sha256
    assert data["identity_key"] == schema.identity.key
    assert data["tf_version"] == "13.1.0"
    assert data["object_types"] == len(schema.object_types)
    assert data["node_features"] == len(schema.node_features)
    assert data["edge_features"] == len(schema.edge_features)
    assert data["load_seconds"] >= 0 and data["extract_seconds"] >= 0
    assert data["trace_python"] is False
    assert data["python_traced_peak_bytes"] is None
    assert str(tmp_path) not in json.dumps(data)
    for key in ("rss_bytes_at_load", "rss_bytes_after_extract", "peak_process_rss_bytes"):
        assert data[key] is None or (type(data[key]) is int and data[key] > 0)


def test_optional_python_allocator_trace_and_cli_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory, output = tmp_path / "corpus", tmp_path / "schema-metrics.json"
    directory.mkdir()
    build_tiny_corpus(directory)
    code = main([str(directory), "--trace-python", "--output", str(output)])
    assert code == 0
    report = json.loads(output.read_text())
    assert report["trace_python"] is True
    assert type(report["python_traced_peak_bytes"]) is int
    assert report["python_traced_peak_bytes"] > 0
    assert str(directory) not in output.read_text()
    assert capsys.readouterr().out == ""


def test_profile_rejects_missing_directory_without_creating_report(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent"
    with pytest.raises(ValueError, match="corpus directory"):
        profile_schema(missing)
    output = tmp_path / "missing.json"
    with pytest.raises(ValueError, match="corpus directory"):
        main([str(missing), "--output", str(output)])
    assert not output.exists()


def test_profile_does_not_mutate_existing_corpus_features(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    api: Any = load_api(tmp_path)
    feature_before = dict(api.F.sp.data)
    profile_schema(tmp_path)
    assert dict(api.F.sp.data) == feature_before
