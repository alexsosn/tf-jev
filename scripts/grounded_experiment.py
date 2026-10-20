"""Preregistered opt-in grounded-v1 experiment, reusing existing evaluation/metering."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import subprocess
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

from scripts.diagnose_abstention import _write, verify_sources
from scripts.measure_comparison import MeteredBackend, RecordingParser
from scripts.nl_benchmark_v2 import execute, load_benchmark
from scripts.semantic_evaluation import evaluate
from tf_jev.decisions import DecisionBatch, DecisionRequest
from tf_jev.grounded import Gate, GroundedParser, GroundedPolicy
from tf_jev.schema import extract_schema

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/grounded-v1/bhsa-2021.json"
DIGEST = "0a9f8d1a1808b8cfd07a1815bfcaba3ae34381d55dec3475039e1ebbe32f7b27"
POLICIES = dict(
    strict=GroundedPolicy(),
    exploratory=GroundedPolicy(
        shape_gate=Gate(0.9, 0.3), type_gate=Gate(0.6, 0.3), feature_gate=Gate(0.6, 0.3)
    ),
    guarded=GroundedPolicy(
        shape_gate=Gate(0.9, 0.5), type_gate=Gate(0.7, 0.3), feature_gate=Gate(0.6, 0.3)
    ),
)


class StageMeter(MeteredBackend):
    """Only code-authored stage IDs; never labels, descriptions or state."""

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        try:
            return super().decide(request)
        finally:
            self.attempts[-1]["stages"] = list(request.questions)


def select_policy(reports: dict[str, dict[str, Any]]) -> str:
    eligible = [
        k
        for k, r in reports.items()
        if r["unsafe_supported_on_negative"] == 0
        and r["result_equivalent"] == r["status_counts"].get("supported", 0)
    ]
    return (
        max(
            eligible,
            key=lambda k: (
                reports[k]["result_equivalent"],
                {"strict": 3, "guarded": 2, "exploratory": 1}[k],
            ),
        )
        if eligible
        else "strict"
    )


def account(report: dict[str, Any], parser: RecordingParser) -> None:
    for row, attempts in zip(report["cases"], parser.attempts, strict=True):
        complete = all(
            a["input_tokens"] is not None and a["output_tokens"] is not None for a in attempts
        )
        row.update(
            attempted_backend_calls=len(attempts),
            attempts=attempts,
            metering_complete=complete,
            input_tokens=sum(a["input_tokens"] for a in attempts) if complete else None,
            output_tokens=sum(a["output_tokens"] for a in attempts) if complete else None,
        )
        row["estimated_cost_usd"] = row["input_tokens"] * 0.042 / 1e6 if complete else None
    complete = all(c["metering_complete"] for c in report["cases"])
    report["estimated_cost_usd_complete"] = complete
    report["estimated_cost_usd"] = (
        sum(c["estimated_cost_usd"] for c in report["cases"]) if complete else None
    )


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("corpus", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--private-review", type=Path, required=True)
    cli.add_argument("--phase", choices=["calibration", "evaluation"], required=True)
    cli.add_argument("--policy", choices=list(POLICIES))
    cli.add_argument("--live", action="store_true")
    args = cli.parse_args(argv)
    if not args.live or os.environ.get("TF_JEV_LIVE") != "1":
        raise ValueError("explicit live opt-in required")
    if args.output.exists() or args.private_review.exists() or args.output == args.private_review:
        raise ValueError("output and private review paths must be distinct and new")
    if args.phase == "evaluation" and args.policy is None:
        raise ValueError("evaluation requires a frozen policy")
    if args.phase == "calibration" and args.policy is not None:
        raise ValueError("calibration uses all preregistered policies")
    if hashlib.sha256(BENCHMARK.read_bytes()).hexdigest() != DIGEST:
        raise ValueError("frozen benchmark mismatch")
    sources = verify_sources(args.corpus)
    benchmark = load_benchmark(BENCHMARK)
    benchmark.verify_source(args.corpus)
    api = Fabric(locations=str(args.corpus), silent="deep").load("", silent="deep")
    if not api:
        raise ValueError("native corpus load failed")
    schema = extract_schema(api)
    partition = "development" if args.phase == "calibration" else "heldout"
    # Only the requested partition is accessed for model evaluation. Native gold
    # is verified independently before any credential-bearing client is created.
    for case in benchmark.selected(partition):
        if case["expected"] == "supported":
            gold = case["gold"]
            if execute(api, gold["query"], tuple(gold["projection"])) != (
                gold["count"],
                gold["signature"],
            ):
                raise ValueError("native gold drift")
    metadata = dict(
        dataset="grounded-v1",
        benchmark_sha256=DIGEST,
        source_sha256=sources,
        package_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        python=platform.python_version(),
        text_fabric=version("text-fabric"),
        typesafe_sdk=version("typesafe-sdk"),
        model="jev-1.13.0",
        phase=args.phase,
    )
    args.output.mkdir(parents=True)
    args.private_review.mkdir(parents=True, mode=0o700)
    from tf_jev.jev import JevBackend

    reports = {}
    names = list(POLICIES) if args.phase == "calibration" else [args.policy]
    with JevBackend() as backend:
        meter = StageMeter(backend)
        for name in names:
            parser = RecordingParser(GroundedParser(schema, meter, POLICIES[name]), meter)
            report = evaluate(
                benchmark,
                parser,
                api,
                partition=partition,
                input_usd_per_million=0.042,
                output_usd_per_million=0.0,
            )
            account(report, parser)
            report.update(
                metadata,
                policy_name=name,
                policy=asdict(POLICIES[name]),
                selection=dict(complete=True, selection_method="whole_partition"),
            )
            _write(args.output / (name + ".json"), report)
            _write(args.private_review / (name + ".json"), parser.predictions)
            reports[name] = report
            print(
                name,
                report["result_equivalent"],
                report["safe_negative"],
                report["status_counts"],
                flush=True,
            )
    if args.phase == "calibration":
        _write(
            args.output / "selection.json",
            dict(
                metadata,
                selected_policy=select_policy(reports),
                requires_independent_intent_review=True,
            ),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
