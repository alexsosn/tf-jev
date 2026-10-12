"""Run a small, source-verified BHSA semantic evaluation with opt-in live Jev.

No live requests without BOTH --live and TF_JEV_LIVE=1. The installed package
does not ship this checkout-only benchmarking script.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

from scripts.nl_benchmark_v2 import Benchmark, load_benchmark
from scripts.semantic_evaluation import evaluate
from tf_jev.decisions import DecisionBackend
from tf_jev.parser import SemanticParser
from tf_jev.schema import extract_schema


def run_evaluation(
    directory: Path,
    benchmark: Benchmark,
    backend: DecisionBackend,
    *,
    partition: str = "development",
    max_cases: int,
    input_usd_per_million: float | None = None,
    output_usd_per_million: float | None = None,
) -> dict[str, Any]:
    """Verify source before native evaluation; limit each costly parser invocation."""
    selection = benchmark.selected(partition)
    if type(max_cases) is not int or not 1 <= max_cases <= len(selection):
        raise ValueError("max_cases must be a positive integer within the partition")
    if not isinstance(directory, Path) or directory.name != benchmark.corpus["version"]:
        raise ValueError("expected version-named Text-Fabric source directory")
    if (input_usd_per_million is None) != (output_usd_per_million is None):
        raise ValueError("both token prices must be provided together")
    benchmark.verify_source(directory)
    api: Any = Fabric(locations=str(directory), silent="deep").load("", silent="deep")
    if not api:
        raise ValueError("Text-Fabric failed to load the verified corpus")
    schema = extract_schema(api)
    parser = SemanticParser(schema, backend)
    # Reuse the immutable, validated benchmark schema but select an honest prefix;
    # the evaluator only passes each case's request prose to the backend.
    chosen = Benchmark(
        benchmark.corpus, benchmark.features, benchmark.source_sha256, selection[:max_cases]
    )
    report = evaluate(
        chosen, parser, api, partition=partition,
        input_usd_per_million=input_usd_per_million,
        output_usd_per_million=output_usd_per_million,
    )
    report["selection"] = {
        "partition_cases": len(selection),
        "evaluated_cases": max_cases,
        "complete": len(selection) == max_cases,
        "selection_method": "canonical_prefix",
    }
    return report


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("corpus", type=Path, help="exact pinned BHSA tf/2021 directory")
    cli.add_argument("--partition", choices=("development", "heldout"), default="development")
    cli.add_argument("--max-cases", required=True, type=int)
    cli.add_argument("--input-usd-per-million", type=float)
    cli.add_argument("--output-usd-per-million", type=float)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--live", action="store_true", help="explicitly permit live backend calls")
    args = cli.parse_args(argv)
    if not args.live or os.environ.get("TF_JEV_LIVE") != "1":
        raise ValueError("live evaluation needs --live and TF_JEV_LIVE=1 opt-in")
    if args.output.exists() or args.output.with_name(args.output.name + ".tmp").exists():
        raise ValueError("output already exists; choose a new report path")
    corpus: Path = args.corpus.expanduser()
    benchmark = load_benchmark()
    chosen = benchmark.selected(args.partition)
    if type(args.max_cases) is not int or not 1 <= args.max_cases <= len(chosen):
        raise ValueError("max_cases must be a positive integer within the partition")
    # Fail source drift *before* creating the API client (which may hold credentials).
    if corpus.name != benchmark.corpus["version"]:
        raise ValueError("expected version-named Text-Fabric source directory")
    benchmark.verify_source(corpus)
    from tf_jev.jev import JevBackend

    with JevBackend() as backend:
        report = run_evaluation(
            corpus, benchmark, backend,
            partition=args.partition, max_cases=args.max_cases,
            input_usd_per_million=args.input_usd_per_million,
            output_usd_per_million=args.output_usd_per_million,
        )
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
    output: Path = args.output
    tmp = output.with_name(output.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf8")
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
