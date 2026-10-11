"""Research intake contract for sourced BHSA tutorial candidates (#10)."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from scripts.bhsa_gold_ir import PROMOTED_IR
from scripts.nl_candidates import (
    CandidateCatalog,
    load_candidates,
    run_candidate,
    verify_candidate_source,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nl-tf-v1/tutorial-candidates.json"


def _read() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _load(tmp_path: Path, data: dict[str, Any]) -> CandidateCatalog:
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return load_candidates(path)


def test_official_sources_are_discovery_only_and_cross_version() -> None:
    catalog = load_candidates(FIXTURE)
    gold = json.loads((ROOT / "benchmarks/nl-tf-v1/bhsa-2021.json").read_text())
    assert catalog.corpus == "ETCBC/bhsa"
    assert catalog.target_data_version == "2021"
    assert len(catalog.cases) >= 16
    assert {c.capability for c in catalog.cases} == {"in_scope", "deferred"}
    assert {v.data_version for v in catalog.notebooks.values()} == {"2017", "unversioned"}
    # Reviewed tutorial cases are retained here for provenance after promotion.
    # A *new* overlap must be independently approved and cannot touch evaluation.
    gold_ids = {case["id"] for case in gold["cases"]}
    shared = {c.id for c in catalog.cases} & gold_ids
    assert shared == set(PROMOTED_IR)
    assert all(
        case["split"] != "evaluation"
        for case in gold["cases"]
        if case["id"] in shared
    )
    assert all(c.reported_count is not None for c in catalog.cases)
    assert {case.source_file for case in catalog.cases} == set(catalog.notebooks)
    assert all(case.source_cell >= 0 for case in catalog.cases)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.__setitem__("purpose", "gold"),
        lambda d: d.__setitem__("target_data_version", "2017"),
        lambda d: d.__setitem__("format_version", True),
        lambda d: d["cases"][1].__setitem__("id", d["cases"][0]["id"]),
        lambda d: d["cases"][0].__setitem__("source_cell", True),
        lambda d: d["cases"][0].__setitem__("reported_count", -1),
        lambda d: d["cases"][0].__setitem__("reported_count", True),
        lambda d: d["cases"][0].__setitem__("source_file", "fake.ipynb"),
        lambda d: d["cases"][0].__setitem__("capability", "gold"),
        lambda d: d["cases"][0].__setitem__("query", " "),
        lambda d: d["cases"][0].__setitem__("extra", "injection"),
        lambda d: d["notebooks"]["searchFromMQL.ipynb"].__setitem__("data_version", "2021"),
        lambda d: d["source_git_blobs"].__setitem__("otype.tf", "bad-hash"),
    ],
)
def test_invalid_or_forged_provenance_rejected(
    tmp_path: Path, mutate: Any
) -> None:
    data = copy.deepcopy(_read())
    mutate(data)
    with pytest.raises(ValueError):
        _load(tmp_path, data)


def test_unverified_counts_never_behave_as_gold(tiny_api: Any) -> None:
    case = load_candidates(FIXTURE).cases[0]
    candidate = replace(
        case,
        query="word sp=subs",
        reported_count=999999,
        capability="in_scope",
    )
    # Recorded notebook count is for another corpus run; this result is independent.
    assert run_candidate(tiny_api, candidate) == 3
    with pytest.raises(ValueError, match="limit"):
        run_candidate(tiny_api, candidate, max_rows=2)
    with pytest.raises(ValueError, match="invalid"):
        run_candidate(tiny_api, replace(candidate, query="word missing=x"))
    with pytest.raises(ValueError, match="deferred"):
        run_candidate(tiny_api, replace(candidate, capability="deferred"))


def test_candidate_source_check_detects_feature_edit_and_missing_source(
    tmp_path: Path,
) -> None:
    catalog = load_candidates(FIXTURE)
    directory = tmp_path / "2021"
    directory.mkdir()
    hashes = []
    for name, _ in catalog.source_git_blobs:
        payload = ("source:" + name).encode()
        (directory / name).write_bytes(payload)
        digest = hashlib.sha1(
            b"blob " + str(len(payload)).encode() + b"\0" + payload
        ).hexdigest()
        hashes.append((name, digest))
    fake = replace(catalog, source_git_blobs=tuple(hashes))
    verify_candidate_source(directory, fake)
    (directory / "gn.tf").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="source"):
        verify_candidate_source(directory, fake)
    (directory / "gn.tf").unlink()
    with pytest.raises(ValueError, match="source"):
        verify_candidate_source(directory, fake)
    with pytest.raises(ValueError, match="2021"):
        verify_candidate_source(tmp_path, fake)
