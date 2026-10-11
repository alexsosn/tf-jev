"""RED-first reproducible schema load/extraction measurements on real tiny TF."""

from __future__ import annotations

import json
from importlib.metadata import version
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
        "python_traced_peak_bytes", "phases",
    }
    schema = extract_schema(load_api(tmp_path))
    assert data["format_version"] == 1
    assert data["loaded_sha256"] == schema.identity.loaded_sha256
    assert data["identity_key"] == schema.identity.key
    assert data["tf_version"] == version("text-fabric")
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



PHASE_NAMES = (
    "discover",
    "load_features",
    "type_index",
    "warp_digest",
    "node_features",
    "edge_features",
    "source_identity",
    "domains",
)


def test_schema_phase_profile_reports_real_boundary_metrics(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    result = profile_schema(tmp_path)
    phases = result["phases"]
    assert type(phases) is list
    assert tuple(item["name"] for item in phases) == PHASE_NAMES
    assert all(
        type(item["seconds"]) is float and 0 <= item["seconds"] < result["extract_seconds"]
        for item in phases
    )
    for item in phases:
        assert set(item) == {"name", "seconds", "rss_bytes", "peak_process_rss_bytes"}
        assert item["rss_bytes"] is None or (
            type(item["rss_bytes"]) is int and item["rss_bytes"] > 0
        )
    assert abs(sum(item["seconds"] for item in phases) - result["extract_seconds"]) < 2
    assert str(tmp_path) not in json.dumps(result)


def test_private_phase_callback_is_observational_only(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    api: Any = load_api(tmp_path)
    events: list[str] = []
    monitored = extract_schema(api, _phase_observer=events.append)
    baseline = extract_schema(api)
    assert tuple(events) == PHASE_NAMES
    assert monitored.identity == baseline.identity
    assert monitored.to_json() == baseline.to_json()
    assert monitored._inventories == baseline._inventories
