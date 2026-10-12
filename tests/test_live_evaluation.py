"""RED-first opt-in Jev entrypoint tests on a genuinely saved tiny TF corpus.

Fake decisions validate CLI/source-verification wiring, never model quality.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from scripts.nl_benchmark_v2 import Benchmark, BenchmarkError, execute
from scripts.run_jev_evaluation import main, run_evaluation
from tests.conformance.tf_harness import build_tiny_corpus, load_api
from tf_jev.decisions import (
    Capabilities,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBatch,
    DecisionRequest,
    Receipt,
)


class AbstainingBackend:
    def __init__(self) -> None:
        self.requests: list[DecisionRequest] = []

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(max_options=255)

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        self.requests.append(request)
        question = request.questions["shape"]
        assert isinstance(question, ChoiceQuestion)
        chosen = next(o for o in question.options
                      if (o.description or "").startswith("unsupported:"))
        probabilities = {
            o.label: (1.0 if o.label == chosen.label else 0.0)
            for o in question.options
        }
        return DecisionBatch(
            {"shape": ChoiceDecision(chosen.label, probabilities)},
            Receipt("scripted", "test-only", input_tokens=7, output_tokens=3),
        )


def fixture(tmp_path: Path) -> tuple[Path, Benchmark]:
    corpus = tmp_path / "2021"
    corpus.mkdir()
    build_tiny_corpus(corpus)
    api: Any = load_api(corpus)
    count, digest = execute(api, "word sp=verb", (0,))
    names = ("otype", "oslots", "otext", "sp")
    hashes = {
        name + ".tf": hashlib.sha256((corpus / (name + ".tf")).read_bytes()).hexdigest()
        for name in names
    }
    benchmark = Benchmark(
        {"name": "BHSA", "version": "2021", "text_fabric": "13.1.0"},
        ("sp",), hashes,
        (
            {"id": "dev-a", "family": "pos", "partition": "development",
             "request": "Return verbs.", "expected": "supported",
             "rationale": "private gold", "gold": {
                 "query": "word sp=verb", "projection": [0],
                 "count": count, "signature": digest}},
            {"id": "dev-b", "family": "negative", "partition": "development",
             "request": "Give a translation.", "expected": "unsupported",
             "rationale": "private rationale"},
            {"id": "held-c", "family": "held", "partition": "heldout",
             "request": "Find impossibilities.", "expected": "unsupported",
             "rationale": "private rationale"},
        ),
    )
    return corpus, benchmark


def test_verified_tiny_native_run_discloses_partial_partition(tmp_path: Path) -> None:
    corpus, benchmark = fixture(tmp_path)
    backend = AbstainingBackend()
    report = run_evaluation(corpus, benchmark, backend, partition="development", max_cases=1)
    assert report["selection"] == {
        "partition_cases": 2, "evaluated_cases": 1, "complete": False,
        "selection_method": "canonical_prefix",
    }
    assert report["partition"] == "development"
    assert report["total"] == 1
    assert report["status_counts"] == {"unsupported": 1}
    assert len(backend.requests) == 1
    assert backend.requests[0].context["request"] == "Return verbs."
    assert "private" not in str(backend.requests[0].context)
    assert report["cases"][0]["input_tokens"] == 7
    assert report["cases"][0]["estimated_cost_usd"] is None


def test_full_small_partition_and_heldout_isolation(tmp_path: Path) -> None:
    corpus, benchmark = fixture(tmp_path)
    backend = AbstainingBackend()
    report = run_evaluation(corpus, benchmark, backend, partition="heldout", max_cases=1)
    assert report["selection"]["complete"] is True
    assert report["safe_negative"] == 1
    assert [r.context["request"] for r in backend.requests] == ["Find impossibilities."]


def test_source_drift_rejected_before_decision(tmp_path: Path) -> None:
    corpus, benchmark = fixture(tmp_path)
    (corpus / "sp.tf").write_text("@node\\n@valueType=str\\n\\n1\\taltered\\n")
    backend = AbstainingBackend()
    with pytest.raises(BenchmarkError, match="source mismatch"):
        run_evaluation(corpus, benchmark, backend, partition="development", max_cases=1)
    assert not backend.requests


@pytest.mark.parametrize("amount", [0, -1, True, 1.5, 4])
def test_bad_limit_rejected_before_load(
    tmp_path: Path, amount: Any
) -> None:
    corpus, benchmark = fixture(tmp_path)
    backend = AbstainingBackend()
    with pytest.raises(ValueError, match="max_cases"):
        run_evaluation(corpus, benchmark, backend, partition="development", max_cases=amount)
    assert not backend.requests


def test_cli_double_opt_in_required_and_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "result.json"
    monkeypatch.delenv("TF_JEV_LIVE", raising=False)
    with pytest.raises(ValueError, match="opt-in"):
        main([str(tmp_path / "no-corpus"), "--max-cases", "1", "--output", str(out)])
    with pytest.raises(ValueError, match="opt-in"):
        main([str(tmp_path / "no-corpus"), "--max-cases", "1",
              "--output", str(out), "--live"])
    assert not out.exists()
