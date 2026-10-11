"""RED-first gates for the pinned, single-session BHSA replay harness (#10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import scripts.bhsa_replay as runner

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "benchmarks/nl-tf-v1/bhsa-2021.json"
CANDIDATES = ROOT / "benchmarks/nl-tf-v1/tutorial-candidates.json"


def _stub_sources(monkeypatch: pytest.MonkeyPatch, tiny_api: Any) -> list[str]:
    calls: list[str] = []
    monkeypatch.setattr(runner, "verify_source", lambda *_: calls.append("gold_source"))
    monkeypatch.setattr(runner, "verify_candidate_source", lambda *_: calls.append("candidate_source"))

    def loader(*_: Any, **__: Any) -> Any:
        calls.append("load_api")
        return tiny_api

    monkeypatch.setattr(runner, "load_api", loader)
    return calls


def test_single_session_checks_sources_first_and_never_executes_deferred(
    monkeypatch: pytest.MonkeyPatch, tiny_api: Any, tmp_path: Path
) -> None:
    calls = _stub_sources(monkeypatch, tiny_api)
    monkeypatch.setattr(
        runner,
        "check_gold",
        lambda api, case: calls.append("gold:" + case.id) or case.expected_count,
    )
    monkeypatch.setattr(
        runner,
        "run_candidate",
        lambda api, case: calls.append("candidate:" + case.id) or len(case.id),
    )
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
    assert report["source_commit"] == runner.UPSTREAM_COMMIT
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
            return runner.run_candidate_native(
                api, case, query_override="word gn=f nu=pl sp=subs"
            )
        return 0

    monkeypatch.setattr(runner, "run_candidate", native)
    report = runner.replay(tmp_path / "2021", GOLD, CANDIDATES)
    match = next(
        x for x in report["observations"] if x["id"] == "feminine-plural-substantives"
    )
    assert match["observed_2021_rows"] == 1
    assert match["historical_notebook_rows"] == 5992
    assert not match["agrees_with_notebook"]
