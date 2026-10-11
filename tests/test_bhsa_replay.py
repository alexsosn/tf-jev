"""RED-first gates for the pinned, single-session BHSA replay harness (#10)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import scripts.bhsa_replay as runner
from scripts.nl_candidates import UPSTREAM_COMMIT
from scripts.nl_candidates import run_candidate as native_candidate

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "benchmarks/nl-tf-v1/bhsa-2021.json"
CANDIDATES = ROOT / "benchmarks/nl-tf-v1/tutorial-candidates.json"


def _stub_sources(monkeypatch: pytest.MonkeyPatch, tiny_api: Any) -> list[str]:
    calls: list[str] = []
    monkeypatch.setattr(runner, "verify_source", lambda *_: calls.append("gold_source"))
    monkeypatch.setattr(
        runner, "verify_candidate_source", lambda *_: calls.append("candidate_source")
    )

    def loader(*_: Any, **__: Any) -> Any:
        calls.append("load_api")
        return tiny_api

    monkeypatch.setattr(runner, "load_api", loader)
    return calls


def test_single_session_checks_sources_first_and_never_executes_deferred(
    monkeypatch: pytest.MonkeyPatch, tiny_api: Any, tmp_path: Path
) -> None:
    calls = _stub_sources(monkeypatch, tiny_api)
    def checked_gold(api: Any, case: Any) -> int:
        calls.append("gold:" + case.id)
        assert case.expected_count is not None
        return case.expected_count

    def checked_candidate(api: Any, case: Any) -> int:
        calls.append("candidate:" + case.id)
        return len(case.id)

    monkeypatch.setattr(runner, "check_gold", checked_gold)
    monkeypatch.setattr(runner, "run_candidate", checked_candidate)
    report = runner.replay(tmp_path / "2021", GOLD, CANDIDATES)
    assert calls[:3] == ["gold_source", "candidate_source", "load_api"]
    assert calls.count("load_api") == 1
    assert len([x for x in calls if x.startswith("gold:")]) == 6
    assert len([x for x in calls if x.startswith("candidate:")]) == 14
    assert report["format_version"] == 1
    assert report["corpus"] == "ETCBC/bhsa"
    assert report["data_version"] == "2021"
    assert report["gold_checked"] == 6
    assert report["candidate_checked"] == 14
    assert len(report["observations"]) == 14
    assert report["source_commit"] == UPSTREAM_COMMIT
    for key in ("gold_fixture_sha256", "candidate_fixture_sha256"):
        assert len(report[key]) == 64
    assert all(x["observed_2021_rows"] > 0 for x in report["observations"])
    assert {x["notebook_data_version"] for x in report["observations"]} == {
        "2017", "unversioned"
    }
    assert len(json.dumps(report)) < 12000
    assert "query" not in report["observations"][0]
    assert "result_nodes" not in report


def test_source_failure_precedes_all_search(
    monkeypatch: pytest.MonkeyPatch, tiny_api: Any, tmp_path: Path
) -> None:
    calls = _stub_sources(monkeypatch, tiny_api)

    def bad(_: Path, __: Any) -> None:
        raise ValueError("source mismatch")

    monkeypatch.setattr(runner, "verify_candidate_source", bad)
    with pytest.raises(ValueError, match="source mismatch"):
        runner.replay(tmp_path / "2021", GOLD, CANDIDATES)
    assert calls == ["gold_source"]


def test_gold_count_failure_prevents_candidate_execution(
    monkeypatch: pytest.MonkeyPatch, tiny_api: Any, tmp_path: Path
) -> None:
    calls = _stub_sources(monkeypatch, tiny_api)

    def bad(api: Any, case: Any) -> int:
        raise ValueError("native gold count mismatch")

    monkeypatch.setattr(runner, "check_gold", bad)
    monkeypatch.setattr(
        runner,
        "run_candidate",
        lambda api, case: pytest.fail("candidate must not run after invalid gold"),
    )
    with pytest.raises(ValueError, match="gold count mismatch"):
        runner.replay(tmp_path / "2021", GOLD, CANDIDATES)
    assert calls == ["gold_source", "candidate_source", "load_api"]


def test_report_writing_is_atomic_and_never_clobbers_gold_fixture(tmp_path: Path) -> None:
    report = {"format_version": 1, "observations": []}
    output = tmp_path / "report.json"
    runner.write_report(output, report, protected_paths=(GOLD, CANDIDATES))
    assert json.loads(output.read_text()) == report
    assert len(list(tmp_path.iterdir())) == 1
    with pytest.raises(ValueError, match="fixture"):
        runner.write_report(GOLD, report, protected_paths=(GOLD, CANDIDATES))
    with pytest.raises(ValueError, match="fixture"):
        runner.write_report(CANDIDATES, report, protected_paths=(GOLD, CANDIDATES))


def test_true_tiny_native_count_has_no_dependency_on_notebook_history(
    monkeypatch: pytest.MonkeyPatch, tiny_api: Any, tmp_path: Path
) -> None:
    _stub_sources(monkeypatch, tiny_api)
    monkeypatch.setattr(runner, "check_gold", lambda *_: 0)

    def native(api: Any, case: Any) -> int:
        if case.id == "feminine-plural-substantives":
            return native_candidate(api, replace(case, query="word gn=f nu=pl sp=subs"))
        return 0

    monkeypatch.setattr(runner, "run_candidate", native)
    report = runner.replay(tmp_path / "2021", GOLD, CANDIDATES)
    match = next(
        x for x in report["observations"] if x["id"] == "feminine-plural-substantives"
    )
    assert match["observed_2021_rows"] == 1
    assert match["historical_notebook_rows"] == 5992
    assert not match["agrees_with_notebook"]


def test_native_reference_is_durable_and_distinct_from_semantic_gold(
    tmp_path: Path,
) -> None:
    reference = ROOT / "benchmarks/nl-tf-v1/native-observations-2021.json"
    report = json.loads(reference.read_text(encoding="utf-8"))
    assert report["purpose"] == "native-replay-not-gold-promotion"
    assert report["candidate_checked"] == 14
    assert report["gold_checked"] == 6
    by_id = {o["id"]: o for o in report["observations"]}
    assert by_id["pp-prep-adj-noun"]["observed_2021_rows"] == 61
    assert by_id["pp-prep-adj-noun"]["historical_notebook_rows"] == 64
    assert not by_id["pp-prep-adj-noun"]["agrees_with_notebook"]
    assert "gold_query" not in reference.read_text(encoding="utf-8")
    runner.verify_reference_report(report, reference)
    changed = json.loads(json.dumps(report))
    changed["observations"][0]["observed_2021_rows"] += 1
    with pytest.raises(ValueError, match="native reference"):
        runner.verify_reference_report(changed, reference)
    changed["observations"][0]["observed_2021_rows"] -= 1
    changed["candidate_fixture_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="native reference"):
        runner.verify_reference_report(changed, reference)
    changed = json.loads(json.dumps(report))
    changed["observations"].pop()
    with pytest.raises(ValueError, match="native reference"):
        runner.verify_reference_report(changed, reference)


def test_native_reference_rejects_wrong_types_even_if_python_would_equate_them(
    tmp_path: Path,
) -> None:
    reference = tmp_path / "ref.json"
    reference.write_text('{"candidate_checked": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="native reference"):
        runner.verify_reference_report({"candidate_checked": True}, reference)
