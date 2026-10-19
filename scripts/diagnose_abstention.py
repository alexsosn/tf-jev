"""Observe unchanged parser decisions on DEVELOPMENT only; never dump prompts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

from scripts.nl_benchmark_v2 import DEFAULT, load_benchmark
from tf_jev.decisions import (
    BackendError,
    Capabilities,
    ChoiceDecision,
    ChoiceQuestion,
    DecisionBackend,
    DecisionBatch,
    DecisionRequest,
    RawChoice,
    Receipt,
    validate_answers,
)
from tf_jev.parser import ParseResult, SemanticParser
from tf_jev.schema import extract_schema

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "reports/jev-rules-2026-10-20/corpus-source-sha256.json"
STAGE = re.compile(
    r"(?:shape|relation|edge|distance|output|verify|probe[0-4]|"
    r"atom[01]\.(?:type|count|pred[0-2]\.(?:feature|operator|count|value[0-2])))\Z"
)
ERRORS = {
    "authentication",
    "rate_limit",
    "timeout",
    "connection",
    "response",
    "http",
    "configuration",
    "closed",
}
REASONS = {
    "accepted",
    "invalid_request",
    "incomplete_schema_coverage",
    "backend_or_contract",
    "call_budget",
    "choice_budget",
    "context_budget",
    "no_candidates",
    "low_confidence",
    "integer_budget",
    "value_budget",
    "retrieval_seed_budget",
    "retrieval_overflow",
    "retrieval_miss",
    "duplicate_value",
    "intent",
    "candidate_mismatch",
    "compiler_rejected",
}


def _count(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


class TraceBackend:
    """Delegate unchanged; reports only request-bound, positional numeric data."""

    def __init__(self, backend: DecisionBackend) -> None:
        self.backend = backend
        self.calls: list[dict[str, Any]] = []
        # In-memory only, used to replay exact development shape controls.
        self.requests: list[DecisionRequest] = []

    @property
    def capabilities(self) -> Capabilities:
        return self.backend.capabilities

    def decide(self, request: DecisionRequest) -> DecisionBatch:
        self.requests.append(request)
        row: dict[str, Any] = dict(
            questions=[], error_kind=None, input_tokens=None, output_tokens=None
        )
        start = time.perf_counter()
        try:
            batch = self.backend.decide(request)
        except BackendError as error:
            row["error_kind"] = error.kind if error.kind in ERRORS else "other"
            raise
        except Exception:
            row["error_kind"] = "contract"
            raise
        else:
            try:
                if isinstance(batch.receipt, Receipt):
                    row["input_tokens"] = _count(batch.receipt.input_tokens)
                    row["output_tokens"] = _count(batch.receipt.output_tokens)
                raw = {}
                for name, answer in batch.decisions.items():
                    if not isinstance(answer, ChoiceDecision):
                        raise ValueError("not choice")
                    raw[name] = RawChoice(answer.selected, answer.probabilities)
                checked = validate_answers(request, raw, self.capabilities.probability_resolution)
                questions = []
                for name, question in request.questions.items():
                    answer = checked[name]
                    if not isinstance(question, ChoiceQuestion) or not isinstance(
                        answer, ChoiceDecision
                    ):
                        raise ValueError("not choice")
                    questions.append(
                        dict(
                            question=name if STAGE.fullmatch(name) else "redacted",
                            option_count=len(question.options),
                            selected_index=question.labels.index(answer.selected),
                            probabilities=[answer.probabilities[o.label] for o in question.options],
                            top_probability=answer.top_probability,
                            margin=answer.margin,
                        )
                    )
                row["questions"] = questions
            except Exception:
                # Observation never substitutes a response or exception in the
                # parser's own path; invalid answers remain its responsibility.
                row["error_kind"] = "contract"
            return batch
        finally:
            row["latency_s"] = max(0.0, time.perf_counter() - start)
            self.calls.append(row)


def summarize(result: ParseResult, calls: list[dict[str, Any]]) -> dict[str, Any]:
    last = calls[-1]["questions"][-1]["question"] if calls and calls[-1]["questions"] else None
    stopping = last if result.reason in ("low_confidence", "intent", "candidate_mismatch") else None
    complete = all(c["input_tokens"] is not None and c["output_tokens"] is not None for c in calls)
    inputs = sum(c["input_tokens"] for c in calls) if complete else None
    return dict(
        status=result.status.value,
        reason=result.reason if result.reason in REASONS else "redacted",
        confidence=result.confidence if math.isfinite(result.confidence) else None,
        last_observed_question=last,
        stopping_question=stopping,
        attempted_calls=len(calls),
        calls=calls,
        usage_complete=complete,
        input_tokens=inputs,
        output_tokens=sum(c["output_tokens"] for c in calls) if complete else None,
        estimated_cost_usd=inputs * 0.042 / 1_000_000 if inputs is not None else None,
    )


def verify_sources(directory: Path) -> dict[str, str]:
    if directory.name != "2021":
        raise ValueError("expected BHSA 2021 directory")
    load_benchmark().verify_source(directory)
    expected: dict[str, str] = json.loads(SOURCE_MANIFEST.read_text())
    actual = {p.name for p in directory.glob("*.tf") if p.is_file()}
    if actual != expected.keys():
        raise ValueError("full source inventory mismatch")
    for name, digest in expected.items():
        with (directory / name).open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != digest:
                raise ValueError("full corpus source mismatch")
    return expected


def _write(path: Path, report: Any) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("corpus", type=Path)
    cli.add_argument("--output", required=True, type=Path, help="new report directory")
    cli.add_argument("--max-cases", required=True, type=int)
    cli.add_argument("--live", action="store_true")
    args = cli.parse_args(argv)
    if not args.live or os.environ.get("TF_JEV_LIVE") != "1":
        raise ValueError("live diagnostics require --live and TF_JEV_LIVE=1")
    selected = load_benchmark().selected("development")
    if not 1 <= args.max_cases <= len(selected):
        raise ValueError("max-cases must be within development partition")
    if args.output.exists():
        raise ValueError("output must be new")
    sources = verify_sources(args.corpus)
    metadata = dict(
        package_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        benchmark_sha256=hashlib.sha256(DEFAULT.read_bytes()).hexdigest(),
        source_sha256=sources,
        partition="development",
        max_cases=args.max_cases,
        partition_cases=len(selected),
        complete=args.max_cases == len(selected),
        selection_method="canonical_prefix",
        python=platform.python_version(),
        text_fabric=version("text-fabric"),
        typesafe_sdk=version("typesafe-sdk"),
        model="jev-1.13.0",
        started_utc=datetime.now(UTC).isoformat(),
        min_probability=0.8,
        min_margin=0.2,
    )
    args.output.mkdir(parents=True)
    api = Fabric(locations=str(args.corpus), silent="deep").load("", silent="deep")
    if not api:
        raise ValueError("native corpus load failed")
    schema = extract_schema(api)
    metadata["schema_key"] = schema.identity.key
    from tf_jev.jev import JevBackend

    representatives = {}
    rows = []
    with JevBackend() as backend:
        for case in selected[: args.max_cases]:
            trace = TraceBackend(backend)
            result = SemanticParser(schema, trace).parse(case["request"])
            row = dict(id=case["id"], family=case["family"], **summarize(result, trace.calls))
            rows.append(row)
            if case["family"] not in representatives and trace.requests:
                representatives[case["family"]] = (case["id"], trace.requests[0])
            # Checkpoint completed cases, while preserving honest completeness.
            _write(args.output / "trace.json", dict(metadata, cases=rows, trace_complete=False))
        _write(
            args.output / "trace.json",
            dict(
                metadata,
                cases=rows,
                trace_complete=True,
                stopping_questions=dict(
                    Counter(r["stopping_question"] or "non_decision_stop" for r in rows)
                ),
            ),
        )
        from scripts.diagnostic_probes import run_probes

        probes = run_probes(backend, list(representatives.values()))
        _write(args.output / "probes.json", dict(metadata, probes=probes))
    print("development traces:", len(rows), "probe attempts:", len(probes), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
