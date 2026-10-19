"""Source-verified full frozen Jev/rule measurement. Requires explicit live opt-in."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

from scripts.evaluation_report import compare, decision, retrieval_audit
from scripts.nl_benchmark_v2 import DEFAULT, load_benchmark
from scripts.rule_baseline import BHSARuleParser
from scripts.semantic_evaluation import evaluate
from tf_jev.decisions import BackendError, DecisionBackend, DecisionBatch, DecisionRequest
from tf_jev.parser import SemanticParser
from tf_jev.schema import extract_schema


class MeteredBackend:
    def __init__(self, backend: DecisionBackend) -> None:
        self.backend = backend
        self.attempts: list[dict[str, Any]] = []

    @property
    def capabilities(self) -> Any:
        return self.backend.capabilities

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        row: dict[str, Any] = dict(input_tokens=None, output_tokens=None, error_kind=None)
        start = time.perf_counter()
        try:
            batch = self.backend.decide(request)
            row.update(
                input_tokens=batch.receipt.input_tokens, output_tokens=batch.receipt.output_tokens
            )
            return batch
        except BackendError as error:
            row["error_kind"] = (
                error.kind
                if error.kind
                in (
                    "authentication",
                    "rate_limit",
                    "timeout",
                    "connection",
                    "response",
                    "http",
                    "configuration",
                    "closed",
                )
                else "other"
            )
            raise
        except Exception:
            row["error_kind"] = "contract"
            raise
        finally:
            row["latency_s"] = max(0.0, time.perf_counter() - start)
            self.attempts.append(row)


class RecordingParser:
    def __init__(self, parser: Any, meter: MeteredBackend | None) -> None:
        self.parser, self.meter = parser, meter
        self.schema = parser.schema
        self.attempts: list[list[dict[str, Any]]] = []
        self.predictions: list[dict[str, Any]] = []

    def parse(self, request: str) -> Any:
        start = len(self.meter.attempts) if self.meter else 0
        result = self.parser.parse(request)
        self.attempts.append(self.meter.attempts[start:] if self.meter else [])
        # Local review-only artifact, never transmitted to a model or included in
        # public measurements. Allows independent NL/IR adjudication after freeze.
        self.predictions.append(dict(query=result.query, projection=result.projection))
        return result


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("corpus", type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--private-review", required=True, type=Path)
    cli.add_argument("--live", action="store_true")
    args = cli.parse_args(argv)
    if not args.live or os.environ.get("TF_JEV_LIVE") != "1":
        raise ValueError("live measurement requires --live and TF_JEV_LIVE=1")
    if args.output.exists() or args.private_review.exists():
        raise ValueError("measurement paths must be new")
    benchmark = load_benchmark()
    if args.corpus.name != benchmark.corpus["version"]:
        raise ValueError("corpus version mismatch")
    benchmark.verify_source(args.corpus)
    metadata: dict[str, Any] = dict(
        package_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        benchmark_sha256=hashlib.sha256(DEFAULT.read_bytes()).hexdigest(),
        source_sha256=benchmark.source_sha256,
        python=platform.python_version(),
        text_fabric=version("text-fabric"),
        typesafe_sdk=version("typesafe-sdk"),
        started_utc=datetime.now(UTC).isoformat(),
        pricing=dict(
            input_usd_per_million=0.042,
            output_usd_per_million=0.0,
            source="https://typesafe.ai/",
            checked="2026-10-20",
            kind="list_estimate",
        ),
    )
    args.output.mkdir(parents=True)
    args.private_review.mkdir(parents=True, mode=0o700)
    api = Fabric(locations=str(args.corpus), silent="deep").load("", silent="deep")
    if not api:
        raise ValueError("native corpus load failed")
    started = time.perf_counter()
    schema = extract_schema(api)
    metadata["schema_extraction_s"] = time.perf_counter() - started
    # Import/create the credential-bearing client only after source verification.
    from tf_jev.jev import JevBackend

    reports = {}
    with JevBackend() as backend:
        meter = MeteredBackend(backend)
        for system in ("jev", "rules"):
            for partition in ("development", "heldout"):
                parser = RecordingParser(
                    SemanticParser(schema, meter) if system == "jev" else BHSARuleParser(schema),
                    meter if system == "jev" else None,
                )
                report = evaluate(
                    benchmark,
                    parser,
                    api,
                    partition=partition,
                    input_usd_per_million=0.042,
                    output_usd_per_million=0.0,
                )
                report.update(metadata)
                report["system"] = system
                report["selection"] = dict(complete=True, selection_method="whole_partition")
                report["retrieval_audit"] = retrieval_audit(benchmark, schema, partition)
                for row, attempts in zip(report["cases"], parser.attempts, strict=True):
                    row["attempted_backend_calls"] = len(attempts)
                    row["backend_errors"] = [a["error_kind"] for a in attempts if a["error_kind"]]
                    complete = all(
                        a["input_tokens"] is not None and a["output_tokens"] is not None
                        for a in attempts
                    )
                    row["metering_complete"] = complete
                    row["input_tokens"] = (
                        sum(a["input_tokens"] for a in attempts) if complete else None
                    )
                    row["output_tokens"] = (
                        sum(a["output_tokens"] for a in attempts) if complete else None
                    )
                    row["estimated_cost_usd"] = (
                        row["input_tokens"] * 0.042 / 1_000_000 if complete else None
                    )
                report["estimated_cost_usd_complete"] = all(
                    c["metering_complete"] for c in report["cases"]
                )
                report["estimated_cost_usd"] = (
                    sum(c["estimated_cost_usd"] for c in report["cases"])
                    if report["estimated_cost_usd_complete"]
                    else None
                )
                report["decision"] = decision(report)
                name = f"{system}-{partition}"
                reports[name] = report
                (args.output / f"{name}.json").write_text(
                    json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
                )
                (args.private_review / f"{name}.json").write_text(
                    json.dumps(parser.predictions, ensure_ascii=False) + "\n"
                )
                print(
                    name,
                    report["total"],
                    report["result_equivalent"],
                    report["safe_negative"],
                    report["status_counts"],
                    flush=True,
                )
    paired = {
        p: compare(reports[f"jev-{p}"], reports[f"rules-{p}"]) for p in ("development", "heldout")
    }
    (args.output / "paired.json").write_text(json.dumps(paired, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
