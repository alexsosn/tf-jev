"""RED-first contract tests for the pinned NL → native-TF benchmark seed (#10)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.nl_benchmark import _git_blob_sha, check_gold, equivalent, load_catalog, verify_source

DATA = Path(__file__).resolve().parents[1] / "benchmarks/nl-tf-v1/bhsa-2021.json"


def _record(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": "test-1",
        "split": "train",
        "status": "supported",
        "difficulty": "simple",
        "request": "Find the prepositions",
        "gold_query": "word sp=prep",
        "expected_count": 1,
        "rationale": "Exact part-of-speech predicate.",
    }
    record.update(overrides)
    return record


def _catalog(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "format_version": 1,
        "corpus": "ETCBC/bhsa",
        "data_version": "2021",
        "source_sha256": {"otype.tf": "a" * 64},
        "source_git_blobs": {name: "a" * 40 for name in (
            "otype.tf", "oslots.tf", "sp.tf", "gn.tf", "nu.tf", "function.tf",
            "mother.tf", "book.tf", "qere.tf"
        )},
        "cases": cases,
    }


def _load(tmp_path: Path, doc: dict[str, Any]) -> Any:
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return load_catalog(path)


def test_seed_has_frozen_splits_and_attested_native_cases() -> None:
    catalog = load_catalog(DATA)
    assert catalog.corpus == "ETCBC/bhsa"
    assert catalog.data_version == "2021"
    assert len(catalog.cases) >= 12
    assert {"train", "development", "evaluation"} <= {c.split for c in catalog.cases}
    assert {"supported", "ambiguous", "unsupported"} <= {c.status for c in catalog.cases}
    assert len({c.id for c in catalog.cases}) == len(catalog.cases)
    assert all(c.expected_count is not None for c in catalog.cases if c.status == "supported")


@pytest.mark.parametrize(
    "cases",
    [
        [_record(), _record()],
        [_record(expected_count=True)],
        [_record(expected_count=-1)],
        [_record(gold_query="")],
        [_record(request="  ")],
        [_record(status="unsupported")],
        [_record(status="ambiguous")],
        [_record(status="supported", gold_query=None)],
        [_record(status="unknown")],
        [_record(split="holdout")],
        [_record(unexpected="field")],
    ],
)
def test_reject_malformed_cases(tmp_path: Path, cases: list[dict[str, Any]]) -> None:
    with pytest.raises(ValueError):
        _load(tmp_path, _catalog(cases))


def test_reject_wrong_root_shape(tmp_path: Path) -> None:
    doc = _catalog([_record()])
    doc["extra"] = "unknown"
    with pytest.raises(ValueError):
        _load(tmp_path, doc)
    doc.pop("extra")
    doc["source_sha256"] = {"otype.tf": "z" * 64}
    with pytest.raises(ValueError):
        _load(tmp_path, doc)
    doc["source_sha256"] = {"otype.tf": "a" * 64}
    doc["source_git_blobs"]["sp.tf"] = "x" * 40
    with pytest.raises(ValueError):
        _load(tmp_path, doc)


def test_abstention_never_contains_a_gold_query(tmp_path: Path) -> None:
    for status in ("ambiguous", "unsupported"):
        catalog = _load(
            tmp_path, _catalog([_record(status=status, gold_query=None, expected_count=None)])
        )
        assert catalog.cases[0].gold_query is None


def test_git_blob_hash_matches_independent_git_object_fixture(tmp_path: Path) -> None:
    # Canonical Git blob SHA-1 for "hello" (not SHA-1 over raw bytes).
    (tmp_path / "hello").write_bytes(b"hello")
    assert _git_blob_sha(tmp_path / "hello") == "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"


def test_sha_pin_rejects_drift(tmp_path: Path) -> None:
    doc = _catalog([_record()])
    hashes: dict[str, str] = {}
    for name in doc["source_git_blobs"]:
        raw = ("synthetic-" + name).encode()
        (tmp_path / name).write_bytes(raw)
        hashes[name] = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    doc["source_git_blobs"] = hashes
    doc["source_sha256"] = {
        "otype.tf": hashlib.sha256((tmp_path / "otype.tf").read_bytes()).hexdigest()
    }
    catalog = _load(tmp_path, doc)
    verify_source(tmp_path, catalog)
    # A feature edit must be detected even if otype.tf is unchanged.
    (tmp_path / "sp.tf").write_bytes(b"forged feature")
    with pytest.raises(ValueError, match="source"):
        verify_source(tmp_path, catalog)


def test_native_gold_and_diagnostic_rejection(tiny_api: Any, tmp_path: Path) -> None:
    case = _load(tmp_path, _catalog([_record()])).cases[0]
    assert check_gold(tiny_api, case) == 1
    wrong = _load(tmp_path, _catalog([_record(gold_query="word sp=subs")])).cases[0]
    with pytest.raises(ValueError, match="count"):
        check_gold(tiny_api, wrong)
    invalid = _load(tmp_path, _catalog([_record(gold_query="word unknown=x")])).cases[0]
    with pytest.raises(ValueError, match="invalid"):
        check_gold(tiny_api, invalid)


def test_native_equivalence_checks_node_ids_not_only_counts(tiny_api: Any) -> None:
    # Each has one result, but the matched node IDs differ.
    assert not equivalent(tiny_api, "word sp=prep", "word sp=adjv")
    assert equivalent(tiny_api, "word sp=subs", "n0:word sp=subs")
    # A small row budget must fail closed instead of silently truncating both sets.
    with pytest.raises(ValueError, match="limit"):
        equivalent(tiny_api, "word sp=subs", "word sp=subs", max_rows=2)


def test_opt_in_bhsa_native_counts(bhsa_api: Any, bhsa_dir: Path) -> None:
    catalog = load_catalog(DATA)
    verify_source(bhsa_dir, catalog)
    for case in catalog.cases:
        if case.status == "supported":
            assert check_gold(bhsa_api, case) == case.expected_count
