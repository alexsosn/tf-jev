"""The fresh evaluation cannot accidentally trigger unreviewed paid calls."""

from pathlib import Path
from typing import Any

import pytest

from scripts.candidate_evaluation import main


def test_explicit_live_required_before_artifact_or_network(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    with pytest.raises(ValueError, match="requires"):
        main(
            [
                str(tmp_path),
                "--output",
                str(tmp_path / "report"),
                "--private-review",
                str(tmp_path / "private"),
            ]
        )
    assert not (tmp_path / "report").exists()


def test_frozen_input_change_stops_before_corpus_or_client(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import scripts.candidate_evaluation as runner

    monkeypatch.setenv("TF_JEV_LIVE", "1")
    monkeypatch.setattr(
        runner,
        "version",
        lambda package: {"text-fabric": "13.1.0", "typesafe-sdk": "0.7.4"}[package],
    )
    p = tmp_path / "changed.json"
    p.write_text("{}")
    monkeypatch.setattr(runner, "BENCHMARK", p)
    with pytest.raises(ValueError, match="frozen"):
        main(
            [
                str(tmp_path),
                "--output",
                str(tmp_path / "report"),
                "--private-review",
                str(tmp_path / "private"),
                "--live",
            ]
        )
    assert not (tmp_path / "report").exists()


def test_metadata_attack_has_separate_identity_and_keeps_native_domains(tiny_api: Any) -> None:
    from scripts.candidate_evaluation import attacked_schema, metadata_digest
    from tf_jev.schema import extract_schema

    schema = extract_schema(tiny_api)
    attacked = attacked_schema(schema)
    assert metadata_digest(schema) != metadata_digest(attacked)
    assert schema.identity.key == attacked.identity.key
    assert schema.domain("sp", "word") == attacked.domain("sp", "word")
    assert "UNTRUSTED TEST NOTE" not in (schema.node_feature("sp", "word").description or "")
    assert "UNTRUSTED TEST NOTE" in attacked.node_feature("sp", "word").description
