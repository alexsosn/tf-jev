"""Deterministic benchmark contracts, including real native TF failures."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from scripts.nl_benchmark_v2 import BenchmarkError, execute, load_benchmark, signature
from tests.conformance.tf_harness import build_tiny_corpus, load_api


def artifact() -> dict[str, Any]:
    return {
        "version": "nl-tf-v2",
        "corpus": {"name": "BHSA", "version": "2021", "text_fabric": "13.1.0"},
        "features": ["sp"],
        "source_sha256": {name + ".tf": "0" * 64 for name in ("otype", "oslots", "otext", "sp")},
        "cases": [
            {
                "id": "dev-01",
                "family": "pos",
                "partition": "development",
                "request": "Return verbs.",
                "expected": "supported",
                "rationale": "sp=verb",
                "gold": {
                    "query": "word sp=verb",
                    "projection": [0],
                    "count": 3,
                    "signature": signature([(3,), (6,), (8,)], (0,)),
                },
            },
            {
                "id": "held-01",
                "family": "ambiguity",
                "partition": "heldout",
                "request": "Find mothers.",
                "expected": "ambiguous",
                "rationale": "Two meanings.",
                "interpretations": ["Lexical mothers", "Dependency mother edges"],
            },
        ],
    }


def write(tmp_path: Path, data: dict[str, Any]) -> Path:
    import json

    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_partition_defaults_to_development(tmp_path: Path) -> None:
    benchmark = load_benchmark(write(tmp_path, artifact()))
    assert [c["id"] for c in benchmark.selected()] == ["dev-01"]
    assert [c["id"] for c in benchmark.selected("heldout")] == ["held-01"]
    with pytest.raises(BenchmarkError):
        benchmark.selected("typo")


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate",
        "family",
        "projection",
        "bool",
        "gold",
        "digest",
        "path",
        "class",
        "alternatives",
        "count",
        "features",
        "unknown",
    ],
)
def test_invalid_artifact_rejected(tmp_path: Path, fault: str) -> None:
    data = copy.deepcopy(artifact())
    first, second = data["cases"]
    if fault == "duplicate":
        second["id"] = first["id"]
    elif fault == "family":
        second["family"] = first["family"]
    elif fault == "projection":
        first["gold"]["projection"] = [0, 0]
    elif fault == "bool":
        first["gold"]["projection"] = [True]
    elif fault == "gold":
        second["gold"] = first["gold"]
    elif fault == "digest":
        data["source_sha256"]["sp.tf"] = "invalid"
    elif fault == "path":
        data["source_sha256"]["../sp.tf"] = "0" * 64
    elif fault == "class":
        first["expected"] = "wrong"
    elif fault == "alternatives":
        second["interpretations"] = ["same", "same"]
    elif fault == "count":
        first["gold"]["count"] = True
    elif fault == "features":
        data["features"] = ["missing"]
    elif fault == "unknown":
        first["gld"] = first["gold"]
    with pytest.raises(BenchmarkError):
        load_benchmark(write(tmp_path, data))


def test_signature_has_set_semantics_and_ordered_roles() -> None:
    assert signature([(1, 8), (1, 9), (2, 8)], (0,)) == signature([(2,), (1,)], (0,))
    assert signature([(1, 2)], (0, 1)) != signature([(1, 2)], (1, 0))
    assert signature([], (0,)) != signature([], (0, 1))
    with pytest.raises(BenchmarkError):
        signature([(1,)], (1,))


def test_execute_native_errors_and_projection(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    api = load_api(tmp_path)
    count, digest = execute(api, "clause\n  word sp=verb", (0,))
    assert count == 2
    assert digest == signature([(14,), (15,)], (0,))
    assert execute(api, "word sp=nonexistent", (0,)) == (0, signature([], (0,)))
    with pytest.raises(BenchmarkError):
        execute(api, "clause\n/without/\n  phrase nonexistent=bad\n/-/", (0,))
    with pytest.raises(BenchmarkError):
        execute(api, "word", (0,), limit=2)
    with pytest.raises(BenchmarkError):
        execute(api, "word", (1,))


def test_frozen_benchmark_contract() -> None:
    benchmark = load_benchmark(Path(__file__).parents[1] / "benchmarks/nl-tf-v2/bhsa-2021.json")
    assert len(benchmark.cases) >= 90
    assert {c["expected"] for c in benchmark.cases} == {"supported", "ambiguous", "unsupported"}
    assert len(benchmark.selected("heldout")) >= 25


def test_bhsa_gold(bhsa_api: Any, bhsa_dir: Path) -> None:
    benchmark = load_benchmark(Path(__file__).parents[1] / "benchmarks/nl-tf-v2/bhsa-2021.json")
    benchmark.verify_source(bhsa_dir)
    assert bhsa_api.TF.load(" ".join(benchmark.features), add=True, silent="deep")
    bhsa_api = bhsa_api.TF.api
    for case in benchmark.cases:
        if case["expected"] == "supported":
            gold = case["gold"]
            assert execute(bhsa_api, gold["query"], tuple(gold["projection"])) == (
                gold["count"],
                gold["signature"],
            ), case["id"]


def test_equivalent_native_forms_and_wrong_answer(tmp_path: Path) -> None:
    build_tiny_corpus(tmp_path)
    api = load_api(tmp_path)
    expected = execute(api, "clause\n  word sp=verb", (0,))
    assert execute(api, "w:word sp=verb\nc:clause\nw ]] c", (1,)) == expected
    assert execute(api, "clause\n  word sp=prep", (0,)) != expected


def test_source_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Test source validation independently of the installed runtime version.
    monkeypatch.setattr("scripts.nl_benchmark_v2.version", lambda _: "13.1.0")
    benchmark = load_benchmark(write(tmp_path, artifact()))
    with pytest.raises(BenchmarkError, match="source unavailable"):
        benchmark.verify_source(tmp_path)
    for name in benchmark.source_sha256:
        (tmp_path / name).write_text("changed")
    with pytest.raises(BenchmarkError, match="source mismatch"):
        benchmark.verify_source(tmp_path)


@pytest.mark.parametrize("field", ["partition", "expected"])
def test_wrong_classification_types_rejected(tmp_path: Path, field: str) -> None:
    data = artifact()
    data["cases"][0][field] = []
    with pytest.raises(BenchmarkError):
        load_benchmark(write(tmp_path, data))


def test_original_evaluation_requests_remain_sealed() -> None:
    import json

    root = Path(__file__).parents[1] / "benchmarks"
    old = json.loads((root / "nl-tf-v1/bhsa-2021.json").read_text())
    benchmark = load_benchmark(root / "nl-tf-v2/bhsa-2021.json")
    sealed = {c["request"] for c in benchmark.selected("heldout")}
    assert {c["request"] for c in old["cases"] if c["split"] == "evaluation"} <= sealed
    assert not sealed & {c["request"] for c in benchmark.selected()}


def test_empty_result_still_validates_output_columns(tiny_api: Any) -> None:
    with pytest.raises(BenchmarkError, match="projection"):
        execute(tiny_api, "word sp=nonexistent", (1,))


def test_unpinned_runtime_rejected_before_source_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    benchmark = load_benchmark(write(tmp_path, artifact()))
    monkeypatch.setattr("scripts.nl_benchmark_v2.version", lambda _: "13.1.1")

    def forbidden_read(path: Path) -> bytes:
        pytest.fail("version mismatch must precede source reads")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(BenchmarkError, match="Text-Fabric version mismatch"):
        benchmark.verify_source(tmp_path)
